#!/usr/bin/env python


from __future__ import print_function,division,absolute_import,unicode_literals

import krpc
import sys
import time
import math

def getGeneration(vessel):
    panels = vessel.parts.solar_panels
    generation = 0.0
    for panel in panels:
        generation += panel.energy_flow
    return generation

class ExecutionInformation(object):
    def __init__(self, vessel):
        self.m_vessel = vessel

        auto_pilot = vessel.auto_pilot
        auto_pilot.engage()
        self.m_auto_pilot = auto_pilot
        self.m_node_flight = None

    def vessel(self):
        return self.m_vessel

    def currentRoll(self):
        return self.m_node_flight.roll

    def roll(self, targetRoll=None):
        if targetRoll is not None:
            self.m_auto_pilot.target_roll = targetRoll
        return self.currentRoll()

    def getGeneration(self):
        return getGeneration(self.m_vessel)

    def getSolarCount(self):
        return len(self.m_vessel.parts.solar_panels)

    def hasSolarPanels(self):
        return self.getSolarCount() > 0

    def hasIonDrive(self):
        engines = self.m_vessel.parts.engines
        for engine in engines:
            if not engine.active:
                continue
            if u'ElectricCharge' in engine.propellant_names:
                return True
        return False

    def disengage_auto_pilot(self):
        self.m_auto_pilot.disengage()


SCREEN_RESOLUTION_WIDTH = 1800
SCREEN_RESOLUTION_HEIGHT = 1052

class NodeInformation(ExecutionInformation):
    def __init__(self, vessel, space_center):
        super(NodeInformation,self).__init__(vessel)

        self.m_space_center = space_center

        control = vessel.control
        nodes = control.nodes
        assert(len(nodes) > 0)
        node = nodes[0]
        self.m_auto_pilot.reference_frame = node.reference_frame
        self.m_node_flight = vessel.flight(node.reference_frame)
        self.__m_node = node
        self.__m_previousRemainingDeltaV = self.__m_node.remaining_delta_v + 1

    def __calcuateBurnTime(self):
        vessel = self.m_vessel
        # Calculate burn time (using rocket equation)
        delta_v = self.__m_node.remaining_delta_v
        F = vessel.available_thrust
        Isp = vessel.specific_impulse * 9.82
        m0 = vessel.mass
        m1 = m0 / math.exp(delta_v/Isp)
        flow_rate = F / Isp
        burn_time = (m0 - m1) / flow_rate
        return burn_time

    def waitTillBurnStart(self):
        burn_time = self.__calcuateBurnTime()

        # Wait until burn
        print('Waiting until burn')
        print(self.m_space_center.ut,self.__m_node.ut,burn_time)
        burn_ut = self.__m_node.ut - (burn_time/2.)
        lead_time = 5
        print("Warping to",burn_ut - lead_time)
        self.m_space_center.warp_to(burn_ut - lead_time)
        print("Busy waiting for burn time")
        while self.m_space_center.ut - burn_ut > 0:
            time.sleep(0.01)

    def setTargetDirection(self):
        self.m_auto_pilot.target_direction = self.__m_node.remaining_burn_vector(self.m_auto_pilot.reference_frame)
        self.m_auto_pilot.wait()

    def shouldContinue(self):
        print("Checking remaining delta_v:",self.__m_node.remaining_delta_v,"@",self.m_space_center.warp_rate)

        if self.__m_node.remaining_delta_v > self.__m_previousRemainingDeltaV:
            return False

        self.__m_previousRemainingDeltaV = self.__m_node.remaining_delta_v

        if self.__m_node.remaining_delta_v < 0.09:
            return False
        elif self.__m_node.remaining_delta_v < 1:
            self.m_vessel.control.throttle = 0.5

        return True

    def burnSleepTime(self):
        burn_time = max(0.1,self.__calcuateBurnTime())
        return burn_time/(8.0)  ## *self.m_space_center.warp_rate)

