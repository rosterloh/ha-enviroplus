from bme280 import BME280
from pms5003 import PMS5003, ReadTimeoutError

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

_comp_factor = 1.2

class Sensors():
    def __init__(self):
        self.bus = SMBus(1)
        self.bme280 = BME280(i2c_dev=self.bus)
        self.pms5003 = PMS5003()
        self.comp_factor = _comp_factor

    def read_values(self):
        values = {}
        cpu_temp = self._get_cpu_temperature()
        raw_temp = self.bme280.get_temperature()
        comp_temp = raw_temp - ((cpu_temp - raw_temp) / self.comp_factor)
        values["raw_temperature"] = "{:.2f}".format(raw_temp)
        values["cpu_temperature"] = "{:.2f}".format(cpu_temp)
        values["temperature"] = "{:.2f}".format(comp_temp)
        values["pressure"] = "{:.2f}".format(self.bme280.get_pressure() * 100)
        values["humidity"] = "{:.2f}".format(self.bme280.get_humidity())
        try:
            pm_values = self.pms5003.read()
            values["P2"] = str(pm_values.pm_ug_per_m3(2.5))
            values["P1"] = str(pm_values.pm_ug_per_m3(10))
        except ReadTimeoutError:
            self.pms5003.reset()
            pm_values = self.pms5003.read()
            values["P2"] = str(pm_values.pm_ug_per_m3(2.5))
            values["P1"] = str(pm_values.pm_ug_per_m3(10))
        return values

    def set_temperature_compensation(self, comp):
        self.comp_factor = comp

    def _get_cpu_temperature(self):
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = f.read()
            temp = int(temp) / 1000.0
        return temp

if __name__ == '__main__':
    try:
        sensors = Sensors()
        values = sensors.read_values()
        print("Raw Temperature: " + values["raw_temperature"] + " C")
        print("Compensated Temperature: " + values["temperature"] + " C")
        print("Humidity: " + values["humidity"] + " %")
        print("Pressure: " + values["pressure"] + " hPa")
        print("PM2.5: " + values["P2"] + " ug/m3")
        print("PM10: " + values["P1"] + " ug/m3")
    except KeyboardInterrupt:
        pass