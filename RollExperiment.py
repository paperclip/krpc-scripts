#!/usr/bin/env python


from __future__ import print_function,division,absolute_import,unicode_literals

import krpc
import sys
import time

def run():
	conn = krpc.connect(name='Roll Control') ## krpc.client.Client
	space_center = conn.space_center
	vessel = space_center.active_vessel
	
	orbit_flight = vessel.flight(vessel.orbital_reference_frame)
	vessel_control = vessel.control
	
	
	auto_pilot = vessel.auto_pilot
	auto_pilot.engage()
	
	control = vessel.control
	nodes = control.nodes
	if len(nodes) == 0:
		print("No nodes to execute")
		
	node = nodes[0]
	auto_pilot.reference_frame = node.reference_frame
	auto_pilot.target_direction = node.remaining_burn_vector(auto_pilot.reference_frame)
	print("Direction=",auto_pilot.target_direction)
	
	auto_pilot.target_roll = 90.0
	
	node_flight = vessel.flight(node.reference_frame)
	#~ 
	#~ def currentRoll():
		#~ print("A:",target_roll-auto_pilot.roll_error)
		#~ print("B:",target_roll+auto_pilot.roll_error)
		#~ print("C:",vessel.rotation(auto_pilot.reference_frame))
		#~ print("D:",vessel.direction(auto_pilot.reference_frame))
		#~ print("E:",node_flight.roll())
		#~ 
		#~ return auto_pilot.target_roll-auto_pilot.roll_error
	
	while True:
		print("A:",auto_pilot.target_roll-auto_pilot.roll_error)
		print("B:",auto_pilot.target_roll+auto_pilot.roll_error)
		print("C:",vessel.rotation(auto_pilot.reference_frame))
		print("D:",vessel.direction(auto_pilot.reference_frame))
		print("E:",node_flight.roll)
		
		print("target_roll=",auto_pilot.target_roll)
		print("Roll Error=",auto_pilot.roll_error)
		time.sleep(5)

		#~ print("Current Roll=",orbit_roll)
		#~ print("Need to rolling to",best_roll)
		#~ 
		#~ diff = best_roll - orbit_roll
		#~ print("Diff1:",diff)
		#~ if diff > 180:
			#~ diff -= 180
		#~ if diff < -180:
			#~ diff += 180
			#~ 
		#~ print("Diff2:",diff)
		
		#~ if diff < 0:
			#~ vessel_control.roll = 0.1
		#~ else:
			#~ vessel_control.roll = -0.1
			
		
		#~ vessel_control.roll = -0.01

def main(argv):
	"""
	Control the roll of a craft under ion acceleration to maximise power
	"""
	return run()

if __name__ == "__main__":
	sys.exit(main(sys.argv))
