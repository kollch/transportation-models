import math
import json
import sys
import random

#this is currently entirely random and would require the user to specify an infrastructure so that vehicles can start
#on a road instead of a random place on the map

#takes 1 parameter: number of vehicles through command line

numVehicles = int(sys.argv[1])
data = {}
data['vehicles'] = []
for i in range(numVehicles):
    data['vehicles'].append({
        'id': i,
        'start_loc': {
            'x': random.randint(0, 2000),
            'y': random.randint(0,2000)
        },
        'entry_time': random.randint(0,5000)  # in milliseconds
    })

with open('generated_vehicles.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)
