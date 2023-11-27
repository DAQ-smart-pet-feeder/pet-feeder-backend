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
from temp_hum import get_sensor_data
from lamp import get_lamp

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
WEEKDAYS = ["Monday", "Tueday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


meal_schedules = []


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

lamp = Pin(25, Pin.OUT)
lamp.value(1)  # turn USB lamp off initially

def feed_for(sec):
    lamp.value(0)
    for n in range(sec, 0, -1):
        print(f'feeding for {n} seconds')
        time.sleep(1)
    lamp.value(1) # turn lamp off
    print('feed finished')

def quick_meal_callback(payload):
    por = int(payload)
    if por <= 0:
        print('payload received with value less than 0')
        return
    feed_for(por)


def get_current_day():
    # Get the current weekday as a string
    return WEEKDAYS[utime.localtime()[6]]

def get_current_time():
    # Get the current time as a string formatted as HH:MM
    now = utime.localtime()
    return '{:02}:{:02}'.format(now[3], now[4])

def set_schedule(new_schedule):
    global meal_schedules
    meal_schedules = []


def meal_plan_callback(payload):
    # Decode the payload into a Python object
    new_schedules = json.loads(payload)
    
    # Clear existing schedules and set new ones
    global meal_schedules
    meal_schedules = []  # Reset the schedule list if you want to replace the schedules completely

    # Set new schedules from the payload
    for schedule in new_schedules:
        if schedule['enable_status'] == 1:
            meal_schedules.append(schedule)
    

def sub_callback(topic, payload):
    topic_name = topic.decode()
    payload = payload.decode('utf-8')
    if topic_name == 'daq2023/group4/quick_meal':
        quick_meal_callback(payload)
    elif topic_name == 'daq2023/group4/meal_plan':
        meal_plan_callback(payload)
        
def scheduler():
    current_day = get_current_day()
    current_time = get_current_time()

    # Check if it's time for any of the scheduled feedings
    for schedule in meal_schedules:
        if current_day in schedule['day'] and current_time == schedule['time']:
            feed_for(schedule['por'])
    
        
mqtt.set_callback(sub_callback)
mqtt.subscribe("daq2023/group4/quick_meal")
mqtt.subscribe("daq2023/group4/meal_plan")


async def check_mqtt_msg():
    while True:
        mqtt.check_msg()
        await asyncio.sleep(60)
        
        
async def scheduleing():
    while True:
        scheduler()
        await asyncio.sleep_ms(10)


async def publish_tank_data():
    while True:
        await asyncio.sleep(10800) # every 3hr
        temp, hum = get_sensor_data()
        tank_payload = {
            "temp": temp,
            "hum": hum,
            }
        print('published')
        mqtt.publish('daq2023/group4/sensortank', json.dumps(tank_payload))
        

async def publish_remaining_percent():
    while True:
        await asyncio.sleep(1)
        sensor_tank_payload = {
            "rem_percent": round(find_distance() / FOOD_CONTAINER_AMOUNT * 100, 2),
            "feed_status": lamp.value()
            }
        print('published: ', sensor_tank_payload)
        
        mqtt.publish('daq2023/group4/tank', json.dumps(sensor_tank_payload))



asyncio.create_task(publish_tank_data())
asyncio.create_task(publish_remaining_percent())
asyncio.create_task(check_mqtt_msg())


asyncio.run_until_complete()
