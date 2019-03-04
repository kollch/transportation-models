import math

class Infrastructure():
    """Holds all of the intersections and roads"""
    def __init__(self, intersections, roads):
        self.intersections = intersections
        self.roads = roads


class Intersection():
    """May need connecting capabilities"""
    # roads_blocked = []
    # roads_open = []
    def __init__(self, intersection_id, roads, location):
        self.intersection_id = intersection_id
        self.roads = roads
        self.location = location
    
    
    def road_open(self, casenumber):
        """
        Create the list of road vehicles allowed to move on that direction.
        The cooresponding value is: turn left, go straight, turn right.
        """
        roads_list = [[], [], [], []]

        if casenumber == 1:
            roads_list = [
                    [False, True, True],
                    [False, False, False],
                    [False, True, True],
                    [False, False, False]
                    ]
        elif casenumber == 2:
            roads_list = [
                    [False, False, False],
                    [False, True, True],
                    [False, False, False],
                    [False, True, True]
                    ]
        elif casenumber == 3:
            roads_list = [
                    [True, False, False],
                    [False, False, True],
                    [True, False, False],
                    [False, False, True]
                    ] 
        elif casenumber == 4:
            roads_list = [
                    [False, True, True],
                    [False, False, False],
                    [False, True, True],
                    [False, False, False]
                    ]

        for i in range(4):
            if self.roads[i] is None:
                roads_list[i] = [None, None, None]
        return roads_list
        
class Road():
    """Connect intersections together and vehicles drive on them"""
    # vehicles_on = []
    # speed_limit = 60
    def __init__(self, road_id, two_way, lanes, ends):
        self.road_id = road_id
        self.two_way = two_way
        self.lanes = lanes
        self.ends = ends
        self.length = self.distance()

    def distance(self):
        """Calculates the length of the road"""
        locs = [[0, 0], [0, 0]]
        for i in range(2):
            for j in range(2):
                try:
                    locs[i][j] = self.ends[i][j]
                except TypeError:
                    locs[i][j] = self.ends[i].location[j]
        return math.sqrt((locs[1][0] - locs[0][0]) ** 2
                         + (locs[1][1] - locs[0][1]) ** 2)
