#!/usr/bin/env python
from __future__ import print_function,division,absolute_import,unicode_literals

import krpc
import sys
import time
import math

import NodeExecute

def calcuateBurnTime(vessel, node):
    # Calculate burn time (using rocket equation)
    delta_v = node.remaining_delta_v

    F = vessel.available_thrust
    Isp = vessel.specific_impulse * 9.82
    flow_rate = F / Isp

    m0 = vessel.mass
    m1 = m0 / math.exp(delta_v/Isp)

    burn_time = (m0 - m1) / flow_rate
    return burn_time

def calculateDeltaV(vessel, burn_time):

    F = vessel.available_thrust
    Isp = vessel.specific_impulse * 9.82
    flow_rate = F / Isp

    m0 = vessel.mass
    m1 = m0 - burn_time * flow_rate
    delta_v = Isp * math.log(m0 / m1)
    return delta_v

def addKick(conn, burn_duration=120):

    space_center = conn.space_center
    space_center.rails_warp_factor = 0
    vessel = space_center.active_vessel
    control = vessel.control
    orbit_flight = vessel.flight(vessel.orbital_reference_frame)

    ## Find periapsis
    orbit = vessel.orbit
    time_to_periapsis = orbit.time_to_periapsis

    ## Add node
    node = control.add_node(space_center.ut + time_to_periapsis, calculateDeltaV(vessel, burn_duration), 0, 0)

    ## Tune delta-v - 2 minutes burn time

    return node


def main(argv):
    """
    """
    conn = krpc.connect(name='Add Kick') ## krpc.client.Client
    space_center = conn.space_center
    vessel = space_center.active_vessel
    orbit = vessel.orbit

    count = 1
    if len(argv) > 1:
        count = int(argv[1])

    while count > 0:
        node = addKick(conn, 120)

        ## Execute node
        NodeExecute.executeNextNode(conn)

        node.remove()

        count -= 1

        if orbit.next_orbit is not None:
            print("Leaving orbit!")
            break

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
