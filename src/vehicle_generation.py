"""Generates a JSON file of randomly generated vehicles."""

import math
import json
import sys
import random


def get_roads(data):
    """Find roads which connect with the edge of the canvas"""
    roads = []
    for road in data['roads']:
        for end in road['ends']:
            if not isinstance(end, int):
                # The road hits an edge, so add to results and move on to the
                # next road
                roads.append(road['ends'])
                break
    return roads


def coords(data, road):
    """Get coordinates of the endpoints of the given road"""
    ends = []
    for i in range(2):
        try:
            ends.append((road[i]['x'], road[i]['y']))
        except TypeError:
            for intersection in data['intersections']:
                if intersection['id'] == road[i]:
                    inter_coords = intersection['loc']
                    ends.append((inter_coords['x'], inter_coords['y']))
                    break
    return (ends[0], ends[1])


def io_coords(data):
    """Get coordinate points for the starting location of vehicles"""
    inputs = []
    outputs = []
    roads = get_roads(data)
    for road in roads:
        road_coords = coords(data, road)
        d_y = road_coords[1][1] - road_coords[0][1]
        d_x = road_coords[1][0] - road_coords[0][0]
        angle = math.atan2(d_y, d_x)
        vertical = False
        # Which end of the road is on the edge of the canvas
        canvas_edge = 1
        if abs(math.degrees(angle)) > 45 and abs(math.degrees(angle)) < 135:
            offset = (int(round(6 / math.sin(angle))), 0)
            vertical = True
        else:
            offset = (0, int(round(6 / math.cos(angle))))
        try:
            end = (road[0]['x'], road[0]['y'])
        except TypeError:
            end = (road[1]['x'], road[1]['y'])
            canvas_edge = 2
        if canvas_edge == 1 and not vertical or canvas_edge == 2 and vertical:
            inputs.append((end[0] - offset[0], end[1] - offset[1]))
            outputs.append((end[0] + offset[0], end[1] + offset[1]))
        else:
            inputs.append((end[0] + offset[0], end[1] + offset[1]))
            outputs.append((end[0] - offset[0], end[1] - offset[1]))
    return (inputs, outputs)


def main(argv):
    """The main function of the program."""
    if len(argv) != 4:
        print("Wrong number of arguments!")
        errmsg = "Usage: python3 " + argv[0]
        errmsg += " <infrastructure file name> <# of vehicles> <% CAVS>"
        sys.exit(errmsg)

    with open(argv[1], 'r') as infrastructure_file:
        infrastructure = json.load(infrastructure_file)
    num_vehicles = int(argv[2])
    num_cavs = int(round(num_vehicles * int(argv[3]) / 100))

    points = io_coords(infrastructure)

    data = []
    for i in range(1, num_vehicles + 1):
        start_loc_index = random.randrange(len(points[0]))
        end_loc_index = random.randrange(len(points[1]))
        while end_loc_index == start_loc_index:
            end_loc_index = random.randrange(len(points[1]))
        start_loc = points[0][start_loc_index]
        end_loc = points[1][end_loc_index]
        # 1 is autonomous, 0 is non-autonomous
        vehicle_type = 1
        if i > num_cavs:
            vehicle_type = 0
        # Each frame is 100 ms
        entry_time = random.randrange(100) * 100
        data.append({
            'id': i,
            'start_loc': {
                'x': start_loc[0],
                'y': start_loc[1]
            },
            'type': vehicle_type,
            'end_loc': {
                'x': end_loc[0],
                'y': end_loc[1]
            },
            'entry_time': entry_time
        })
    with open('vehicle_layout.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)

main(sys.argv)
