import math
import json
import sys
import random

#this is currently entirely random and would require the user to specify an infrastructure so that vehicles can start
#on a road instead of a random place on the map

#takes 1 parameter: number of vehicles through command line

numVehicles = int(sys.argv[1])
infrastructure_file = sys.argv[2]
root = json.load(open(infrastructure_file))
arr = root["intersections"]
int_res = [(e["loc"]["x"], e["loc"]["y"]) for e in arr]

arr = root["roads"]
road_res = [(e["ends"]["x"], e["ends"]["y"]) for e in arr]

res = int_res + road_res

data = {}

data['vehicles'] = []
for i in range(numVehicles):
    # pick a random location in the res list
    idx = random.randint(0, len(res)-1)
    print(idx)
    data['vehicles'].append({
        'id': i,
        'start_loc': {
            'x': res[idx][0],
            'y': res[idx][1]
        },
        'entry_time': random.randint(0, 5000)  # in milliseconds
    })

with open('generated_vehicles.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)
