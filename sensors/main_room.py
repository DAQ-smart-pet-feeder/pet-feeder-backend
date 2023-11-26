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


async def publish_behavior():
    # waiting for find good distance for 3 sec
    while True:
        while not is_something_block():
            pass
        curr_time = time.time()
        await asyncio.sleep(1.1)
        if not is_something_block():
            continue
        mqtt.publish('daq2023/group4/behav', json.dumps({'status': 1}))
        print('something is block')
        while is_something_block():
            pass

        mqtt.publish('daq2023/group4/behav', json.dumps({'status': 0}))
        sensor_data = get_sensor_data()
        eat_time = time.time() - curr_time
        temp, hum = sensor_data
        pm25 = get_pm()
        data_vis_payload = {'pm25': pm25, 'temp': temp, 'hum': hum, 'eating_time': eat_time}
        mqtt.publish('daq2023/group4/data_vis', json.dumps(data_vis_payload))
        print('unblocked')
        
async def publish_sensor_room_data():
    while True:
        await asyncio.sleep(1.123456)
        sensor_data = get_sensor_data()
        temp, hum = sensor_data
        sensor_room_data_payload = {
            "temp": temp,
            "hum": hum,
            "pm25": get_pm()
            }
        print('published data')
        mqtt.publish('daq2023/group4/room_data', json.dumps(sensor_room_data_payload))


asyncio.create_task(publish_behavior())
asyncio.create_task(publish_sensor_room_data())

asyncio.run_until_complete()
