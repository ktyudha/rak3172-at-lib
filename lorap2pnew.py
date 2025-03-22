import time
from lora import LoRa
import serial

# Konfigurasi Serial
ser = serial.Serial('/dev/tty.usbserial-1120', baudrate=115200, timeout=1)  # Sesuaikan port

# Konfigurasi LoRa
lora = LoRa(serial=ser, frequency=868E6, spreading_factor=7, bandwidth=125E3,
            coding_rate=5, preamble=8, tx_power=22)

def hex_dump(data):
    """ Fungsi untuk menampilkan hex dump dari pesan """
    print("   +------------------------------------------------+ +----------------+")
    print("   |.0 .1 .2 .3 .4 .5 .6 .7 .8 .9 .a .b .c .d .e .f | |      ASCII     |")
    for i in range(0, len(data), 16):
        hex_values = " ".join(f"{byte:02x}" for byte in data[i:i+16])
        ascii_values = "".join(chr(byte) if 31 < byte < 128 else '.' for byte in data[i:i+16])
        print(f"   | {hex_values.ljust(48)} | | {ascii_values.ljust(16)} |")
    print("   +------------------------------------------------+ +----------------+")

def receive():
    """ Fungsi untuk menerima pesan dari Node 1 """
    print("Menunggu pesan...")
    packet = lora.receive()
    if packet:
        print(f"Pesan diterima: {packet.payload.decode('utf-8')}")
        print(f"RSSI: {packet.rssi}, SNR: {packet.snr}")
        hex_dump(packet.payload)
        return True
    return False

def send_response():
    """ Fungsi untuk mengirim pesan ke Node 1 """
    message = "Payload - Node 2 - Python"
    print("Mengirim balasan...")
    success = lora.send(message.encode())
    if success:
        print("Pesan berhasil dikirim!")
    else:
        print("Gagal mengirim pesan!")

while True:
    if receive():
        time.sleep(1)
        send_response()
    time.sleep(0.5)
