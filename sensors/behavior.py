from machine import ADC, Pin
from time import sleep

# Define the analog pin where the sensor is connected (e.g., P0)
analog_pin = ADC(Pin(33, Pin.OUT))

    
def is_something_block():
    # Read the analog value from the sensor
    sensor_value = analog_pin.read()

    # Convert the analog value to distance using your formula
    distance = 28250 / (sensor_value - 229.5)
    
    return distance >= 0
