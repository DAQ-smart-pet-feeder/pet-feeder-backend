from machine import ADC, Pin
import dht
import time

dht_sensor = dht.DHT11(Pin(32)) # I1


while True:
    dht_sensor.measure()
    temperature = dht_sensor.temperature()
    humidity = dht_sensor.humidity()
    print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
    print("---------------------------------------------------- ")
    
    time.sleep(5)