#!/usr/bin/python
#
# rtl_fm -M am -f 868.300M -s 48k -g 50 | ./test.py                                                                                                                                                                                                                      Displayed daily on lcd        
#
#
from bresser import *

def process_packet(p):
                        
    print "Humidity: %d%% " % p.getHumidity(),
    print "Temperature: %.1f" % p.getTemperature() + u"\u00b0 ",
    print "Wind: %.1f m/s %s" % (p.getWindSpeed(), p.getWindDirection()),
    print "Rain: %.1f mm" % p.getRain(),
    print ""
 
if __name__ == "__main__":

    #Noise neede to be adjusted manually
    b = Bresser(noise = 700)
    b.set_callback(process_packet)
    b.process_radio_data()

