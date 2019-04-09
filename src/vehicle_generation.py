"""Generates a JSON file of randomly generated vehicles."""

import math
import json
import sys
import random


def init_roads(data):
    """Initialize roads"""
    roads = []
    for item in data['roads']:
        ends = [item['ends'][0], item['ends'][1]]
        # Convert road endpoints to tuples if they're coordinates
        for i in range(2):
            try:
                ends[i] = (ends[i]['x'], ends[i]['y'])
            except TypeError:
                for intersection in data['intersections']:
                    if intersection['id'] == ends[i]:
                        ends[i] = intersection
                        break
        roads.append((ends[0], ends[1]))
    return roads


def init_ends(roads):
    """Initialize endpoints"""
    ends = []
    useful_ends = []
    for i in range(len(roads)):
        ends.append([])
        for j in range(2):
            try:
                ends[i].append((roads[i][j]['loc']['x'],
                                roads[i][j]['loc']['y']))
            except TypeError:
                ends[i].append((roads[i][j][0], roads[i][j][1]))
    for end in ends:
        for i in range(2):
            for j in range(2):
                if end[i][j] == 0 or end[i][j] == 1600:
                    useful_ends.append(end)
                    break
            else:
                continue
            break
    return useful_ends


def lane_direction(roads_ends):
    """Find the angle of a lane"""
    angles = []
    for road_end in roads_ends:
        d_x = road_end[0][0] - road_end[1][0]
        d_y = road_end[0][1] - road_end[1][1]
        angles.append(abs(math.atan2(d_y, d_x)))
    return angles


def edge_ends(roads_ends):
    """Find endpoints of the road"""
    edge_endpoints = []
    for item in roads_ends:
        for i in range(2):
            for j in range(2):
                if item[i][j] == 0 or item[i][j] == 1600:
                    edge_endpoints.append(item[i])
                    break
    return edge_endpoints


def read_road():
    """Select roads which are on the screen edges"""
    road = []
    road_end = []
    center_dist = []
    with open('data.json', 'r') as infrastructure_file:
        data = json.load(infrastructure_file)

    all_roads = init_roads(data)
    roads_ends = init_ends(all_roads)
    edge = edge_ends(roads_ends)
    angles = lane_direction(roads_ends)
    for i in range(len(roads_ends)):
        if math.degrees(angles[i]) < 45 or math.degrees(angles[i]) > 135:
            try:
                center_dist.append(abs((12 / math.cos(angles[i])) / 2))
            except ZeroDivisionError:
                center_dist.append(6)
        else:
            try:
                center_dist.append(abs((12 / math.sin(angles[i])) / 2))
            except ZeroDivisionError:
                center_dist.append(6)

    for i in range(len(roads_ends)):
        if edge[i][0] == 0:
            road.append([0, edge[i][1] - center_dist[i]])
        elif edge[i][0] == 1600:
            road.append([1600, edge[i][1] + center_dist[i]])
        elif edge[i][1] == 0:
            road.append([edge[i][0] + center_dist[i], 0])
        elif edge[i][1] == 1600:
            road.append([edge[i][0] - center_dist[i], 1600])

    for i in range(len(roads_ends)):
        if edge[i][0] == 0:
            road_end.append([0, edge[i][1] + center_dist[i]])
        elif edge[i][0] == 1600:
            road_end.append([1600, edge[i][1] - center_dist[i]])
        elif edge[i][1] == 0:
            road_end.append([edge[i][0] - center_dist[i], 0])
        elif edge[i][1] == 1600:
            road_end.append([edge[i][0] + center_dist[i], 1600])
    return (road, road_end)


# Takes 1 parameter: number of vehicles through command line
def generated_vehicles(roads, roads_end):
    """Generates vehicles"""
    num_vehicles = int(sys.argv[1])
    data = []
    for i in range(num_vehicles):
        rand_start = random.randint(0, len(roads) - 1)
        rand_type = random.randint(0, 1)
        rand_end = random.randint(0, len(roads_end) - 1)
        while rand_end == rand_start:
            rand_end = random.randint(0, len(roads_end) - 1)
        data.append({
            'id': i,
            'start_loc': {
                'x': math.floor(roads[rand_start][0]),
                'y': math.floor(roads[rand_start][1])
            },
            'type': rand_type,
            'end_loc': {
                'x': math.floor(roads_end[rand_end][0]),
                'y': math.floor(roads_end[rand_end][1])
            },
            'entry_time': random.randint(0, 50) * 100  # in milliseconds
        })

    with open('generated_vehicles.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)


if __name__ == "__main__":
    ROAD_LIST = read_road()
    generated_vehicles(ROAD_LIST[0], ROAD_LIST[1])
