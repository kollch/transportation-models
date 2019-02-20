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

    def coords(self):
        """Get coordinates of the endpoints of the given road"""
        ends = []
        for i in range(2):
            try:
                ends.append(self.ends[i].location)
            except TypeError:
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
        locs = [[0, 0], [0, 0]]
        for i in range(2):
            for j in range(2):
                try:
                    locs[i][j] = self.ends[i][j]
                except TypeError:
                    locs[i][j] = self.ends[i].location[j]
        return math.sqrt((locs[1][0] - locs[0][0]) ** 2
                         + (locs[1][1] - locs[0][1]) ** 2)
