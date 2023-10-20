import aioble
import bluetooth
from machine import ADC, Pin
from micropython import const
import struct
import uasyncio as asyncio

_ADVERTISING_INTERVAL_US = const(200_000)
_APPEARANCE_MULTI_SENSOR = const(0x0552)

# Constants for the device information service
_SVC_DEVICE_INFO = bluetooth.UUID(0x180A)
_CHAR_MANUFACTURER_NAME_STR = bluetooth.UUID(0x2A29)
_CHAR_MODEL_NUMBER_STR = bluetooth.UUID(0x2A24)
_CHAR_SERIAL_NUMBER_STR = bluetooth.UUID(0x2A25)
_CHAR_FIRMWARE_REV_STR = bluetooth.UUID(0x2A26)
_CHAR_HARDWARE_REV_STR = bluetooth.UUID(0x2A27)

# Constants for the Environmental Sensing Service
_SVC_ENVIRONM_SENSING = bluetooth.UUID(0x181A)
_CHAR_TEMP_MEASUREMENT = bluetooth.UUID(0x2A1C)
_DESC_ES_TRIGGER_SETTING = bluetooth.UUID(0x290D)
_TEMP_MEASUREMENT_INTERVAL_MS = const(15_000)

svc_dev_info = aioble.Service(_SVC_DEVICE_INFO)
aioble.Characteristic(svc_dev_info, _CHAR_MANUFACTURER_NAME_STR, read=True, initial='Jorge')
aioble.Characteristic(svc_dev_info, _CHAR_MODEL_NUMBER_STR, read=True, initial='J-0001')
aioble.Characteristic(svc_dev_info, _CHAR_SERIAL_NUMBER_STR, read=True, initial='J-0001-0000')
aioble.Characteristic(svc_dev_info, _CHAR_FIRMWARE_REV_STR, read=True, initial='0.0.1')
aioble.Characteristic(svc_dev_info, _CHAR_HARDWARE_REV_STR, read=True, initial='0.0.1')

svc_env_sensing = aioble.Service(_SVC_ENVIRONM_SENSING)
temperature_char = aioble.Characteristic(svc_env_sensing, _CHAR_TEMP_MEASUREMENT, read=True, notify=True)
aioble.Descriptor(temperature_char, _DESC_ES_TRIGGER_SETTING, write=True, initial=struct.pack("<B", 0))

aioble.register_services(svc_dev_info, svc_env_sensing)

connected = False
connection = None
led = Pin('LED', Pin.OUT)
adc = ADC(4)

def _encode_ieee11073(value, precision=2):
    """ Binary representation of float value as IEEE-11073:20601 32-bit FLOAT """
    return int(value * (10 ** precision)).to_bytes(3, 'little', True) + struct.pack('<b', -precision)

async def task_peripheral():
  """ Task to handle advertising and connections """
  global connected, connection
  while True:
    connected = False
    async with await aioble.advertise(
      _ADVERTISING_INTERVAL_US,
      appearance=_APPEARANCE_MULTI_SENSOR,
      name='RP2-SENSOR',
      services=[_SVC_DEVICE_INFO, _SVC_ENVIRONM_SENSING]
    ) as connection:
      connected = True
      print("Connected from ", connection.device)
      await connection.disconnected(timeout_ms=None)
      connection = None
      print("Disconnect")

async def task_flash_led():
  """ Blink the on-board LED, faster if connected and slower if connected  """
  BLINK_DELAY_MS_FAST = const(200)
  BLINK_DELAY_MS_SLOW = const(500)
  while True:
    led.toggle()
    if connected:
      await asyncio.sleep_ms(BLINK_DELAY_MS_SLOW)
    else:
      await asyncio.sleep_ms(BLINK_DELAY_MS_FAST)

async def task_sensor():
  """ Task to handle sensor measures """
  while True:
    temperature =  27.0 - ((adc.read_u16() * 3.3 / 65535) - 0.706) / 0.001721
    print("T: {}°C".format(temperature))
    payload = struct.pack("<B4s", 0, _encode_ieee11073(temperature))
    temperature_char.write(payload)
    if connection is not None:
        temperature_char.notify(connection, payload)
    await asyncio.sleep_ms(_TEMP_MEASUREMENT_INTERVAL_MS)

async def main():
  """ Create all the tasks """
  tasks = [
    asyncio.create_task(task_peripheral()),
    asyncio.create_task(task_flash_led()),
    asyncio.create_task(task_sensor()),
  ]
  await asyncio.gather(*tasks)

asyncio.run(main())
