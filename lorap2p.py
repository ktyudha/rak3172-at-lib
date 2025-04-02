from threading import Event
from rak3172 import RAK3172
import signal
import sys
import time


device = None

def hex_dump(data):
    """Mencetak data dalam format hex untuk debugging."""
    print("HEX DUMP:")
    print(" ".join(f"{byte:02X}" for byte in data))

def events(event_type, parameter):
    """Callback untuk event data masuk"""
    if event_type == RAK3172.EVENTS.RECEIVED:
        rssi = device.rssi
        snr = device.snr
        print(f"EVENT - Data Received: {parameter}")
        print(f"RSSI: {rssi}, SNR: {snr}")
        hex_dump(parameter)

        # Kirim kembali RSSI dan SNR ke node pengirim
        send_rssi_data(rssi, snr)
    else:
        print(f"EVENT - Unknown event {event_type}")


def handler_sigint(signal, frame):
    """Menangani interupsi Ctrl + C"""
    print("Menghentikan perangkat...")
    device.close()
    sys.exit(0)


def send_rssi_data(node_rssi, node_snr):
    """Mengirimkan data RSSI node dan RSSI gateway."""
    gateway_rssi = device.rssi
    gateway_snr = device.snr
    
    payload = f"{node_rssi},{node_snr},{gateway_rssi},{gateway_snr}".encode()
    
    print(f"📤 Mengirim data RSSI: {payload}")
    hex_dump(payload)  # Debugging
    
    result = device.send_payload(2, payload)
    print("✅ Pengiriman", "BERHASIL" if result else "GAGAL")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 lorap2p.py /dev/ttyUSB0")
        sys.exit("Leaving now")

    port = str(sys.argv[1])

    # Menangani Ctrl + C untuk keluar dengan aman
    signal.signal(signal.SIGINT, handler_sigint)

    # Inisialisasi perangkat dengan mode P2P
    device = RAK3172(
        serial_port=port,
        network_mode=RAK3172.NETWORK_MODES.P2P,
        verbose=False,
        callback_events=events,
    )

    # Konfigurasi mode P2P
    device.configure_p2p(
        frequency=868000000,  # Frekuensi LoRa (sesuaikan dengan regional)
        spreading_factor=7,    # SF7 (bisa diubah)
        bandwidth=125,         # Bandwidth 125 kHz
        coding_rate=1,         # Coding rate 4/5
        preamble=8,            # Preamble length (sesuai dengan versi C++)
        tx_power=22            # TX Power 22 dBm (maksimal)
    )


    print("Perangkat siap di mode P2P!")

    # Loop utama untuk menerima data
    while True:
        time.sleep(5)  # Menjaga loop tetap berjalan
