#!/bin/env python

from __future__ import print_function,division,absolute_import,unicode_literals


#~ SCREEN_RESOLUTION_WIDTH = 1810
#~ SCREEN_RESOLUTION_HEIGHT = 1050

import krpc

import argparse
import sys
import time

HIGH_SPEED =5

def parseArgs(argv):
    parser = argparse.ArgumentParser(description="KRPC miner")
    parser.add_argument('-a','--address',default="127.0.0.1")
    args = parser.parse_args(argv[1:])
    return args

class Miner2(object):
    def __init__(self, argv):
        self.__m_args = parseArgs(argv)

    def isFull(self):
        vessel = self.m_vessel
        resources = vessel.resources

        for resName in ("LiquidFuel","Ore"):
            if resources.max(resName) - resources.amount(resName) > 0.5:
                return False
        return True

    def isOreFull(self):
        vessel = self.m_vessel
        resources = vessel.resources

        return (resources.max("Ore") - resources.amount("Ore")) < 0.5

    def nextAlarm(self):
        nextAlarm = None
        if not self.m_alarmClock.available:
            return None

        for alarm in self.m_alarmClock.alarms:
            if nextAlarm is None or alarm.time < nextAlarm.time:
                nextAlarm = alarm

        return nextAlarm

    def mine(self):
        vessel = self.m_vessel
        conn = self.m_conn

        panels = vessel.parts.solar_panels
        #~ print(panels)

        resources = vessel.resources

        print(resources.names)
        #~ print(resources.amount(b"ElectricCharge"))
        max_charge = resources.max(b"ElectricCharge")
        percent90 = max_charge * 0.9
        percent10 = max_charge * 0.1
        electric_charge = conn.add_stream(resources.amount,b"ElectricCharge")

        mining = False
        converting = False

        targetSpeed = HIGH_SPEED
        slept = 0
        BEGIN = 20
        displayCount = BEGIN

        while True:
            time.sleep(0.1)
            charge = electric_charge()
            if charge > 0:
                if displayCount == 0:
                    print("EC:",charge,"EC/s:",generation,"mining=",mining,"converting=",converting)
                    if nextAlarm is not None:
                        print("Next alarm in %f seconds: %s"%(remainingBeforeAlarm,nextAlarm.name))
                    displayCount = BEGIN
                else:
                    displayCount -= 1

            generation = 0.0
            for panel in panels:
                generation += panel.energy_flow

            nextAlarm = self.nextAlarm()
            remainingBeforeAlarm = nextAlarm.time - self.m_space_center.ut

            if self.isFull() or remainingBeforeAlarm < 600:
                if self.isFull():
                    print("Fully fueled")
                else:
                    print("Next alarm in %fs: %s"%(remainingBeforeAlarm,nextAlarm.name))

                mining = self.stopMining()
                converting = self.stopConverting()
                self.changeSpeed(0)
                return 0
            if charge > max_charge - 100 and not mining:

                mining = self.startMining()
                converting = self.startConverting()
                self.changeSpeed(HIGH_SPEED)
            elif charge < 100 and mining:
                mining = self.stopMining()
                self.changeSpeed(HIGH_SPEED + 1)
                slept = 0
            elif not mining:
                slept += 1
                if slept < 40:
                    self.changeSpeed(HIGH_SPEED + 1)
                else:
                    self.changeSpeed(HIGH_SPEED)
            elif generation < 1 and converting:
                converting = self.stopConverting()
                self.changeSpeed(HIGH_SPEED)
            elif generation > 1 and not converting:
                converting = self.startConverting()
                self.changeSpeed(HIGH_SPEED)
            elif self.isOreFull() and not converting:
                converting = self.startConverting()
                self.changeSpeed(HIGH_SPEED)

        return 0

    def run(self):
        print(krpc.__version__)
        conn = krpc.connect(name='Miner2',address=self.__m_args.address) ## krpc.client.Client
        self.m_conn = conn
        self.m_alarmClock = conn.kerbal_alarm_clock

        print(conn.krpc.get_status().version)
        krpc_obj = conn.krpc
        space_center = conn.space_center
        self.m_space_center = space_center
        #~ print(dir(space_center.get_services()))
        #~ print(space_center.get_services().services)
        vessel = space_center.active_vessel
        self.m_vessel = vessel

        if vessel.situation != conn.space_center.VesselSituation.landed:
            print("Vessel not landed")
            return 1

        try:
            return self.mine()
        finally:
            self.m_space_center.rails_warp_factor = 0

    def changeSpeed(self, speed):
        oldSpeed = self.m_space_center.rails_warp_factor
        if self.m_space_center.rails_warp_factor != speed:
            self.m_space_center.rails_warp_factor = speed
        return oldSpeed

    def generateConverters(self):
        vessel = self.m_vessel
        for r in vessel.parts.resource_converters:
            for i in xrange(r.count):
                if r.name(i) in ("Oxidizer","LiquidFuel"):
                    yield (r,i)
                else:
                    print(r.name(i),r.outputs(i))



    def stopConverting(self):
        print("Stop Converting")
        originalSpeed = self.changeSpeed(0)
        for (r,i) in self.generateConverters():
            r.stop(i)
        self.changeSpeed(originalSpeed)
        return False

    def startConverting(self):
        print("Start Converting")
        originalSpeed = self.changeSpeed(0)
        for (r,i) in self.generateConverters():
            r.start(i)
        self.changeSpeed(originalSpeed)
        return True


    def startMining(self):
        vessel = self.m_vessel
        print("Starting Mining")
        originalSpeed = self.changeSpeed(0)
        for r in vessel.parts.resource_harvesters:
            r.depoyed = True
            r.active = True

        self.changeSpeed(originalSpeed)
        return True

    def stopMining(self):
        vessel = self.m_vessel
        print("Stop Mining")
        originalSpeed = self.changeSpeed(0)
        for r in vessel.parts.resource_harvesters:
            r.active = False

        self.changeSpeed(originalSpeed)
        return False


def main(argv):
    m = Miner2(argv)
    m.run()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
