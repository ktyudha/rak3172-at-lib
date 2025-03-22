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

# Inisialisasi Serial ke RAK3172 (Sesuaikan Port)
serial_port = "/dev/tty.usbserial-1120"  # Ganti sesuai dengan port Node 2
baud_rate = 115200

ser = None
device = None
state = STATES.RECEIVE_P2P
received_data = None

def send_command(command, delay=0.5):
    """Mengirim perintah AT dan membaca respons"""
    ser.write((command + "\r\n").encode())  # Kirim perintah
    time.sleep(delay)
    
    response = ser.read(ser.inWaiting()).decode(errors='ignore')  # Baca respons
    logging.info(f"> {command}")  # Log perintah
    logging.info(f"< {response}")  # Log respons dari LoRa

    return response

def events(type, parameter):
    global state
    if type == RAK3172.EVENTS.JOINED:
        state = STATES.JOINED
        logging.info("EVENT - Joined")
    elif type == RAK3172.EVENTS.SEND_CONFIRMATION:
        logging.info(f"EVENT - Confirmed: {parameter}")
        state = STATES.RECEIVE_P2P  # Kembali ke mode P2P setelah mengirim
    else:
        logging.warning(f"EVENT - Unknown event {type}")

def handler_sigint(signal, frame):
    logging.info("SIGINT received, exiting...")
    if device:
        device.close()
    if ser:
        ser.close()
    sys.exit(0)

def set_mode_p2p():
    """Mengatur modul ke mode P2P"""
    global ser
    try:
        ser = serial.Serial(serial_port, baudrate=baud_rate, timeout=1)
        logging.info(f"[OK] Terhubung ke {serial_port}")
    except serial.SerialException as e:
        logging.error(f"[ERROR] Port {serial_port} tidak ditemukan! Aborting. Error: {e}")
        sys.exit(1)

    ser.reset_input_buffer()
    
    # Pastikan LoRa dalam mode P2P
    send_command("AT+PRECV=0")  # Matikan mode penerimaan
    time.sleep(1)
    send_command("AT")  # Cek koneksi
    send_command("AT+NWM=0")  # Mode P2P
    # send_command("AT+NJM=0")  # Non-Join Mode

    # Konfigurasi P2P (Harus Sama dengan Node 1)
    send_command("AT+PFREQ=868000000")  # Frekuensi 868 MHz
    send_command("AT+PSF=7")  # Spreading Factor 7
    send_command("AT+PBW=125")  # Bandwidth 125 kHz
    send_command("AT+PCR=1")  # Coding Rate 4/5
    send_command("AT+PPL=8")  # Preamble Length 8
    send_command("AT+PTP=20")  # TX Power 20 dBm
   

def set_mode_lorawan():
    """Mengatur modul ke mode LoRaWAN dan bergabung dengan jaringan"""
    global device, state
    device = RAK3172(
        serial_port=serial_port,
        network_mode=RAK3172.NETWORK_MODES.LORAWAN,
        verbose=False,
        callback_events=events,
    )
    device.deveui = "70B3D57ED09F6A7B"  # Ganti dengan DEVEUI Anda
    device.joineui = "0000000000000000"  # Ganti dengan JoinEUI Anda
    device.appkey = "4EE7845FA0A5BA6D81389261A7140E5B"  # Ganti dengan APPKEY Anda
    device.join()
    state = STATES.JOINING

def send_data_via_lorawan(data):
    """Mengirim data melalui LoRaWAN"""
    if state == STATES.JOINED:
        logging.info(f"Mengirim data: {data}")
        payload_text = "31;55;5"
        payload_hex = ConvertData.str2hex(payload_text).encode()
        device.send_payload(2, payload_hex)
    else:
        logging.warning("Device belum bergabung dengan jaringan LoRaWAN")

def main():
    global state, received_data
    signal.signal(signal.SIGINT, handler_sigint)
    set_mode_p2p()
    logging.info("[READY] Node siap menerima data P2P...")

    while True:
        if state == STATES.RECEIVE_P2P:
            # Menerima data P2P
            send_command("AT+PRECV=0")  # Reset penerimaan
            time.sleep(0.5)
            status = send_command("AT+PRECV=65535")  # Aktifkan penerimaan
            time.sleep(0.5)
            response = send_command("AT+RECV=?")
            logging.info(f"[RECEIVED RAW] {response}")

            # response = ser.read(ser.inWaiting()).decode(errors='ignore')
            # time.sleep(1)
            if response:
                parts = response.split(":")
                hex_payload = parts[-1].strip()  # Ambil payload HEX
                logging.info(f"📦 Payload HEX: {hex_payload}")
                received_data = hex_payload
                state = STATES.SEND_LORAWAN  # Pindah ke mode LoRaWAN

        elif state == STATES.SEND_LORAWAN:
            set_mode_lorawan()
            logging.warning("Menunggu bergabung dengan jaringan LoRaWAN...")
        elif state == STATES.JOINED:
                send_data_via_lorawan(received_data)
                state = STATES.RECEIVE_P2P  # Kembali ke mode P2P setelah mengirim
                set_mode_p2p()

if __name__ == "__main__":
    main()