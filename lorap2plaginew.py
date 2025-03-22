import serial
import time
import sys

# Inisialisasi Serial ke RAK3172 (Sesuaikan Port)
serial_port = "/dev/tty.usbserial-1120"  # Ganti sesuai dengan port Node 2
baud_rate = 115200

try:
    ser = serial.Serial(serial_port, baudrate=baud_rate, timeout=1)
    print(f"[OK] Terhubung ke {serial_port}")
except serial.SerialException:
    sys.exit(f"[ERROR] Port {serial_port} tidak ditemukan! Aborting.")

ser.reset_input_buffer()

def send_command(command, delay=0.5):
    """Mengirim perintah AT dan membaca respons"""
    ser.write((command + "\r\n").encode())  # Kirim perintah
    time.sleep(delay)
    
    response = ser.read(ser.inWaiting()).decode(errors='ignore')  # Baca respons
    print(f"> {command}")  # Print perintah
    print(f"< {response}")  # Print respons dari LoRa

    return response


send_command("AT+PRECV=0")  # Matikan mode penerimaan
time.sleep(1)

# 🔹 Pastikan LoRa dalam mode P2P
send_command("AT")  # Cek koneksi
send_command("AT+NWM=0")  # Mode P2P
send_command("AT+NJM=0")  # Non LoRaWAN

# 🔹 Konfigurasi P2P (Harus Sama dengan Node 1)
send_command("AT+PFREQ=868000000")  # Frekuensi 915 MHz
send_command("AT+PSF=7")  # Spreading Factor 7
send_command("AT+PBW=125")  # Bandwidth 125 kHz
send_command("AT+PCR=1")  # Coding Rate 4/5
send_command("AT+PPL=8")  # Preamble Length 8
send_command("AT+PTP=20")  # TX Power 20 dBm

print("[READY] Node 2 siap menerima data...")

while True:
    # send_command("AT+PRECV=0")  # Reset RX
    # time.sleep(1)
    send_command("AT+PRECV=65535")  # Aktifkan RX kembali
    time.sleep(1)

    response = ser.read(ser.inWaiting()).decode(errors='ignore')  # Baca data masuk
    if response:
        print(f"[RECEIVED RAW] {response}")  # Debugging: Print semua data masuk

    if "+EVT:RXP2P" in response:
            hex_data = response.split(",")[-1].strip()  # Ambil bagian HEX
            received_message = bytes.fromhex(hex_data).decode(errors='ignore')  # Konversi HEX ke teks
            print(f"📩 Pesan diterima: {received_message}")
            # print(f"📩 Pesan diterima: {hex_data}")
        # try:
        # except ValueError:
        #     print("[WARNING] Gagal decoding data!")
