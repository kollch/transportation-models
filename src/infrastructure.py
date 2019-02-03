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


class Road():
    """Connect intersections together and vehicles drive on them"""
    # vehicles_on = []
    # speed_limit = 60
    def __init__(self, road_id, two_way, lanes, ends, intersections, roads):
        self.road_id = road_id
        self.two_way = two_way
        self.lanes = lanes
        self.ends = ends
        self.intersections = intersections
        self.roads = roads

    def distance(self, road_id):
        """initialize the start point and end point for x and y."""
        x_1 = 0
        x_2 = 0
        y_1 = 0
        y_2 = 0
        """check which interesction connect with road"""
        # road_connection_id = 0

        for i in roads:
            if road_id == self.roads['id']:
                if type(self.roads.ends[0]) == int:
                    road_intersection_id = self.roads.ends[0]
                    for j in intersections:
                        if road_intersection_id == self.intersections['id']:
                            x_1 = self.intersections['loc']['x']
                            y_1 = self.intersections['loc']['y']
                else:
                    x_1 = self.roads.ends[0][0]
                    y_1 = self.roads.ends[0][1]
                if type(self.roads.ends[1]) == int:
                    road_intersection_id = self.roads.ends[1]
                    for j in intersections:
                        if road_intersection_id == self.intersection['id']:
                            x_2 = self.intersections['loc']['x']
                            y_2 = self.intersections['loc']['y']
                else:
                    x_2 = self.roads.ends[1][0]
                    y_2 = self.roads.ends[1][1]
        """calculate distance"""
        dis = math.sqrt((x_1 - x_2) ** 2 + (y_1 - y_2) ** 2)
        return dis
