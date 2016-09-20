#!/usr/bin/python
#
# Radio signal decoder
# for BRESSER WEATHER CENTER 5-IN-1
#
# Copyright (C) 2016 Andrea Fabrizi <andrea.fabrizi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# rtl_fm command to use:
#   rtl_fm -M am -f 868.300M -s 48k -g 50 -l 15  | ./test.py
#
# Packet structure:
#
# 1010101010101010101010101010101010101010 0010110111010100111 0101 1101 101110111111111111111110011111111100111101111101010001111110111000111111011011111110111111111000101000100100010000000000000000011 0000 0000 0110 0001 0000 0101 0111 0000 0010 0011 1000 0001 0010 0000001
# |                                        |                   |                                                                                                                                           |    |    |              |    |    |    |    |    |    |    |
# 1                                       41                  60                                                                                                                                          197  201  205            217  221  225  229  233  237   241  245
# Preamble                               Sync                                                                                                                                                            WindD1    WindDec        TempD2      +- TempD1     HumD2 RainD2
#                                                                                                                                                                                                            WindD2                    TempDec        HumD1           RainDec
#
import sys
import struct
import math
import time
import sqlite3
import signal
import os

class BufferNoMoreBits(Exception):
    pass

class StdinNoMoreData(Exception):
    pass

class packet():

    def __init__(self, buffer, debug = False):
        self.buffer = buffer
        self.offset = 0
        self.size = len(buffer)
        self.humidity = 0
        self.temperature = 0.0
        self.wind_speed = 0.0
        self.rain_month = 0.0
        self.debug = debug

    #Convert the bit stream encoded in BCD to digits
    def bcd2Digit(self, buff):
        res = ""
        digits = [buff[i:i+4] for i in range(0, len(buff), 4)]
        for digit in digits:
            n = int(digit, 2)
            res += str(n)
        return int(res)

    #Gets n bit from the stream
    def getBits(self, n):
        if self.offset + n> self.size:
            raise BufferNoMoreBits

        bits = self.buffer[self.offset:self.offset+n]
        self.offset = self.offset + n
        return bits

    #Get a single bit from the stream
    def getBit(self):
        return ord(self.getBits(1))

    def parse(self):

        if self.debug:
            print "%d -> %s" % (len(self.buffer), self.buffer)

        try:

            #Preamble
            data = self.getBits(40)
            if data != "1010101010101010101010101010101010101010":
                return 2

            #Is the sync?
            data = self.getBits(19)

            #Unknown data
            data = self.getBits(137)

            #Wind speed
            data = self.getBits(4)
            wind_digit_1 = self.bcd2Digit(data)

            data = self.getBits(4)
            wind_digit_2 = self.bcd2Digit(data)

            data = self.getBits(4)
            wind_decimal = self.bcd2Digit(data)

            wind = wind_digit_1 * 10 + wind_digit_2 + (float(wind_decimal)/10)

            if wind >= 0 and wind <= 99:
                self.wind_speed = wind
            else:
                return 3

            #Unknown
            data = self.getBits(4)
            #print self.bcd2Digit(data)

            #Unknown
            data = self.getBits(4)
            #print self.bcd2Digit(data)

            #Temperature
            data = self.getBits(4)
            temp_digit_2 = self.bcd2Digit(data)

            data = self.getBits(4)
            temp_decimal = self.bcd2Digit(data)

            #Junk or is the sign indicator?
            data = self.getBits(4)
            temp_sign = self.bcd2Digit(data)

            data = self.getBits(4)
            temp_digit_1 = self.bcd2Digit(data)

            temp = temp_digit_1 * 10 + temp_digit_2 + (float(temp_decimal)/10)

            if temp_sign != 0:
                temp = 0 - temp

            if temp >= -50 and temp <= 50:
                self.temperature = temp
            else:
                return 3

            #Umidity
            data = self.getBits(8)
            hum = self.bcd2Digit(data)
            if hum >= 0 and hum <= 100:
                self.humidity = hum
            else:
                return 4

            #Rain. Seems that the first digit of the value is missing, and only the less significant and the decimal digits are sent
            data = self.getBits(4)
            rain_digit_2 = self.bcd2Digit(data)

            data = self.getBits(4)
            rain_decimal = self.bcd2Digit(data)

            rain_mm = rain_digit_2 + (float(rain_decimal)/10)
            self.rain_month = rain_mm

        except BufferNoMoreBits as e:
            return 1

        return 0

    def printReadings(self):
        print time.strftime("%Y-%m-%d %H:%M:%S: "),
        print "Humidity: %d%% " % self.humidity,
        print "Temperature: %.1f" % self.temperature + u"\u00b0C ",
        print "Wind: %.1f Km/h " % self.getWindSpeedKm(),
        print "Rain: %.1f mm" % self.getRain(),
        print ""

    def store(self, dest):
        try:
            f = open(dest, "a")
            f.write(time.strftime("%Y-%m-%d %H:%M:%S: "))
            f.write(self.buffer)
            f.write("\n")
            f.close()
        except Exception as e:
            print "Error storing sample to file: %s" % e

    def getHumidity(self):
        return self.humidity

    def getTemperature(self):
        return self.temperature

    def getIntTemperature(self):
        return int(self.temperature * 10)

    def getWindSpeed(self):
        return self.wind_speed

    def getWindSpeedKm(self):
        return self.wind_speed * 3.6

    def getIntWindSpeed(self):
        return int(self.wind_speed * 10)

    def getIntWindSpeedKm(self):
        return int(self.getIntWindSpeed() * 10)

    def getRain(self):
        return self.rain_month


