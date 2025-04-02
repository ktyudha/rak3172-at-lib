import serial
import time

class LoRa:
    def __init__(self, port="/dev/tty.usbserial-1120 ", baudrate=115200, timeout=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(1)  # Tunggu modul siap
        self.flush()

    def flush(self):
        """ Bersihkan buffer serial """
        self.ser.flushInput()
        self.ser.flushOutput()
    
    def send_command(self, command, delay=0.5):
        """ Kirim perintah ke modul LoRa dan baca respons """
        self.ser.write((command + "\r\n").encode())
        time.sleep(delay)
        response = self.ser.readlines()
        return [line.decode().strip() for line in response]
    
    def init_lora_p2p(self, freq=915000000, sf=12, bw=125, cr=4, preamble=8, power=22):
        """ Konfigurasi LoRa P2P mode """
        self.send_command(f'AT+P2P={freq},{sf},{bw},{cr},{preamble},{power}')
    
    def send_data(self, data):
        """ Kirim data melalui LoRa """
        hex_data = data.encode().hex()
        response = self.send_command(f'AT+SEND={hex_data}', delay=2)
        return response
    
    def receive_data(self):
        """ Cek apakah ada data yang diterima """
        response = self.send_command('AT+RECV')
        return response if response else None
    
    def close(self):
        """ Tutup koneksi serial """
        self.ser.close()

# Contoh Penggunaan
if __name__ == "__main__":
    lora = LoRa(port="/dev/tty.usbserial-1120 ")  # Sesuaikan port dengan perangkat Anda
    lora.init_lora_p2p()
    lora.send_data("Hello LoRa")
    print("Received:", lora.receive_data())
    lora.close()