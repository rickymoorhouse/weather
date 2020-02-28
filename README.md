# Raspberry Pi Weather Station

## Environment Variables

LOG_LEVEL - level of logging (default INFO)
SYSLOG_TARGET - optional host:port to send log messages to
WIND_PIN - GPIO pin for wind sensor (default 22)
GRAPHITE_PREFIX - prefix for the values sent to graphite (default weather)
GRAPHITE_SERVER - where to send metrics (default localhost)
USE_BME280 - also log readings from BME280 - temperature, humidity, pressure (default false)



## Running weather station as a service

Create an environment file at /etc/default/weather containing the environment variables desired from above

Copy the init script into /etc/systemd/system/ and register it with systemd

    $ sudo cp init/wind.service /etc/systemd/system/weather.service
    $ sudo systemctl enable weather.service
    Created symlink from /etc/systemd/system/multi-user.target.wants/weather.service to /etc/systemd/system/weather.service.

Then you can start it

    $ sudo systemctl start weather.service

To check it has started successfully have a look in syslog

