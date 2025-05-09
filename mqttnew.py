import sys
import time
import paho.mqtt.client as mqtt

MQTT_BROKER_WS = "mqtt.ktyudha.site"
MQTT_PORT_WS = 80  # 80 untuk ws://, 443 untuk wss://
MQTT_TOPIC = "v1/devices/uplink-tes"
MQTT_USERNAME = "barjon"
MQTT_PASSWORD = "password" 

def on_connect(mqttc, obj, flags, rc):
    print("rc: "+str(rc))

def on_message(mqttc, obj, msg):
    print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

def on_publish(mqttc, obj, mid):
    print("mid: "+str(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))

def on_log(mqttc, obj, level, string):
    print(string)

# Initialize MQTT
mqttc = mqtt.Client(transport="websockets")   
mqttc.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe

# Connect to MQTT
mqttc.connect(MQTT_BROKER_WS, MQTT_PORT_WS, keepalive=60)

while True:
    mqttc.publish(MQTT_TOPIC, "22;33;44;55", qos=0)
    time.sleep(2)

# mqttc.subscribe("v1/devices/uplink", 0)

mqttc.loop_forever()