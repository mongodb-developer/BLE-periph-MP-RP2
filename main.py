from machine import Pin
import time

led = Pin('LED', Pin.OUT)

while True:
  time.sleep_ms(500)
  led.toggle()
