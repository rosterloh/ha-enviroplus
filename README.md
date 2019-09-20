# Enviro+ Monitor for Home Assistant
This python script that runs every 60 seconds and sends several system data over MQTT. It uses the MQTT Discovery for Home Assistant so you don’t need to configure anything in Home Assistant if you have discovery enabled for MQTT

It currently logs the following data:
* BME280 Temperature
* BME280 Humidity
* CPU usage
* CPU temperature
* Disk usage
* Memory usage
* Power status of the RPI
* Last boot

## Installation:
1. Enable I2C and SPI
2. pip3 install -r requirements.txt --user
3. sudo cp ~/ha-enviroplus/enviroplus-monitor.service /etc/systemd/system
4. sudo systemctl enable enviroplus-monitor.service
5. sudo systemctl start system_sensor.service

## Home Assistant configuration:
### Configuration:
The only config you need in Home Assistant is the following:
```yaml
mqtt:
  discovery: true
  discovery_prefix: homeassistant
```

### Lovelace UI example:
I have used following custom plugins for lovelace:
* vertical-stack-in-card
* mini-graph-card
* bar-card

Config:
```yaml
- type: 'custom:vertical-stack-in-card'
    title: Enviro+ System Monitor
    cards:
      - type: horizontal-stack
        cards:
          - type: custom:mini-graph-card
            entities:
              - sensor.enviropluscpuusage
            name: CPU
            line_color: '#2980b9'
            line_width: 2
            hours_to_show: 24
          - type: custom:mini-graph-card
            entities:
              - sensor.enviroplustemperature
            name: Temp
            line_color: '#2980b9'
            line_width: 2
            hours_to_show: 24
      - type: custom:bar-card
        entity: sensor.enviroplusdiskuse
        title: HDD
        title_position: inside
        align: split
        show_icon: true
        color: '#00ba6a'
      - type: custom:bar-card
        entity: sensor.enviroplusmemoryuse
        title: RAM
        title_position: inside
        align: split
        show_icon: true
      - type: entities
        entities:
          - sensor.enviropluslastboot
          - sensor.enviropluspowerstatus
```