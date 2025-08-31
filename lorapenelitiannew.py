import serial
import time
import logging
import signal
import sys
import json
from rak3172 import RAK3172
from mqtt import MQTTClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

device = None
mqttc = None

CLIENT_ADDRESS = 1
RELAY_ADDRESS = 2
SERVER_ADDRESS = 3

MQTT_BROKER_WS = "mqtt.ktyudha.site"
MQTT_PORT_WS = 80
MQTT_TOPIC = "v1/devices/uplink-p2p"
MQTT_USERNAME = "barjon"
MQTT_PASSWORD = "password" 

LORA_SF = 7
LORA_FREQ = 868000000
LORA_BW = 125
LORA_CR = 1
LORA_PPL = 8
LORA_TXP = 7

FALLBACK_TIMEOUT = 5  # detik idle sebelum request relay

STATE_IDLE = 0
STATE_WAIT_RELAY = 1
current_state = STATE_IDLE

last_direct_rx_time = 0

def change_state(new_state):
    global current_state
    states = {STATE_IDLE: "IDLE", STATE_WAIT_RELAY: "WAIT_RELAY"}
    logging.info(f"[STATE] {states[current_state]} → {states[new_state]}")
    current_state = new_state

def events(type, parameter):
    global last_direct_rx_time, current_state
    if type == RAK3172.EVENTS.RECEIVED:
        rssi, snr, hex_payload = parameter.split(":")
        payload_bytes = bytes.fromhex(hex_payload)
        fromAddr = payload_bytes[0]
        toAddr = payload_bytes[1]
        payload = payload_bytes[2:].decode("utf-8", errors='ignore').strip()

        if fromAddr == CLIENT_ADDRESS:
            last_direct_rx_time = time.time()

            if current_state == STATE_WAIT_RELAY:
                # Kirim RES ke Relay
                payload_bytes = bytearray([SERVER_ADDRESS, RELAY_ADDRESS]) + b'RES'
                logging.info("Node terdeteksi langsung, kirim RES ke Relay...")
                if send_payload_safe(payload_bytes.hex()):
                    logging.info("RES berhasil dikirim")
                else:
                    logging.error("Gagal kirim RES")
                change_state(STATE_IDLE)

        if toAddr != SERVER_ADDRESS:
            logging.warning(f"Paket bukan untuk gateway (tujuan: {toAddr})")
            return

        process_payload(fromAddr, toAddr, rssi, snr, payload)
    else:
        logging.warning(f"EVENT - Unknown event {type}")

def send_payload_safe(hex_payload, retries=3):
    for i in range(retries):
        try:
            device.send_command("AT+PRECV=0")
            time.sleep(0.2)
            success = device.send_p2p_payload(hex_payload)
            if success:
                logging.info(f"TX sukses: {hex_payload}")
                time.sleep(0.2)
                device.send_command("AT+PRECV=65534")
                return True
        except Exception as e:
            logging.error(f"Retry {i+1} gagal: {e}")
        time.sleep(0.5)
    logging.error(f"Gagal TX setelah {retries} percobaan")
    try:
        device.send_command("AT+PRECV=65534")  # pastikan kembali listen
    except:
        pass
    return False

def process_payload(fromAddr, toAddr, rssi, snr, payload):
    try:
        parts = payload.split(";")[:6]
        if len(parts) < 6:
            logging.error("Payload tidak lengkap")
            return

        temperature = float(parts[0])
        humidity = float(parts[1])
        ph = float(parts[2])
        nitrogen = int(parts[3])
        phosphorus = int(parts[4])
        potassium = int(parts[5])

        mqtt_payload = {
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
            "timestamp": int(round(time.time() * 1000))
        }

        logging.info("Processing payload:")
        logging.info(json.dumps(mqtt_payload, indent=2))

        mqttc.publish(MQTT_TOPIC, json.dumps(mqtt_payload, indent=2))
    except Exception as e:
        logging.error(f"Failed to process payload: {e}")

def handler_sigint(signal, frame):
    print("SIGINT received, exiting...")
    if device:
        device.send_command("AT+PRECV=0")
        device.close()
    sys.exit(0)

def init_p2p_mode(port):
    logging.info("Initializing P2P mode...")
    device = RAK3172(
        serial_port=port,
        network_mode=RAK3172.NETWORK_MODES.P2P,
        verbose=False,
        callback_events=events,
    )
    device.configure_p2p(
        frequency=LORA_FREQ,
        spreading_factor=LORA_SF,
        bandwidth=LORA_BW,
        coding_rate=LORA_CR,
        preamble=LORA_PPL,
        tx_power=LORA_TXP,
    )
    return device

def init_mqtt():
    logging.info("Initializing MQTT...")
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
    signal.signal(signal.SIGINT, handler_sigint)
    
    try:
        mqttc = init_mqtt()
        device = init_p2p_mode(port)
        
        logging.info("Listening for P2P data... (Press Ctrl+C to stop)")
    
        while True:
            now = time.time()

            if last_direct_rx_time != 0 and (now - last_direct_rx_time > FALLBACK_TIMEOUT):
                if current_state == STATE_IDLE:
                    payload_bytes = bytearray([SERVER_ADDRESS, RELAY_ADDRESS]) + b'REQ'
                    logging.info(f"[FALLBACK] {FALLBACK_TIMEOUT}s idle, kirim REQ ke Relay...")
                    if send_payload_safe(payload_bytes.hex()):
                        logging.info("REQ berhasil dikirim")
                        change_state(STATE_WAIT_RELAY)
                    else:
                        logging.error("Gagal kirim REQ, tetap di IDLE")

            time.sleep(1)
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
    finally:
        if 'device' in locals() and device:
            device.send_command("AT+PRECV=0")
            device.close()
