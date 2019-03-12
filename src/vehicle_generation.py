import math
import json
import sys
import random

#this is currently entirely random and would require the user to specify an infrastructure so that vehicles can start
#on a road instead of a random place on the map

def read_road():
    """Select roads which are on the screen edges"""
    data = {}
    road = []
    road_end = []
    with open('data.json', 'r') as f:
        data = json.load(f)
    for item in data['roads']:
        #create start point coords
        try:
            if item['ends'][0]['x'] == 0:
                road.append([0,item['ends'][0]['y'] - 6])
            elif item['ends'][0]['x'] == 1600:
                road.append([1600,item['ends'][0]['y'] + 6])
            elif item['ends'][0]['y'] == 0:
                road.append([item['ends'][0]['x'] + 6,0])
            elif item['ends'][0]['y'] == 1600:
                road.append([item['ends'][0]['x'] - 6,1600])
        except TypeError:
            try:
                if item['ends'][1]['x'] == 0:
                    road.append([0,item['ends'][1]['y'] - 6])
                elif item['ends'][1]['x'] == 1600:
                    road.append([1600,item['ends'][1]['y'] + 6])
                elif item['ends'][1]['y'] == 0:
                    road.append([item['ends'][1]['x'] + 6,0])
                elif item['ends'][1]['y'] == 1600:
                    road.append([item['ends'][1]['x'] - 6,1600])
            except TypeError:
                continue

    for item in data['roads']:
        #create end points coords
        try:
            if item['ends'][0]['x'] == 0:
                road_end.append([0,item['ends'][0]['y']-6])
            elif item['ends'][0]['x'] == 1600:
                road_end.append([1600,item['ends'][0]['y']+6])
            elif item['ends'][0]['y'] == 0:
                road_end.append([item['ends'][0]['x']+6,0])
            elif item['ends'][0]['y'] == 1600:
                road_end.append([item['ends'][0]['x']-6,1600])
        except TypeError:
            try:
                if item['ends'][1]['x'] == 0:
                    road_end.append([0,item['ends'][1]['y']+6])
                elif item['ends'][1]['x'] == 1600:
                    road_end.append([1600,item['ends'][1]['y'] - 6])
                elif item['ends'][1]['y'] == 0:
                    road_end.append([item['ends'][1]['x'] - 6,0])
                elif item['ends'][1]['y'] == 1600:
                    road_end.append([item['ends'][1]['x'] + 6,1600])
            except TypeError:
                continue

    return (road, road_end)

#takes 1 parameter: number of vehicles through command line
def generated_vehicles(roads,roads_end):
    numVehicles = int(sys.argv[1])
    data = {}
    data = []
    for i in range(numVehicles):
        rand_start = random.randint(0,len(roads)-1)
        rand_type = random.randint(0,1)
        rand_end = random.randint(0,len(roads_end)-1)
        while rand_end == rand_start:
            rand_end = random.randint(0,len(roads_end)-1)
        data.append({
            'id': i,
            'start_loc': {
                'x': roads[rand_start][0],
                'y': roads[rand_start][1]
            },
            'type': rand_type,
            'end_loc': {
                'x': roads_end[rand_end][0],
                'y': roads_end[rand_end][1]
            },
            'entry_time': random.randint(0,5000)  # in milliseconds
        })

    with open('generated_vehicles.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)

if __name__== "__main__":
  roads = read_road()
  generated_vehicles(roads[0],roads[1])
