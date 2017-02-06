
from __future__ import print_function,division,absolute_import,unicode_literals

import krpc
import sys
import time

def main(argv):
    conn = krpc.connect(name='Scan Control') ## krpc.client.Client
    space_center = conn.krpc
    print(dir(space_center.get_services()))
    print(space_center.get_services().services)
    vessel = space_center.active_vessel
    
    resources = vessel.resources
    print(resources.names)
    print(resources.amount(b"ElectricCharge"))
    electric_charge = conn.add_stream(resources.amount,b"ElectricCharge")
    
    root = vessel.parts.root
    stack = [(root, 0)]
    while len(stack) > 0:
        part,depth = stack.pop()
        print(' '*depth, part.title)
        for child in part.children:
            stack.append((child, depth+1))
            
    
    
    scanning = False
    
    return 0
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))
