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

device = None
state = None
payload = ""


def events(type, parameter):
    """Callback for incoming data events"""
    global state, payload

    if type == RAK3172.EVENTS.JOINED:
        state = STATES.JOINED
        print("EVENT - Joined")
    elif type == RAK3172.EVENTS.SEND_CONFIRMATION:
        print(f"EVENT - Confirmed: {parameter}")
        state = STATES.SEND_LORAWAN
    elif type == RAK3172.EVENTS.RECEIVED:
        payload = bytes.fromhex(parameter).decode(errors='ignore')
        print(f"EVENT - Data: {payload}")
        state = STATES.RECEIVE_P2P
    else:
        print("EVENT - Unknown event {type}")

    # if event_type == RAK3172.EVENTS.RECEIVED:
    #     print(f"Data diterima:{bytes.fromhex(parameter).decode(errors='ignore')}")

def handler_timeout_tx(signal, frame):
    print("Timeout occurred during transmission")
    global state
    state = STATES.SEND_DATA

def handler_sigint(signal, frame):
    print("SIGINT received, exiting...")
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
        tx_power=20
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

        # ====== P2P ======
        # Switch to P2P mode
        device = switch_to_p2p(port)
        print("Operating in P2P mode for 10 seconds")
            
        # Operate in P2P mode
        start_time = time.time()
        while time.time() - start_time < 10:
            # Your P2P operations here
            time.sleep(1)
            
        # DISABLE P2P
        device.send_command("AT+PRECV=0")
        # Clean up P2P mode
        device.close()            
        time.sleep(1)  # Small delay before switching


        # ====== LoRaWAN ====== 
        # Switch to LoRaWAN mode
        device = switch_to_lorawan(port)
        print("Operating in LoRaWAN mode for 20 seconds")
            
        # Operate in LoRaWAN mode
        start_time = time.time()
        while time.time() - start_time < 20:
            # Your LoRaWAN operations here
            time.sleep(1)
            if state == STATES.JOINED:
                payload_text = "31;55;5"
                payload_hex = ConvertData.str2hex(payload_text).encode()
                device.send_payload(2, payload_hex)
            
        # Clean up LoRaWAN mode
        device.close()
        time.sleep(1)
