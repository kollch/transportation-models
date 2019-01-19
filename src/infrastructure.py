
class Infrastructure():
    """Holds all of the intersections and roads"""
    def __init__(self, intersections, roads):
        self.intersections = intersections
        self.roads = roads

class Intersection():
    """May need connecting capabilities"""
    # roads_blocked = []
    # roads_open = []
    def __init__(self, intersections_id, roads, location):
        self.intersection_id = intersections_id
        self.roads = roads
        self.location = location

class Road():
    """Connect intersections together and vehicles drive on them"""
    # vehicles_on = []
    # speed_limit = 60
    def __init__(self, roads_id, two_way, lanes, ends):
        self.road_id = roads_id
        self.two_Way = two_way
        self.lanes = lanes
        self.ends = ends
