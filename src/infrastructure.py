"""This holds all of the transportation network infrastructure."""
import math


class Infrastructure():
    """Holds all of the intersections and roads"""
    def __init__(self, intersections, roads):
        self.intersections = intersections
        self.roads = roads

    def intersection_efficiency(self):
        """Determine how many vehicles have passed through all
        intersections so far
        """
        total = 0
        for intersection in self.intersections:
            total += intersection.vehicles_passed
        return total

    def avg_speed(self):
        """Determine the average speed of all vehicles at the moment"""
        total = 0
        vehicles = 0
        for road in self.roads:
            for vehicle in road.vehicles_on:
                total += vehicle.veloc[0]
            vehicles += len(road.vehicles_on)
        return total / vehicles


class Intersection():
    """May need connecting capabilities"""
    # roads_blocked = []
    # roads_open = []
    def __init__(self, intersection_id, roads, location):
        self.intersection_id = intersection_id
        self.roads = roads
        self.loc = location
        self.vehicles_on = []
        self.vehicles_passed = 0
        self.counter = 0

    def adjacent(self):
        """Gets intersections adjacent to the current one;
        Returns a list of tuples; each tuple has the intersection and
        the connecting road
        """
        results = []
        for road in self.roads:
            if road is None:
                continue
            for end in road.ends:
                if end is not self and hasattr(end, 'roads'):
                    # If end is an intersection and is not current one
                    results.append((end, road))
        return results

    def road_open(self, casenumber):
        """Create the list of road vehicles allowed to move on that direction.
        The corresponding value is: turn left, go straight, turn right.
        Each 10 frame, the intersection light will change.
        """
        self.counter += 1
        roads_list = [[], [], [], []]
        if currentf % 40 >= 1 and currentf % 40 <= 10:
            roads_list = [
                [False, True, True],
                [False, False, False],
                [False, True, True],
                [False, False, False]
            ]
        elif currentf % 40 >= 11 and currentf % 40 <= 20:
            roads_list = [
                [False, False, False],
                [False, True, True],
                [False, False, False],
                [False, True, True]
            ]
        elif currentf % 40 >= 21 and currentf % 40 <= 30:
            roads_list = [
                [True, False, False],
                [False, False, True],
                [True, False, False],
                [False, False, True]
            ]
        elif currentf % 40 >= 31 and currentf % 40 <= 40:
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
    def __init__(self, road_id, size, speed=60):
        """Parameters:
        road_id: Road ID
        size:    (two-way boolean, number of lanes, endpoints)
        speed:   speed limit
        """
        self.road_id = road_id
        self.two_way = size[0]
        self.lanes = size[1]
        self.ends = size[2]
        self.speed = speed
        self.length = None
        self.length = self.distance()
        self.vehicles_on = []

    def coords(self):
        """Get coordinates of the endpoints of the given road"""
        ends = []
        for i in range(2):
            try:
                ends.append(self.ends[i].loc)
            except AttributeError:
                ends.append(self.ends[i])
        return (ends[0], ends[1])

    def has_point(self, loc):
        """Check if a point is on the road"""
        ends = self.coords()
        for i in range(2):
            d_1 = abs(ends[1][i] - ends[0][i])
            d_2 = abs(ends[1][(i + 1) % 2] - ends[0][(i + 1) % 2])
            if (d_1 >= d_2
                    and (ends[0][i] < loc[i] and ends[1][i] < loc[i]
                         or ends[0][i] > loc[i] and ends[1][i] > loc[i])):
                return False
        d_x = ends[1][0] - ends[0][0]
        d_y = ends[1][1] - ends[0][1]
        calc_eq = d_y * (loc[0] - ends[0][0]) - d_x * (loc[1] - ends[0][1])
        dist = abs(calc_eq) / math.hypot(d_x, d_y)
        if dist <= self.lanes * 6:
            return True
        return False

    def lane_direction(self, loc):
        """Return the angle of the lane at the given location"""
        ends = self.coords()
        d_x = ends[1][0] - ends[0][0]
        d_y = ends[1][1] - ends[0][1]
        angle = math.atan2(d_y, d_x)
        calc_eq = d_y * (loc[0] - ends[0][0]) - d_x * (loc[1] - ends[0][1])
        signed_dist = calc_eq / math.hypot(d_x, d_y)
        if signed_dist < 0:
            angle = math.atan2(-d_y, -d_x)
        return math.degrees(angle)

    def distance(self):
        """Calculates the length of the road"""
        if self.length is not None:
            return self.length
        ends = self.coords()
        return math.hypot(ends[1][0] - ends[0][0], ends[1][1] - ends[0][1])
