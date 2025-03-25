import serial
import time
import sys

serial_port = "COM6"
baud_rate = 115200

try:
    ser = serial.Serial(serial_port, baudrate=baud_rate, timeout=1)
    print(f"[OK] Terhubung ke {serial_port}")
except serial.SerialException:
    sys.exit(f"[ERROR] Port {serial_port} tidak ditemukan! Aborting.") 
def send_command(command, delay=0.5):
    """Mengirim perintah AT dan membaca respons"""
    ser.write((command + "\r\n").encode())
    time.sleep(delay)
    response = ser.read(ser.inWaiting()).decode(errors='ignore')
    print(f"> {command}")
    print(f"< {response}")
    return response

send_command("AT+PRECV=0")
time.sleep(1)

# Konfigurasi P2P
send_command("AT")  # Cek koneksi
send_command("AT+NWM=0")  # Mode P2P
send_command("AT+NJM=0")
send_command("AT+PFREQ=868000000")  # Frekuensi 915 MHz
send_command("AT+PSF=7")  # Spreading Factor 7
send_command("AT+PBW=125")  # Bandwidth 125 kHz
send_command("AT+PCR=1")  # Coding Rate 4/5
send_command("AT+PPL=8")  # Preamble Length 8
send_command("AT+PTP=20")  # TX Power 20 dBm

print("Node 1 siap mengirim data...")

while True:
    message = "Hello"
    hex_message = message.encode().hex()  # Ubah teks menjadi HEX
    send_command(f"AT+PSEND={hex_message}")
    # send_command("AT+PSEND=AABA")
    print(f"Pesan terkirim: {message}")
    time.sleep(0.5)  # Kirim setiap 5 detik
