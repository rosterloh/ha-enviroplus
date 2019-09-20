#!/usr/bin/env python3
from subprocess import check_output
from re import findall
import psutil
import sys
import os
import threading, time, signal
from datetime import timedelta
import datetime as dt
import paho.mqtt.client as mqtt
import pytz
from pytz import timezone
from json import dumps
from display import Display
from sensors import Sensors
__version__ = '0.0.1'

UTC = pytz.utc
DEFAULT_TIME_ZONE = timezone('Europe/London')
broker_url = "hassio.local"
broker_port = 1883
deviceName = "EnviroPlus"
client = mqtt.Client(client_id=deviceName)
client.username_pw_set("hass", "QV*4$YqajXvf")
SYSFILE = '/sys/devices/platform/soc/soc:firmware/get_throttled'
WAIT_TIME_SECONDS = 60
display = Display()
sensors = Sensors()

class ProgramKilled(Exception):
    client.loop_stop()
    client.disconnect()
    pass

def signal_handler(signum, frame):
    raise ProgramKilled

class Job(threading.Thread):
    def __init__(self, interval, execute, *args, **kwargs):
        threading.Thread.__init__(self)
        self.daemon = False
        self.stopped = threading.Event()
        self.interval = interval
        self.execute = execute
        self.args = args
        self.kwargs = kwargs

    def stop(self):
        self.stopped.set()
        self.join()

    def run(self):
        while not self.stopped.wait(self.interval.total_seconds()):
            self.execute(*self.args, **self.kwargs)

def utc_from_timestamp(timestamp: float) -> dt.datetime:
    """Return a UTC time from a timestamp."""
    return UTC.localize(dt.datetime.utcfromtimestamp(timestamp))

def as_local(dattim: dt.datetime) -> dt.datetime:
    """Convert a UTC datetime object to local time zone."""
    if dattim.tzinfo == DEFAULT_TIME_ZONE:
        return dattim
    if dattim.tzinfo is None:
        dattim = UTC.localize(dattim)

    return dattim.astimezone(DEFAULT_TIME_ZONE)

def updateSensors():
    values = sensors.read_values()
    display.display_text("temperature", values["raw_temperature"], "°C")
    values["disk_use"] = str(psutil.disk_usage('/').percent)
    values["memory_use"] = str(psutil.virtual_memory().percent)
    values["cpu_usage"] = str(psutil.cpu_percent(interval=None))
    values["swap_usage"] = str(psutil.swap_memory().percent)
    values["power_status"] = get_rpi_power_status()
    values["last_boot"] = str(as_local(utc_from_timestamp(psutil.boot_time())).isoformat())

    client.publish(
        topic="homeassistant/sensor/" + deviceName + "/state",
        payload=dumps(values),
        qos=1,
        retain=False
    )

def get_rpi_power_status():
    _throttled = open(SYSFILE, 'r').read()[:-1]
    _throttled = _throttled[:4]
    if _throttled == '0':
        return 'Everything is working as intended'
    elif _throttled == '1000':
        return 'Under-voltage was detected, consider getting a uninterruptible power supply for your Raspberry Pi.'
    elif _throttled == '2000':
        return 'Your Raspberry Pi is limited due to a bad powersupply, replace the power supply cable or power supply itself.'
    elif _throttled == '3000':
        return 'Your Raspberry Pi is limited due to a bad powersupply, replace the power supply cable or power supply itself.'
    elif _throttled == '4000':
        return 'The Raspberry Pi is throttled due to a bad power supply this can lead to corruption and instability, please replace your changer and cables.'
    elif _throttled == '5000':
        return 'The Raspberry Pi is throttled due to a bad power supply this can lead to corruption and instability, please replace your changer and cables.'
    elif _throttled == '8000':
        return 'Your Raspberry Pi is overheating, consider getting a fan or heat sinks.'
    else:
        return 'There is a problem with your power supply or system.'

