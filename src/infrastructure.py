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

    def road_open(self):
        """Create intersection roads list, true -- road open, false -- road close"""
        roads_list = [False, True, False, True]
        for i in range(4):
            if self.roads[i] is None:
                roads_list[i] = None
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
        self.length = None
        self.length = self.distance()

    def coords(self):
        """Get coordinates of the endpoints of the given road"""
        ends = []
        for i in range(2):
            try:
                ends.append(self.ends[i].location)
            except AttributeError:
                ends.append(self.ends[i])
        return (ends[0], ends[1])

    def has_point(self, loc):
        """Check if a point is on the road"""
        ends = self.coords()
        dx = ends[1][0] - ends[0][0]
        dy = ends[1][1] - ends[0][1]
        if (abs(dx) >= abs(dy)
                and (ends[0][0] < loc[0] and ends[1][0] < loc[0]
                or ends[0][0] > loc[0] and ends[1][0] > loc[0])
                or abs(dx) <= abs(dy)
                and (ends[0][1] < loc[1] and ends[1][1] < loc[1]
                or ends[0][1] > loc[1] and ends[1][1] > loc[1])):
            return False
        calc_eq = dy * (loc[0] - ends[0][0]) - dx * (loc[1] - ends[0][1])
        dist = abs(calc_eq) / math.hypot(dx, dy)
        if dist <= self.lanes * 6:
            return True
        return False

    def lane_direction(self, loc):
        """Return the angle of the lane at the given location"""
        ends = self.coords()
        dx = ends[1][0] - ends[0][0]
        dy = ends[1][1] - ends[0][1]
        angle = math.atan2(dy, dx)
        calc_eq = dy * (loc[0] - ends[0][0]) - dx * (loc[1] - ends[0][1])
        signed_dist = calc_eq / math.hypot(dx, dy)
        if signed_dist < 0:
            angle = math.atan2(-dy, -dx)
        return math.degrees(angle)

    def distance(self):
        """Calculates the length of the road"""
        if self.length is not None:
            return self.length
        ends = self.coords()
        return math.hypot(ends[1][0] - ends[0][0], ends[1][1] - ends[0][1])
