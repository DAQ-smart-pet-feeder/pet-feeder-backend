import uasyncio as asyncio
from machine import Pin,I2C,ADC
import network
import time
import json
from time import sleep
from umqtt.robust import MQTTClient
from config import (
    WIFI_SSID, WIFI_PASS,
    MQTT_BROKER, MQTT_USER, MQTT_PASS
)
import math
from behavior import is_something_block
from temp_hum import get_sensor_data
from PM import get_pm

led_wifi = Pin(2, Pin.OUT)
led_wifi.value(1)  # turn the red led off
led_iot = Pin(12, Pin.OUT)
led_iot.value(1)   # turn the green led off

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
mqtt = MQTTClient(client_id="",
                      server=MQTT_BROKER,
                      user=MQTT_USER,
                      password=MQTT_PASS)

FOOD_CONTAINER_AMOUNT = 20

def connect_anything():
    try:
        # connect to wifi  
        wlan.connect(WIFI_SSID, WIFI_PASS)
        print("connecting to wifi...")
        while not wlan.isconnected():
            time.sleep(0.5)
        print("connected to wifi")

        mqtt.connect()
        led_wifi.value(0)
        print("connected to MQTT broker")
    except:
        led_wifi.value(1)
        print("wifi disconnected")

connect_anything()

def disconnect_mqtt():
    try:
        mqtt.disconnect()
        print("Disconnected from MQTT broker")
    except Exception as e:
        print("Error disconnecting from MQTT broker:", e)
        
def reconnect_mqtt():
    try:
        mqtt.connect()
        print("Reconnected to MQTT broker")
    except Exception as e:
        print("Error reconnecting to MQTT broker:", e)

async def publish_behavior():
    while True:
        start_time = time.time()
        while not is_something_block():
            await asyncio.sleep_ms(10)  # Sleep for 10 ms
        curr_time = time.time()
        await asyncio.sleep(5)
        while is_something_block():
            await asyncio.sleep_ms(10)  # Sleep for 10 ms
        reconnect_mqtt()
        mqtt.publish('daq2023/group4/behav', json.dumps({'status': 0}))
        sensor_data = get_sensor_data()
        eat_time = time.time() - curr_time
        temp, hum = sensor_data
        pm25 = get_pm()
        data_vis_payload = {'pm25': pm25, 'temp': temp, 'hum': hum, 'eating_time': eat_time}
        mqtt.publish('daq2023/group4/data_vis', json.dumps(data_vis_payload))
        disconnect_mqtt()
        print('Unblocked')
        await asyncio.sleep_ms(10)
        
async def publish_sensor_room_data():
    while True:
        reconnect_mqtt()
        sensor_data = get_sensor_data()
        temp, hum = sensor_data
        sensor_room_data_payload = {
            "temp": temp,
            "hum": hum,
            "pm25": get_pm()
            }
        print('published data', sensor_room_data_payload)
        mqtt.publish('daq2023/group4/room_data', json.dumps(sensor_room_data_payload))
        disconnect_mqtt()
        await asyncio.sleep(3) # 30 min

asyncio.create_task(publish_behavior())
asyncio.create_task(publish_sensor_room_data())

asyncio.run_until_complete()