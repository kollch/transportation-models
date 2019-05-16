"""This holds all of the transportation network infrastructure."""
import math


class Infrastructure():
    """Holds all of the intersections and roads"""
    def __init__(self, intersections, roads):
        self.intersections = intersections
        self.roads = roads

    def closest_intersection(self, pos):
        """Returns the intersection that is closest to the given
        location
        """
        min_distance = None
        nearest = None
        for intersection in self.intersections:
            loc = intersection.loc
            distance = math.hypot(loc[0] - pos[0], loc[1] - pos[1])

            if min_distance is None or min_distance > distance:
                nearest = intersection
                min_distance = distance
        return nearest

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

    def road_at(self, loc):
        """Find the road at the given location;
        return None if there aren't any
        """
        for road in self.roads:
            if road.has_point(loc):
                return road
        return None

    def road_from_id(self, rid):
        """Get road from passed in road id"""
        for road in self.roads:
            if rid == road.road_id:
                return road
        return None


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
        self.roads_list = [[], [], [], []]

    def __str__(self):
        return ("{Inter " + str(self.intersection_id)
                + "\n  Loc: " + str(self.loc)
                + "\nRoads: " + str(self.roads)) + "\n}"

    def __repr__(self):
        return "Inter-" + str(self.intersection_id)

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

    def index(self, road):
        """Returns the index of a given road"""
        for i, curr_road in enumerate(self.roads):
            if curr_road.road_id == road.road_id:
                return i
        raise ValueError("Road not connected to intersection")

    def road_open(self):
        """Create the list of road vehicles allowed to move on that direction.
        The corresponding value is: turn left, go straight, turn right.
        Every 'delay' seconds, the intersection light will change.
        """
        delay = 10
        if self.counter % (delay * 40) < delay * 10:
            self.roads_list = [
                [False, True, True],
                [False, False, False],
                [False, True, True],
                [False, False, False]
            ]
        elif self.counter % (delay * 40) < delay * 20:
            self.roads_list = [
                [False, False, False],
                [False, True, True],
                [False, False, False],
                [False, True, True]
            ]
        elif self.counter % (delay * 40) < delay * 30:
            self.roads_list = [
                [True, False, False],
                [False, False, True],
                [True, False, False],
                [False, False, True]
            ]
        else:
            self.roads_list = [
                [False, False, True],
                [True, False, False],
                [False, False, True],
                [True, False, False]
            ]
        self.counter += 1

    def is_green(self, vehicle):
        """Check if light is green for vehicle; essentially an alias
        for Vehicle method can_go()
        """
        if vehicle.can_go():
            return True
        return False

    def turn_point(self, vehicle, road, io):
        """Find the endpoint location for a given road

        Param 'io' must be "input" or "output"
        """
        lane_width = 12

        min_offset = lane_width / 2
        if io == 'output':
            min_offset = -min_offset
        elif io != 'input':
            raise ValueError

        max_offset = lane_width + vehicle.size[0] / 2
        index = self.index(road)
        stop_line = None
        if index == 0:
            # If approaching from top
            stop_line = (self.loc[0] - min_offset, self.loc[1] + max_offset)
        elif index == 1:
            # If approaching from right
            stop_line = (self.loc[0] + max_offset, self.loc[1] + min_offset)
        elif index == 2:
            # If approaching from bottom
            stop_line = (self.loc[0] + min_offset, self.loc[1] - max_offset)
        elif index == 3:
            # If approaching from left
            stop_line = (self.loc[0] - max_offset, self.loc[1] - min_offset)
        else:
            raise ValueError
        return stop_line


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

    def __str__(self):
        return ("{Road " + str(self.road_id)
                + "\n  Loc: (" + self.ends[0].__repr__()
                + ", " + self.ends[1].__repr__()
                + ")\nSpeed: " + str(self.speed)) + "\n}"

    def __repr__(self):
        return "Road-" + str(self.road_id)

    def coords(self):
        """Get coordinates of the endpoints of the given road"""
        ends = []
        for i in range(2):
            try:
                ends.append(self.ends[i].loc)
            except AttributeError:
                ends.append(self.ends[i])
        return (ends[0], ends[1])

    def get_next_inter(self):
        """Return the only intersection connecting to this road"""
        singular = False
        result = None
        for end in self.ends:
            if hasattr(end, 'roads'):
                result = end
            else:
                singular = True
        if not singular or result is None:
            err = "Road does not have a singular connecting intersection"
            raise RuntimeError(err)
        return result

    def on_path(self, vehicle):
        """Determines if road is on route of vehicle"""
        if vehicle.road.road_id == self.road_id:
            return True
        if not vehicle.plan[1]:
            return False
        index = None
        inter_ids = [p.intersection_id for p in vehicle.plan[1]]
        for i, end in enumerate(self.ends):
            try:
                inter_id = end.intersection_id
            except AttributeError:
                inter_id = self.ends[(i + 1) % 2].intersection_id
                dest = vehicle.plan[0]
                # 9 is a safe value in case of overshooting at 60 mph
                if (inter_id == inter_ids[-1]
                        and abs(dest[0] - end[0]) < 9
                        and abs(dest[1] - end[1]) < 9):
                    return True
                return False
            if inter_id not in inter_ids:
                return False
            new_index = inter_ids.index(inter_id)
            if index is None:
                index = new_index
            elif abs(new_index - index) == 1:
                return True
        return False

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
