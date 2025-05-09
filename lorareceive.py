import serial
import time
import logging
import signal
import sys
import json
from rak3172 import RAK3172
from mqtt import MQTTClient
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

device = None
mqttc = None

RELAY_ADDRESS = 2
SERVER_ADDRESS = 3

MQTT_BROKER_WS = "mqtt.ktyudha.site"
MQTT_PORT_WS = 80  # 80 untuk ws://, 443 untuk wss://
MQTT_TOPIC = "v1/devices/uplink-tes"
MQTT_USERNAME = "barjon"
MQTT_PASSWORD = "password" 

LORA_SF=7
LORA_FREQ=868000000
LORA_BW=125
LORA_CR=1
LORA_PPL=8
LORA_TXP=20

def events(type, parameter):
    """Callback for incoming data events"""
    if type == RAK3172.EVENTS.RECEIVED:
        rssi, snr, hex_payload = parameter.split(":")

        # Parsing payload
        payload_bytes = bytes.fromhex(hex_payload)

        # Ambil Address
        fromAddr = payload_bytes[0]
        toAddr = payload_bytes[1]

        payload = payload_bytes[2:].decode(errors='ignore')

        # # Batasi hanya menerima dari relay
        # if client_address != RELAY_ADDRESS:
        #     print(f"Ignored packet from unknown node {client_address}")
        #     return
        
        # # Optional: pastikan alamat tujuan adalah gateway
        # if server_address != SERVER_ADDRESS:
        #     print(f"Paket bukan untuk gateway (tujuan: {server_address})")
        #     return

        process_payload(fromAddr, toAddr, rssi, snr, payload)
    else:
        print(f"EVENT - Unknown event {type}")

def process_payload(fromAddr, toAddr, rssi, snr, payload):
    """Process the received payload"""

    try:
        parts = payload.split(";")
        if len(parts) < 6 :
            print("Payload tidak lengkap")
            return

        temperature = parts[0]
        humidity = parts[1]
        ph = parts[2]
        nitrogen = parts[3]
        phosphorus = parts[4]
        potassium = parts[5]

        mqtt_payload = [
            {
                "metadata": {"rssi": rssi, "snr": snr},
                "uplink": {
                    "temperature": temperature,
                    "humidity": humidity,
                    "ph": ph,
                    "nitrogen": nitrogen,
                    "phossporus": phosphorus,
                    "potassium": potassium,
                },
                "address": {"from": fromAddr, "to": toAddr},
                "timestamp": int(time.time())
            }
        ]

        # Check Log
        logging.info("Processing payload:")
        logging.info(json.dumps(mqtt_payload, indent=2))

        # Kirim melalui MQTT
        mqttc.publish("v1/devices/uplink-tes", json.dumps(mqtt_payload, indent=2))
    except Exception as e:
        print(f"Failed to process payload: {e}")


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
        frequency=LORA_FREQ,      # Sesuaikan dengan frekuensi yang digunakan
        spreading_factor=LORA_SF,       # SF7
        bandwidth=LORA_BW,            # 125 kHz
        coding_rate=LORA_CR,            # Coding rate 4/5
        preamble=LORA_PPL,               # Preamble length 8
        tx_power=LORA_TXP,              # TX power 20 dBm
    )
    return device

def init_mqtt():
    print("Initializing MQTT...")
    mqttc = MQTTClient(
        broker=MQTT_BROKER_WS,
        port=MQTT_PORT_WS,
        username=MQTT_USERNAME,
        password=MQTT_PASSWORD
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
        # Inisialisasi mqtt & LoRa mode p2p
        mqttc = init_mqtt()
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