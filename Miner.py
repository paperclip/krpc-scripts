#!/usr/bin/env python

from __future__ import print_function,division,absolute_import,unicode_literals

import krpc
import sys
import time
NIGHT_TIMER=10

def main(argv):
	if len(argv) > 1:
		actionGroup = int(argv[1])
	else:
		actionGroup = 2
	
	conn = krpc.connect(name='Mine Control') ## krpc.client.Client
	space_center = conn.space_center
	vessel = space_center.active_vessel
	#~ print(vessel.name)
	#~ print(vessel.situation)
	#~ print(dir(vessel))
	#~ print(dir(krpc))
	#~ print(dir(conn.space_center))
	if vessel.situation != conn.space_center.VesselSituation.landed:
		print("Vessel not landed")
		return 1
		
	panels = vessel.parts.solar_panels
	print(panels)
	
	resources = vessel.resources
	print(resources.names)
	print(resources.amount(b"ElectricCharge"))
	electric_charge = conn.add_stream(resources.amount,b"ElectricCharge")
	
	mining = False
	nighttime=0
	
	while True:
		time.sleep(1)
		charge = electric_charge()
		print("EC:",charge)

		generation = 0.0
		for panel in panels:
			generation += panel.energy_flow
		print("EC/s:",generation)
			
		powered = charge > 0.0 or generation > 0.0
					
		if powered and not mining:
			space_center.rails_warp_factor = 0
			vessel.control.toggle_action_group(actionGroup) ## Action group to start mining
			mining = True
			space_center.rails_warp_factor = 5
		elif mining and not powered:
			mining = False
			
		if powered:
			if nighttime > 0:
				print("Night-time lasted %d seconds"%(nighttime))
			nighttime=0
		else:
			nighttime += 1
			if nighttime >= 7:
				space_center.rails_warp_factor = 5
			else:
				space_center.rails_warp_factor = 6
				
			
	return 0
	
if __name__ == "__main__":
	sys.exit(main(sys.argv))
