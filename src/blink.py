from machine import Pin
import utime

# Onboard LED is on GPIO 25
led = Pin(25, Pin.OUT)

while True:
    led.toggle()
    utime.sleep(0.5)  # Sleep for 500ms