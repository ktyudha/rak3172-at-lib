from threading import Event
from rak3172 import RAK3172
import signal
import sys
import time

device = None

def hex_dump(data):
    """Print data in hex format for debugging."""
    print("HEX DUMP:", " ".join(f"{byte:02X}" for byte in data))

def events(event_type, parameter):
    """Callback for incoming data events"""
    if event_type == RAK3172.EVENTS.RECEIVED:
        rssi = device.rssi
        snr = device.snr
        try:
            # Try to decode as string
            data_str = parameter.decode('utf-8')
            print(f"EVENT - Data Received: {data_str}")
            
            # If it's RSSI data (from ESP32)
            if ',' in data_str:
                parts = data_str.split(',')
                if len(parts) >= 2:
                    node_rssi = parts[0]
                    node_snr = parts[1]
                    print(f"Node RSSI: {node_rssi}, Node SNR: {node_snr}")
            
        except UnicodeDecodeError:
            print("EVENT - Binary Data Received")
        
        print(f"RSSI: {rssi}, SNR: {snr}")
        hex_dump(parameter)

        # Send back RSSI and SNR data
        send_rssi_data(rssi, snr)

def handler_sigint(signal, frame):
    """Handle Ctrl+C interrupt"""
    print("Stopping device...")
    device.close()
    sys.exit(0)

def send_rssi_data(node_rssi, node_snr):
    """Send RSSI data to the node"""
    gateway_rssi = device.rssi
    gateway_snr = device.snr
    
    payload = f"{node_rssi},{node_snr},{gateway_rssi},{gateway_snr}".encode()
    
    print(f"📤 Sending RSSI data: {payload.decode()}")
    hex_dump(payload)
    
    result = device.send_payload(2, payload)
    print("✅ Transmission", "SUCCESS" if result else "FAILED")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 lorap2p.py /dev/ttyUSB0")
        sys.exit("Leaving now")

    port = str(sys.argv[1])

    # Handle Ctrl+C for clean exit
    signal.signal(signal.SIGINT, handler_sigint)

    # Initialize device in P2P mode
    device = RAK3172(
        serial_port=port,
        network_mode=RAK3172.NETWORK_MODES.P2P,
        verbose=False,
        callback_events=events,
    )

    # Configure P2P mode to match ESP32 settings
    device.configure_p2p(
        frequency=868000000,  # Match frequency with ESP32
        spreading_factor=7,    # SF7
        bandwidth=125,         # 125 kHz
        coding_rate=1,         # CR 4/5
        preamble=8,            # Preamble length 8
        tx_power=20            # TX Power 20 dBm (match with ESP32)
    )

    print("Device ready in P2P mode!")

    # Main loop
    while True:
        # You can add periodic transmissions here if needed
        time.sleep(5)