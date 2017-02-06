#!/usr/bin/env python


from __future__ import print_function,division,absolute_import,unicode_literals

import krpc
import sys
import time

def getGeneration(vessel):
	panels = vessel.parts.solar_panels
	generation = 0.0
	for panel in panels:
		generation += panel.energy_flow
	return generation
	
def setTargetDirectionFromNode(auto_pilot,node):
	auto_pilot.target_direction = node.remaining_burn_vector(auto_pilot.reference_frame)
	

def main(argv):
	"""
	Execute a node, maximise power by roll while doing so.
	"""
	conn = krpc.connect(name='Node Execute') ## krpc.client.Client
	space_center = conn.space_center
	space_center.rails_warp_factor = 0
	vessel = space_center.active_vessel
	#~ 
	#~ resources = vessel.resources
	#~ print(resources.names)
	#~ print(resources.amount(b"ElectricCharge"))
	#~ electric_charge = conn.add_stream(resources.amount,b"ElectricCharge")
	
	control = vessel.control
	#~ 
	#~ bodies = space_center.bodies
	#~ sun = bodies[b'Sun']
	
	orbit_flight = vessel.flight(vessel.orbital_reference_frame)
	
	results = {}
	auto_pilot = vessel.auto_pilot
	auto_pilot.engage()
	#~ auto_pilot.sas = True	
	
	nodes = control.nodes
	if "--pro" in argv:
		auto_pilot.reference_frame = vessel.orbital_reference_frame
		node_flight = orbit_flight
		def setTargetDirection():
			auto_pilot.target_direction = (0,1,0)
			
		def shouldContinue():
			return True
			
	elif len(nodes) == 0:
		print("No nodes to execute")
		return 1
	else:
		node = nodes[0]
		auto_pilot.reference_frame = node.reference_frame
		node_flight = vessel.flight(node.reference_frame)
		def setTargetDirection():
			setTargetDirectionFromNode(auto_pilot,node)
			
		def shouldContinue():
			return node.remaining_delta_v > 0.1
			
	setTargetDirection()
	
	results = {}
	
	def currentRoll():
		return node_flight.roll
	
	target_roll = 0.0
	while len(results) < 30:
		auto_pilot.target_roll = target_roll
		time.sleep(1)
		
		generation = getGeneration(vessel)
		roll = currentRoll()
		
		print(generation,"EC/s at roll=",roll)
		results[roll] = generation
		target_roll += 10
		
	best_roll = 0.0
	best_generation = 0.0
	for (roll,generation) in results.iteritems():
		if generation > best_generation:
			best_roll = roll
			best_generation = generation
			
	print("Best roll is",best_roll,"at",best_generation,"EC/s")
	auto_pilot.target_roll = best_roll
	
	while shouldContinue():		
		setTargetDirection()
		
		roll = currentRoll()
		generation = getGeneration(vessel)
		
		if generation > best_generation:
			best_roll = roll
			best_generation = generation
			print("Updating best roll is",best_roll,"at",best_generation,"EC/s")
			auto_pilot.target_roll = best_roll
			
		#~ rotation = vessel.rotation(ref_frame)
		#~ print("Rotation=",rotation)
		#~ 
		#~ rollControl = control.roll
		#~ print("Roll control=",rollControl)
		
		time.sleep(1)
		
	control.throttle = 0.0
	auto_pilot.disengage()

	return 0

if __name__ == "__main__":
	sys.exit(main(sys.argv))
