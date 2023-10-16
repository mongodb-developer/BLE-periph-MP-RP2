from machine import ADC, Pin
import time

led = Pin('LED', Pin.OUT)
adc = ADC(4)

while True:
  time.sleep_ms(500)
  led.toggle()
  temperature =  27.0 - ((adc.read_u16() * 3.3 / 65535) - 0.706) / 0.001721
  print("T: {}°C".format(temperature))
