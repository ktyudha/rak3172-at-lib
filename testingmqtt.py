from mqtt import MQTTClient
import time

client = MQTTClient(
    broker="mqtt.ktyudha.site",
    port=80,
    topic="v1/devices/uplink-tes",
    username="barjon",
    password="password"
)

client.connect()
# client.publish_loop("22;33;44;55", interval=2)
client.publish("Hallo!")
# while True:
#     client.publish("11")
#     time.sleep(2)

mqttc.loop_forever()