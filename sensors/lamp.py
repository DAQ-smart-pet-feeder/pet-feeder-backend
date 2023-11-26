from machine import Pin,I2C,ADC
import _thread
import time



lamp = None
lamp_lock = _thread.allocate_lock()


lamp.value(1)  # turn USB lamp off initially


def lamp_thread():
    global sensor_data
    while True:
        try:
            with sensor_data_lock:
                lamp = Pin(25, Pin.OUT)
        except Exception as e:
            print("Sensor read error:", e)
        time.sleep(1)  # Delay between lamp readings
        
        
def get_lamp():
    global lamp
    with lamp_lock:
        while lamp_data is None:
            time.sleep(0.1)
            print('waiting for avalible')
        return lamp

