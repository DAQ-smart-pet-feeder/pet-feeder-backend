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
from ultra import find_distance
from behavior import is_something_block
from temp_hum import temp_hum

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


async def publish_distance():
    await asyncio.sleep(3)
    initial_distance = find_distance()
    prev_state = 0
    while True:
        while abs(find_distance() - initial_distance) <= 6:
            pass
        print('state_change')
        await asyncio.sleep(1)
        while abs(find_distance() - initial_distance) > 6:
            pass
        print('state change again')
        await asyncio.sleep(1)

asyncio.create_task(publish_behavior())
asyncio.run_until_complete()
