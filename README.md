# Bresser Weather Center

The [BRESSER weather center 5-in-1](http://www.bresser.de/en/Weather-Time/BRESSER-Weather-Center-5-in-1.html) (model 7002510) outdoor sensor transfers all measured values for wind speed, wind direction, humidity, temperature and precipitation rate to the base station using radio signals and a proprietary protocol.

This library decodes the readings sent by the Bresser sensors. I tested it only with a RTL2838 dongle, using the rtl-sdr software ([http://www.rtl-sdr.com/](http://www.rtl-sdr.com/)).

Note that I've not fully reversed yet the data packed sent by the sensor, the work is still ongoing and the library still need to be tested a lot.

## Reversing and packet structure
The sensor transmit the packet on the 868.300M frequency with AM modulation.

Following a capture of the wave already demodulated:

![Radio Signal](https://www.andreafabrizi.it/img/bresser_radio_signal.png "Radio wave")

The packet is 264 bits long and the bits are ecoded with 1 for high and 0 for low. The data should be read as nybble (half byte) in BCD format.

With the sampling rate set to 48Khz we have an average of 6 samples per bit.

Following the packet structure I've reversed so far, not highlighted the parts who still need to be identified.

![Packet structure](https://www.andreafabrizi.it/img/bresser_packet.png)

## Get the code
Visit the project page on [GitHub](https://github.com/andreafabrizi/BresserWeatherCenter) or get the code with the command:
```
git clone https://github.com/andreafabrizi/BresserWeatherCenter.git
```

## Usage example
```
from bresser import *

b = Bresser(printdata=True)
b.process_radio_data()
```

```
rtl_fm -M am -f 868.300M -s 48k -g 49.6 -l 30  | ./test.py

2016-09-09 19:59:07:  Humidity: 50%  Temperature: 20.7°  Wind: 2.2 Km/h  Rain: 4.0 mm
2016-09-09 19:59:17:  Humidity: 50%  Temperature: 20.7°  Wind: 2.2 Km/h  Rain: 4.0 mm
2016-09-09 19:59:30:  Humidity: 49%  Temperature: 20.6°  Wind: 2.2 Km/h  Rain: 4.0 mm
```

Note that the gain and the squelch level most probably needs to be adjusted, depending on your device and antenna.

## Antenna
As antenna I used a self made metal wire 8.64 cm long (300000/868000/4) and it works quite well.

## To do
* Decode wind direction data
* Verify if what I identified as sync is actually the sync or the device ID
