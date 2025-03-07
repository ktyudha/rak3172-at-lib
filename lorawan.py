from threading import Event
from rak3172 import RAK3172
from data import ConvertData
import signal
import sys
import time
import random

class STATES:
    JOINING = 0
    JOINED = 1
    SEND_DATA = 2
    SLEEP = 3
    RECV_DATA = 4



device = None
state = None


def events(type, parameter):
    global state

    if type == RAK3172.EVENTS.JOINED:
        state = STATES.JOINED
        print("EVENT - Joined")
    elif type == RAK3172.EVENTS.SEND_CONFIRMATION:
        print(f"EVENT - Confirmed: {parameter}")
    else:
        print("EVENT - Unknown event {type}")


def handler_timeout_tx(signal, frame):
    global state
    state = STATES.SEND_DATA


def handler_sigint(signal, frame):
    device.close()
    sys.exit(0)


if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #     print(
    #         "\n\n================================================================\nMissing argument! Usage:"
    #     )
    #     print("> python3 lorawan.py /dev/ttyUSB0")
    #     sys.exit(
    #         "Leaving now\n================================================================\n\n"
    #     )
    port = str(sys.argv[1])

    # Prepare signal management
    signal.signal(signal.SIGALRM, handler_timeout_tx)
    signal.signal(signal.SIGINT, handler_sigint)

    device = RAK3172(
        serial_port=port,
        network_mode=RAK3172.NETWORK_MODES.LORAWAN,
        verbose=False,
        callback_events=events,
    )
    device.deveui = "70B3D57ED09F6A7B"
    device.joineui = "0000000000000000"
    device.appkey = "4EE7845FA0A5BA6D81389261A7140E5B"

    # Display device informations
    # print(f"Module devEUI: 0x{device.deveui}")
    # print(f"Module joinEUI: 0x{device.joineui}")
    # print(f"Module AppKey: 0x{device.appkey}")

    # Join the network
    device.join()
    state = STATES.JOINING

    while True:
        if state == STATES.JOINED:
            print("Device has joined the network")
            state = STATES.SEND_DATA
        elif state == STATES.SEND_DATA:
            message_send = random.randint(1000,9999)
            message_send_hex = ConvertData.str2hex(str(message_send)).encode()
            status = device.send_payload(2, message_send_hex)
            # Send a payload
            # device.send_payload(2, b"FEED")
            signal.alarm(2)
        
        elif state == STATES.RECV_DATA:
            data_from_gw = device.getdata
            data_split = data_from_gw.split("=")
            if data_split[1].split(":")[0] =="1":
                # print("masuk")
                print(f"message received: {data_from_gw.split(':')[1]}")
            state = STATES.SLEEP
        elif state == STATES.SLEEP:
            time.sleep(1)