class Bresser():

    def __init__(self, dumpfile = None, debug = False, printdata = False):
        self.dumpfile = dumpfile
        self.printdata = printdata
        self.callback_func = None
        self.debug = debug
        pass

    def set_callback(self, callback_func):
        self.callback_func = callback_func

    def process_packet(self, buffer):

        p = packet(buffer, self.debug)

        if p.parse() == 0:
            if self.printdata:
                p.printReadings()

            if self.dumpfile:
                p.store(self.dumpfile)

            if self.callback_func:
                self.callback_func(p)

        elif self.debug:
            print "Invalid packed received"

    def get_sample_stdin(self):
        short = sys.stdin.read(2)
        if not short:
            raise StdinNoMoreData

        return abs(struct.unpack("h", short)[0])

    def process_signal(self, samples):

        buffer = ""

        #Calculatig the average value
        average = max(samples) / 2

        #Normalising the samples
        for index, sample in enumerate(samples):
            if samples[index] >= average:
                #print "%d -> 1" % samples[index]
                samples[index] = 1
            else:
                #print "%d -> 0" % samples[index]
                samples[index] = 0

        prev_sample = 0
        count_prev_samples = 0

        #Reducing the samples
        for sample in samples:
            if sample == prev_sample:
                count_prev_samples += 1
                continue

            #6 is the rate for a 48Khz sampling
            rate = math.ceil(float(count_prev_samples) / 6)
            buffer+=str(prev_sample) * int(rate)

            prev_sample = sample
            count_prev_samples = 0

        #Stripping zeros from the signal
        buffer = buffer.strip("0")

        self.process_packet(buffer)

    #Detecting sequences of data separated by silence
    def process_radio_data(self):

        samples = list()
        prev_sample = 0

        while True:

            count_prev_samples = 0

            #Reading silence
            sample = self.get_sample_stdin()
            while (sample < 10):
                sample = self.get_sample_stdin()

            #Reading all data until there's silence for at least 300 samples (300 is good for a 48Khz sampling)
            while True:
                samples.append(sample)
                sample = self.get_sample_stdin()
                if sample == 0 and prev_sample == 0 and count_prev_samples > 300:
                    break

                if sample == prev_sample:
                    count_prev_samples += 1
                else:
                    count_prev_samples = 0

                prev_sample = sample

            self.process_signal(samples)
            samples = []
