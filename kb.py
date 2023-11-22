import machine
import time
import network
import uasyncio as asyncio

from umqtt.robust import MQTTClient
from config import (
    WIFI_SSID, WIFI_PASS,
    MQTT_BROKER, MQTT_USER, MQTT_PASS
)

import json

# Define the data pin for the DHT11 sensor
DHpin = 23  # Change this to the correct pin number

# Initialize the DHT11 sensor pin
dht11 = machine.Pin(DHpin, machine.Pin.OPEN_DRAIN)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
mqtt = MQTTClient(client_id="",
                      server=MQTT_BROKER,
                      user=MQTT_USER,
                      password=MQTT_PASS)
def connect_anything():
    try:
        # connect to wifi  
        wlan.connect(WIFI_SSID, WIFI_PASS)
        print("connecting to wifi...")
        while not wlan.isconnected():
            time.sleep(0.5)
        print("connected to wifi")

        mqtt.connect()
        print("connected to MQTT broker")
    except:
        pass

connect_anything()

def set_pin_low():
    dht11.init(mode=machine.Pin.OPEN_DRAIN)
    dht11.value(0)

def set_pin_high():
    dht11.init(mode=machine.Pin.IN)

async def read_data():
    # Send start signal
    set_pin_low()
    time.sleep_ms(18)
    set_pin_high()
    time.sleep_us(40)

    # Change pin to input to read data
    dht11.init(mode=machine.Pin.IN, pull=None)

    # Read and interpret the data
    data = []
    for i in range(5):  # Read 5 bytes
        byte = 0
        for j in range(8):  # Each byte has 8 bits
            while not dht11.value():
                print('a')
                pass
            time.sleep_us(28)
            if dht11.value():
                byte |= 1 << (7 - j)
            timeout = 100  # Timeout counter
            while dht11.value():
                if timeout <= 0:
                    print("Timeout - Sensor did not respond")
                    break
                timeout -= 1
                time.sleep_us(1)  # Short delay to decrement the timeout
        data.append(byte)
    print('okkk')

    dht11.init(mode=machine.Pin.OPEN_DRAIN)
    set_pin_high()

    return data

async def publish_temp_humid():
    while True:
        print('hi')
        # Specify the register address to access the current temperature
        data = await read_data()
        humid = data[0] + data[1] / 10
        temp = data[2] + data[3] / 10
        payload = {
            "humid": round(humid, 2),
            "temp": round(temp, 2)
            }
        
        checksum = sum(data[:4]) & 0xFF
        if checksum != data[4]:
            print("-- Checksum Error!")
            continue

        print("-- OK")

        print(f"published payload: {payload}")
        mqtt.publish("daq2023/group4/temp_hum", json.dumps(payload))
        await asyncio.sleep(3)

asyncio.create_task(publish_temp_humid())
asyncio.run_until_complete()
