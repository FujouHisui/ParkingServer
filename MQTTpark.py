# python3.6
import random
import time
import flask_server
from paho.mqtt import client as mqtt_client
import globalvar as gl

broker = '127.0.0.1'
port = 1883
topic = "parking"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        try:
            received_msg = msg.payload.decode()
        except UnicodeDecodeError:
            print("读卡信息错误")
        else:
            print(f"Received `{received_msg}` from `{msg.topic}` topic")

            if len(received_msg) != 0:
                legit = legit_data(received_msg)
                if legit == 0:
                    gl.set_value("area_1", str(received_msg[1]))
                elif legit == 1:
                    gl.set_value("area_2", str(received_msg[1]))
                print(received_msg)

    client.subscribe(topic)
    client.on_message = on_message


def publish(client):
    msg_count = 0
    while True:
        time.sleep(1)
        msg = f"messages: {msg_count}"
        result = client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


def legit_data(data):
    data = str(data).strip()
    if data[1].isdigit:
        if data[0] == "A":
            return 0
        elif data[0] == "B":
            return 1
        else:
            return -1
    else:
        return -1

# if __name__ == '__main__':
#    run()
