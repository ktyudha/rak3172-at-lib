from threading import Event
from rak3172 import RAK3172
from data import ConvertData
import signal
import sys
import time


class STATES:
    JOINING = 0
    JOINED = 1
    SEND_DATA = 2
    SLEEP = 3
    RECEIVE_DATA = 4


device = None
state = None


def events(type, parameter):
    global state

    if type == RAK3172.EVENTS.JOINED:
        state = STATES.JOINED
        print("EVENT - Joined")
    elif type == RAK3172.EVENTS.SEND_CONFIRMATION:
        print(f"EVENT - Confirmed: {parameter}")
    elif type == RAK3172.EVENTS.RECEIVED:
        rssi = device.rssi
        snr = device.snr
        print(f"EVENT - Data Received: {parameter}")
        print(f"RSSI: {rssi}, SNR: {snr}")

        # Kirim kembali RSSI gateway ke node
        send_rssi_data(rssi, snr)
    else:
        print("EVENT - Unknown event {type}")


def handler_timeout_tx(signal, frame):
    global state
    state = STATES.SEND_DATA


def handler_sigint(signal, frame):
    device.close()
    sys.exit(0)

def send_rssi_data(node_rssi, node_snr):
    """Mengirimkan data RSSI node dan RSSI gateway."""
    gateway_rssi = device.rssi  # Dapatkan RSSI dari LoRa module
    gateway_snr = device.snr    # Dapatkan SNR dari LoRa module
    
    payload = f"{node_rssi},{node_snr},{gateway_rssi},{gateway_snr}".encode()
    
    print(f"Mengirim data RSSI: {payload}")
    device.send_payload(2, payload)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "\n\n================================================================\nMissing argument! Usage:"
        )
        print("> python3 lorawan.py /dev/ttyUSB0")
        sys.exit(
            "Leaving now\n================================================================\n\n"
        )
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
    print(f"Module devEUI: 0x{device.deveui}")
    print(f"Module joinEUI: 0x{device.joineui}")
    print(f"Module AppKey: 0x{device.appkey}")

    # Join the network
    device.join()
    state = STATES.JOINING

    while True:
        if state == STATES.JOINED:
            print("Device has joined the network")
            state = STATES.SEND_DATA
        elif state == STATES.SEND_DATA:
            print("send data")
            payload_text = "31;55;5"
            payload_hex = ConvertData.str2hex(payload_text).encode()  # Konversi ke hex
            status = device.send_payload(2, payload_hex)
            # device.send_payload(2, b"AAFFBB")
            signal.alarm(2)
            state = STATES.RECEIVE_DATA
        elif state == STATES.RECEIVE_DATA:
            print("successs recv")
            data_from_gw = device.getdata  # Asumsikan ini mengandung string panjang
            print(f"Raw Data Received: {data_from_gw}")  # Debug output

            # Cari bagian yang mengandung payload HEX (biasanya setelah titik dua terakhir)
            try:
                parts = data_from_gw.split(":")
                hex_payload = parts[-1].strip()  # Ambil bagian terakhir sebagai payload

                # Konversi ke string
                received_message = ConvertData.hex2str(hex_payload)
                print(f"Message received: {received_message}")

            except Exception as e:
                print(f"Error parsing received data: {e}")
            state = STATES.SLEEP
        elif state == STATES.SLEEP:
            time.sleep(1)