def create_payload(name, unit, value, uid, model, manufacturer, device_class = None):
    data = {
        "name": deviceName + name,
        "state_topic": "homeassistant/sensor/" + deviceName + "/state",
        "unit_of_measurement": unit,
        "value_template": value,
        "unique_id": deviceName.lower() + uid,
        "device": {
            "identifiers": deviceName.lower() + "_sensor",
            "name": deviceName + "Sensors",
            "model": model,
            "manufacturer": manufacturer
        }
    }
    if device_class:
        data["device_class"] = device_class
    
    return dumps(data)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

def on_message(client, userdata, message):
    print("message received ", str(message.payload.decode("utf-8")))
    print("message topic=", message.topic)
    print("message qos=", message.qos)
    print("message retain flag=", message.retain)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker_url, broker_port)

    client.publish(
        topic="homeassistant/sensor/"+ deviceName +"/"+ deviceName +"Temp/config",
        payload=create_payload("Temp", "°C", "{{ value_json.temperature}}", "_sensor_temperature", "BME280", "Bosch", device_class="temperature"),
        qos=1, retain=True
    )
    client.publish(
        topic="homeassistant/sensor/"+ deviceName +"/"+ deviceName +"Humidity/config",
        payload=create_payload("Humidity", "%", "{{ value_json.humidity}}", "_sensor_humidity", "BME280", "Bosch", device_class="humidity"),
        qos=1, retain=True
    )
    client.publish(
        topic="homeassistant/sensor/"+ deviceName +"/"+ deviceName +"CpuTemp/config",
        payload=create_payload("CpuTemp", "°C", "{{ value_json.cpu_temperature}}", "_sensor_cpu_temperature", "RPI "+deviceName, "RPI", device_class="temperature"),
        qos=1, retain=True
    )
    client.publish(
        topic="homeassistant/sensor/"+ deviceName +"/"+ deviceName +"DiskUse/config",
        payload=create_payload("DiskUse", "%", "{{ value_json.disk_use}}", "_sensor_disk_use", "RPI "+deviceName, "RPI"),
        qos=1, retain=True
    )
    client.publish(
        topic="homeassistant/sensor/"+ deviceName +"/"+ deviceName +"MemoryUse/config",
        payload=create_payload("MemoryUse", "%", "{{ value_json.memory_use}}", "_sensor_memory_use", "RPI "+deviceName, "RPI"),
        qos=1, retain=True
    )
    client.publish(
        topic="homeassistant/sensor/"+ deviceName +"/"+ deviceName +"CpuUsage/config",
        payload=create_payload("CpuUsage", "%", "{{ value_json.cpu_usage}}", "_sensor_cpu_usage", "RPI "+deviceName, "RPI"),
        qos=1, retain=True
    )
    client.publish(
        topic="homeassistant/sensor/"+ deviceName +"/"+ deviceName +"SwapUsage/config",
        payload=create_payload("SwapUsage", "%", "{{ value_json.swap_usage}}", "_sensor_swap_usage", "RPI "+deviceName, "RPI"),
        qos=1, retain=True
    )
    client.publish(
        topic="homeassistant/sensor/"+ deviceName +"/"+ deviceName +"PowerStatus/config",
        payload=create_payload("PowerStatus", "", "{{ value_json.power_status}}", "_sensor_power_status", "RPI "+deviceName, "RPI"),
        qos=1, retain=True
    )
    client.publish(
        topic="homeassistant/sensor/"+ deviceName +"/"+ deviceName +"LastBoot/config",
        payload=create_payload("LastBoot", "%", "{{ value_json.last_boot}}", "_sensor_last_boot", "RPI "+deviceName, "RPI", device_class="timestamp"),
        qos=1, retain=True
    )
    job = Job(interval=timedelta(seconds=WAIT_TIME_SECONDS), execute=updateSensors)
    job.start()
    client.loop_forever()

    while True:
        try:
            time.sleep(1)
        except ProgramKilled:
            print("Program killed: running cleanup code")
            sys.stdout.flush()
            job.stop()
            break

