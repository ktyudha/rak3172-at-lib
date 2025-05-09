import serial
import time
import logging
import signal
import sys
from rak3172 import RAK3172
from mqtt import MQTTClient
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
mqttc = None

RELAY_ADDRESS = 2
SERVER_ADDRESS = 3

def events(type, parameter):
    """Callback for incoming data events"""
    if type == RAK3172.EVENTS.RECEIVED:
        payload_bytes = bytes.fromhex(parameter)
        payload = payload_bytes.decode(errors='ignore')
        
        client_address = payload_bytes[0]
        server_address = payload_bytes[1]

        # Batasi hanya menerima dari relay
        if client_address != RELAY_ADDRESS:
            print(f"Ignored packet from unknown node {client_address}")
            return
        
        # Optional: pastikan alamat tujuan adalah gateway
        if server_address != SERVER_ADDRESS:
            print(f"Paket bukan untuk gateway (tujuan: {server_address})")
            return
                
        print(f"Dari: {client_address}, Ke: {server_address}")
        print(f"Data received: {payload}")
        # Lakukan sesuatu dengan payload yang diterima
        process_payload(payload)
    else:
        print(f"EVENT - Unknown event {type}")

def process_payload(payload):
    """Process the received payload"""
    # Tambahkan logika pemrosesan data di sini
    print(f"Processing payload: {payload}")
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    payload_with_timestamp = f"{timestamp} - {payload}"
    mqttc.publish(payload_with_timestamp)
    # mqttc.publish(payload)

def handler_sigint(signal, frame):
    print("SIGINT received, exiting...")
    if device:
        device.send_command("AT+PRECV=0")  # Nonaktifkan penerimaan P2P
        device.close()
    sys.exit(0)

def init_p2p_mode(port):
    print("Initializing P2P mode...")
    device = RAK3172(
        serial_port=port,
        network_mode=RAK3172.NETWORK_MODES.P2P,
        verbose=False,
        callback_events=events,
    )
    device.configure_p2p(
        frequency=868000000,      # Sesuaikan dengan frekuensi yang digunakan
        spreading_factor=7,       # SF7
        bandwidth=125,            # 125 kHz
        coding_rate=1,            # Coding rate 4/5
        preamble=8,               # Preamble length 8
        tx_power=20,              # TX power 20 dBm
    )
    return device

def init_mqtt():
    print("Initializing MQTT...")
    mqttc = MQTTClient(
        broker="mqtt.ktyudha.site",
        port=80,
        topic="v1/devices/uplink-tes",
        username="barjon",
        password="password"
    )
    mqttc.connect()
    return mqttc

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <serial_port>")
        sys.exit(1)
        
    port = str(sys.argv[1])
    
    # Prepare signal management
    signal.signal(signal.SIGINT, handler_sigint)
    
    try:
        # Inisialisasi mqtt
        mqttc = init_mqtt()
        # Inisialisasi device dalam mode P2P
        device = init_p2p_mode(port)
        
        print("Listening for P2P data... (Press Ctrl+C to stop)")
        
        # Loop utama - device akan memanggil callback events ketika data diterima
        while True:
            time.sleep(1)  # Kurangi penggunaan CPU
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'device' in locals() and device:
            device.send_command("AT+PRECV=0")  # Pastikan penerimaan dinonaktifkan
            device.close()