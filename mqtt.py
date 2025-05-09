import time
import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, broker, port, username, password, transport='websockets'):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = mqtt.Client(transport=transport)
        self._setup_callbacks()
        self.client.username_pw_set(username, password)

    def _setup_callbacks(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe
        self.client.on_log = self.on_log

    def connect(self):
        self.client.connect(self.broker, self.port, keepalive=60)
        self.client.loop_start()  # Non-blocking

    def publish_loop(self, topic, message="hello!", interval=2):
        try:
            while True:
                self.client.publish(topic, message, qos=0)
                print(f"Published: {message}")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("Stopped publishing.")
            self.client.loop_stop()
    
    def publish(self, topic, message="hello!"):
        self.client.publish(topic, message, qos=0)

    def on_connect(self, client, userdata, flags, rc):
        print("rc:", str(rc))

    def on_message(self, client, userdata, msg):
        print(msg.topic, str(msg.qos), str(msg.payload.decode()))

    def on_publish(self, client, userdata, mid):
        print("mid:", str(mid))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("Subscribed:", str(mid), str(granted_qos))

    def on_log(self, client, userdata, level, buf):
        print("Log:", buf)
