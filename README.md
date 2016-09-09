# Bresser Weather Center

This library allows to decode the radio signal sent by the Bresser Weather Center 5-IN-1 sensors.
http://www.bresser.de/en/Weather-Time/BRESSER-Weather-Center-5-in-1.html

I tested it only with a RTL2838 dongle, using the rtl-sdr software (http://www.rtl-sdr.com/).

Note that I've not fully reversed yet the data packed sent by the sensors, the work is still ongoing and the library still need to be tested a lot.

## Example
```
from bresser import *

def process_packet(p):
                        
    print "Humidity: %d%% " % p.getHumidity(),
    print "Temperature: %.1f" % p.getTemperature() + u"\u00b0 ",
    print "Wind: %.1f m/s " % p.getWindSpeed(),
    print "Rain: %.1f mm" % p.getRain(),
    print ""
 
if __name__ == "__main__":

    b = Bresser()
    b.set_callback(process_packet)
    b.process_radio_data()
    
```
```
rtl_fm -M am -f 868.300M -s 48k -g 50 -l 15  | ./test.py    
```
