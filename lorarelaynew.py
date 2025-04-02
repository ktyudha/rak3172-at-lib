import serial
import time
import logging
from rak3172 import RAK3172
import signal
from data import ConvertData
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class STATES:
    RECEIVE_P2P = 0
    SEND_LORAWAN = 1
    JOINING = 2
    JOINED = 3
    WAITING_P2P_DATA = 4

device = None
state = STATES.WAITING_P2P_DATA
payload = ""
lorawan_sent = False

def events(type, parameter):
    """Callback for incoming data events"""
    global state, payload, lorawan_sent

    if type == RAK3172.EVENTS.JOINED:
        state = STATES.JOINED
        print("EVENT - Joined")
    elif type == RAK3172.EVENTS.SEND_CONFIRMATION:
        print(f"EVENT - Confirmed: {parameter}")
        lorawan_sent = True
        state = STATES.WAITING_P2P_DATA  # Kembali menunggu data P2P
    elif type == RAK3172.EVENTS.RECEIVED:
        payload = bytes.fromhex(parameter).decode(errors='ignore')
        print(f"EVENT - Data: {payload}")
        state = STATES.RECEIVE_P2P
    else:
        print(f"EVENT - Unknown event {type}")

def handler_timeout_tx(signal, frame):
    print("Timeout occurred during transmission")
    global state
    state = STATES.SEND_LORAWAN

def handler_sigint(signal, frame):
    print("SIGINT received, exiting...")
    if device:
        device.close()
    sys.exit(0)

def switch_to_p2p(port):
    print("Initializing P2P mode...")
    device = RAK3172(
        serial_port=port,
        network_mode=RAK3172.NETWORK_MODES.P2P,
        verbose=False,
        callback_events=events,
    )
    device.configure_p2p(
        frequency=868000000,
        spreading_factor=7,
        bandwidth=125,
        coding_rate=1,
        preamble=8,
        tx_power=20,
    )
    return device

def switch_to_lorawan(port):
    print("Initializing LoRaWAN mode...")
    device = RAK3172(
        serial_port=port,
        network_mode=RAK3172.NETWORK_MODES.LORAWAN,
        verbose=False,
        callback_events=events,
    )
    device.deveui = "70B3D57ED09F6A7B"
    device.joineui = "0000000000000000"
    device.appkey = "4EE7845FA0A5BA6D81389261A7140E5B"
    device.join()
    return device

if __name__ == "__main__":
    port = str(sys.argv[1])

    # Prepare signal management
    signal.signal(signal.SIGALRM, handler_timeout_tx)
    signal.signal(signal.SIGINT, handler_sigint)

    while True:
        if state == STATES.WAITING_P2P_DATA or state == STATES.RECEIVE_P2P:
            # ====== P2P MODE ======
            if device:
                device.close()
                time.sleep(1)
            
            device = switch_to_p2p(port)
            print("Waiting for P2P data...")
            
            # Tunggu sampai data P2P diterima
            start_time = time.time()
            while state != STATES.RECEIVE_P2P and (time.time() - start_time < 30):  # Timeout 30 detik
                time.sleep(0.1)
            
            if state == STATES.RECEIVE_P2P:
                print(f"Payload received in P2P mode: {payload}")
                # Nonaktifkan P2P RX sebelum beralih
                device.send_command("AT+PRECV=0")
                device.close()
                time.sleep(1)
                state = STATES.JOINING  # Siap untuk beralih ke LoRaWAN

        elif state == STATES.JOINING or state == STATES.JOINED or state == STATES.SEND_LORAWAN:
            # ====== LoRaWAN MODE ======
            if device:
                device.close()
                time.sleep(1)
            
            device = switch_to_lorawan(port)
            lorawan_sent = False
            
            # Tunggu sampai join berhasil
            start_time = time.time()
            while state != STATES.JOINED and (time.time() - start_time < 30):
                time.sleep(0.1)
            
            if state == STATES.JOINED:
                print("Successfully joined LoRaWAN network")
                # Kirim payload yang diterima dari P2P
                if payload:
                    try:
                        payload_hex = ConvertData.str2hex(payload).encode()
                        device.send_payload(2, payload_hex)
                        print(f"Sending payload to LoRaWAN: {payload}")
                        
                        # Tunggu konfirmasi pengiriman
                        start_time = time.time()
                        while not lorawan_sent and (time.time() - start_time < 30):
                            time.sleep(0.1)
                        
                        if lorawan_sent:
                            print("Payload successfully sent via LoRaWAN")
                            payload = ""  # Reset payload
                    except Exception as e:
                        print(f"Error sending LoRaWAN payload: {str(e)}")
            
            # Kembali ke mode P2P
            device.close()
            time.sleep(1)
            state = STATES.WAITING_P2P_DATA

        time.sleep(0.1)  # Small delay to prevent CPU overuse