class ProgradeInformation(ExecutionInformation):
    def __init__(self, vessel):
        super(ProgradeInformation,self).__init__(vessel)
        self.m_auto_pilot.reference_frame = vessel.orbital_reference_frame
        self.m_node_flight = vessel.flight(vessel.orbital_reference_frame)

    def waitTillBurnStart(self):
        pass

    def setTargetDirection(self):
        self.m_auto_pilot.target_direction = (0,1,0)

    def shouldContinue(self):
        return True

    def burnSleepTime(self):
        return 10

class RollHandler(object):
    def __init__(self):
        self.m_results = {}
        self.m_best_generation = 0.0
        self.m_best_roll = 0.0

    def setInfo(self, info):
        self.m_info = info

    def setBestRoll(self):
        roll = self.m_info.currentRoll()
        generation = self.m_info.getGeneration()

        if generation > self.m_best_generation:
            self.m_best_roll = roll
            self.m_best_generation = generation
            print("Updating best roll is",self.m_best_roll,"at",self.m_best_generation,"EC/s")

        self.m_info.roll(self.m_best_roll)

        #~ rotation = vessel.rotation(ref_frame)
        #~ print("Rotation=",rotation)
        #~
        #~ rollControl = control.roll
        #~ print("Roll control=",rollControl)

    def investigateBestRoll(self):
        info = self.m_info

        if not self.m_info.hasSolarPanels():
            print("No generation - skipping roll checks")
            return

        if not self.m_info.hasIonDrive():
            print("No ion drive - skipping roll checks")
            return

        def currentRoll():
            return info.roll()

        target_roll = 0.0
        while len(self.m_results) < 30:
            info.roll(target_roll)
            time.sleep(1)

            generation = self.m_info.getGeneration()
            roll = self.m_info.roll()

            print(generation,"EC/s at roll=",roll)
            self.m_results[roll] = generation
            target_roll += 10

        best_roll = 0.0
        best_generation = 0.0
        for (roll,generation) in self.m_results.iteritems():
            if generation > best_generation:
                best_roll = roll
                best_generation = generation

        print("Best roll is",best_roll,"at",best_generation,"EC/s")
        info.roll(best_roll)

        self.m_best_generation = best_generation
        self.m_best_roll = best_roll

def executeInfo(conn, vessel, info, roller=None):
    space_center = conn.space_center
    control = vessel.control

    info.setTargetDirection()
    if roller is None:
        roller = RollHandler()

    roller.setInfo(info)
    roller.investigateBestRoll()

    info.waitTillBurnStart()
    print("Starting burn")
    control.throttle = 1.0
    try:
        space_center.physics_warp_factor = 3

        while info.shouldContinue():
            info.setTargetDirection()
            roller.setBestRoll()

            sleepTime = info.burnSleepTime()
            if sleepTime < 3:
                space_center.physics_warp_factor = 0

            time.sleep(sleepTime)
    finally:
        print("Finishing burn")
        control.throttle = 0.0
        space_center.rails_warp_factor = 0
        space_center.physics_warp_factor = 0
        info.disengage_auto_pilot()

    return 0

def executeNextNode(conn, roller=None):
    space_center = conn.space_center
    vessel = space_center.active_vessel
    info = NodeInformation(vessel, space_center)
    return executeInfo(conn, vessel, info, roller)

def main(argv):
    """
    Execute a node, maximise power by roll while doing so.


    #~
    #~ resources = vessel.resources
    #~ print(resources.names)
    #~ print(resources.amount(b"ElectricCharge"))
    #~ electric_charge = conn.add_stream(resources.amount,b"ElectricCharge")
    #~
    #~ bodies = space_center.bodies
    #~ sun = bodies[b'Sun']
    """
    conn = krpc.connect(name='Node Execute') ## krpc.client.Client
    space_center = conn.space_center
    space_center.rails_warp_factor = 0
    vessel = space_center.active_vessel


    control = vessel.control
    nodes = control.nodes
    if "--pro" in argv:
        info = ProgradeInformation(vessel)
    elif len(nodes) == 0:
        print("No nodes to execute")
        return 1
    else:
        info = NodeInformation(vessel, space_center)

    return executeInfo(conn, vessel, info)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
