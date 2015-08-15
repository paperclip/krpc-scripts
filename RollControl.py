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
	

def main(argv):
	"""
	Control the roll of a craft under ion acceleration to maximise power
	"""
	conn = krpc.connect(name='Roll Control') ## krpc.client.Client
	space_center = conn.space_center
	vessel = space_center.active_vessel
	#~ 
	#~ resources = vessel.resources
	#~ print(resources.names)
	#~ print(resources.amount(b"ElectricCharge"))
	#~ electric_charge = conn.add_stream(resources.amount,b"ElectricCharge")
	
	vessel_control = vessel.control
	
	bodies = space_center.bodies
	sun = bodies[b'Sun']
	
	sun_flight = vessel.flight(sun.reference_frame)
	orbit_flight = vessel.flight(vessel.orbital_reference_frame)
	
	results = {}
	
	while len(results) < 5:
		
		generation = getGeneration(vessel)
		print("EC/s:",generation)
		#~ roll = vessel_control.roll
		#~ print("Roll:",roll)
		
		#~ sun_direction = sun_flight.direction
		#~ print("Sun direction:",sun_direction)
		
		#~ orbit_direction = orbit_flight.direction
		#~ print("Orbit direction:",orbit_direction)
		#~ 
		orbit_roll = orbit_flight.roll
		print("Orbit roll:",orbit_roll)
		
		results[orbit_roll] = generation
		
		#~ target_roll = auto_pilot.target_roll
		#~ print("Target roll:",target_roll)
		
		time.sleep(0.5)
		
	best_roll = 0.0
	best_generation = 0.0
	for (roll,generation) in results.iteritems():
		if generation > best_generation:
			best_roll = roll
			best_generation = generation
			
	print("Best roll is",best_roll,"at",best_generation,"EC/s")
	
	#~ auto_pilot = vessel.auto_pilot
	#~ auto_pilot.engage()
	#~ auto_pilot.sas = True	
	while True:
		orbit_roll = orbit_flight.roll
		generation = getGeneration(vessel)
		
		if generation > best_generation:
			best_roll = orbit_roll
			best_generation = generation
			print("Updating best roll is",best_roll,"at",best_generation,"EC/s")
		
		#~ auto_pilot.target_roll = best_roll
		
		print("Current Roll=",orbit_roll)
		print("Need to rolling to",best_roll)
		
		diff = best_roll - orbit_roll
		if diff > 180:
			diff -= 180
		if diff < -180:
			diff += 180
			
		print("Diff:",diff)
		
		if diff < 0:
			vessel_control.roll = 0.1
		else:
			vessel_control.roll = -0.1
			
		
		#~ print("target_roll=",auto_pilot.target_roll)
		#~ print("Roll Error=",auto_pilot.roll_error)
		time.sleep(5)

	return 0

if __name__ == "__main__":
	sys.exit(main(sys.argv))
