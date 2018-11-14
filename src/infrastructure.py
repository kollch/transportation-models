class Infrastructure():
    """Holds all of the intersections and roads"""
    def __init__(self, intersections=[], roads=[]):
        self.intersections = intersections
        self.roads = roads

class Intersection():
    """May need connecting capabilities"""
    roads_blocked = []
    roads_open = []
    def __init__(self, connecting_roads):
        self.connecting_roads = connecting_roads

class Road():
    """Connect intersections together and vehicles drive on them"""
    vehicles_on = []
    speed_limit = 60
