import math
import json
import sys
import random

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
