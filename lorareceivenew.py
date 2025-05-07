import serial
import time
import logging
from rak3172 import RAK3172
import signal
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def events(type, parameter):
    """Callback for incoming data events"""
    if type == RAK3172.EVENTS.RECEIVED:
        try:
            # Konversi payload hex ke bytes
            payload_bytes = bytes.fromhex(parameter)
            
            # Ambil byte ke-0 dan ke-1
            if len(payload_bytes) >= 2:
                client_address = payload_bytes[0]
                server_address = payload_bytes[1]
                
                print(f"Dari: {client_address}, Ke: {server_address}")
                
                # Sisakan payload setelah 2 byte pertama jika perlu
                remaining_payload = payload_bytes[2:].decode(errors='ignore')
                if remaining_payload:
                    print(f"Payload lainnya: {remaining_payload}")
                
                # Process the complete payload if needed
                process_payload(payload_bytes)
            else:
                print("Payload terlalu pendek, minimal 2 byte")
                
        except Exception as e:
            print(f"Error processing payload: {str(e)}")

def process_payload(payload_bytes):
    """Process the complete payload bytes"""
    # Tambahkan logika pemrosesan data lengkap di sini
    print(f"Processing complete payload: {payload_bytes.hex()}")

def handler_sigint(signal, frame):
    print("SIGINT received, exiting...")
    if device:
        device.send_command("AT+PRECV=0")  # Nonaktifkan penerimaan P2P
        device.close()
    sys.exit(0)

def init_p2p_mode(port):
    print("Initializing P2P mode...")
    device = RAK3172(
        serial_port=port,
        network_mode=RAK3172.NETWORK_MODES.P2P,
        verbose=False,
        callback_events=events,
    )
    device.configure_p2p(
        frequency=868000000,      # Sesuaikan dengan frekuensi yang digunakan
        spreading_factor=7,       # SF7
        bandwidth=125,            # 125 kHz
        coding_rate=1,            # Coding rate 4/5
        preamble=8,               # Preamble length 8
        tx_power=20,             # TX power 20 dBm
    )
    return device

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <serial_port>")
        sys.exit(1)
        
    port = str(sys.argv[1])
    
    # Prepare signal management
    signal.signal(signal.SIGINT, handler_sigint)
    
    try:
        # Inisialisasi device dalam mode P2P
        device = init_p2p_mode(port)
        
        print("Listening for P2P data... (Press Ctrl+C to stop)")
        
        # Loop utama - device akan memanggil callback events ketika data diterima
        while True:
            time.sleep(1)  # Kurangi penggunaan CPU
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'device' in locals() and device:
            device.send_command("AT+PRECV=0")  # Pastikan penerimaan dinonaktifkan
            device.close()