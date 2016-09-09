#!/usr/bin/python
#
# rtl_fm -M am -f 868.300M -s 48k -g 50 -l 15  | ./test.py                                                                                                                                                                                                                      Displayed daily on lcd        
#
#
import sys
import time
import signal
import os
from bresser import *

def process_packet(p):
                        
    print "Humidity: %d%% " % p.getHumidity(),
    print "Temperature: %.1f" % p.getTemperature() + u"\u00b0 ",
    print "Wind: %.1f m/s " % p.getWindSpeed(),
    print "Rain: %.1f mm" % p.getRain(),
    print ""
 
if __name__ == "__main__":

    b = Bresser(dumpfile="/tmp/data.txt", debug=False, printdata=False)
    b.set_callback(process_packet)
    b.process_radio_data()

