from machine import ADC, Pin
import dht
import _thread
import time

dht_sensor = dht.DHT11(Pin(32)) # I1
sensor_data = None
sensor_data_lock = _thread.allocate_lock()



def sensor_thread():
    global sensor_data
    while True:
        try:
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            hum = dht_sensor.humidity()
            with sensor_data_lock:
                sensor_data = (temp, hum)
        except Exception as e:
            print("Sensor read error:", e)
        time.sleep(1)  # Delay between sensor readings

# Starting the sensor thread
_thread.start_new_thread(sensor_thread, ())


def get_sensor_data():
    global sensor_data
    with sensor_data_lock:
        while sensor_data is None:
            time.sleep(0.1)
            print('waiting for avalible')
        return sensor_data

