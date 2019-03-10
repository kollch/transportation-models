import random
import math


class Vehicle():
    """Includes CAVs and HVs"""
    def __init__(self, world, attribs=(None, 20, 8, 0),
                 speed=(0, 0), locs=(None, None)):
        """Almost all parameters are grouped into sets of tuples:
        world:   InvisibleHand class.
                 Needed for things like cavs_in_range()
        attribs: (Vehicle ID, Vehicle length, Vehicle width, direction)
        speed:   (Speed, Acceleration)
        locs:    (Current location, Destination)
        """
        self.world = world
        self.vehicle_id = attribs[0]
        self.length = attribs[1]
        self.width = attribs[2]
        self.direction = attribs[3]
        self.speed = speed[0]
        self.accel = speed[1]
        self.loc = locs[0]
        self.dest = locs[1]
        self.route = []

    def angle(self, loc):
        """Compute angle from vehicle to location"""
        return math.atan2(loc[1] - self.loc[1], loc[0] - self.loc[0])

    def decide_move(self):
        """Determines move. Required to be implemented in CAV and HV"""
        raise NotImplementedError

    def at_intersection(self):
        """Determines if vehicle is at an intersection;
        based on proximity to center of intersection"""
        for x in self.world.infrastructure.intersections:
            # proximity currently set at 50 ft, may be changed
            if self.dist_to(x.location) < 50:
                return True
        return False

    def dist_to(self, loc):
        """Returns the distance between the vehicle and a given
        location"""
        return math.hypot(loc[0] - self.loc[0], loc[1] - self.loc[1])

    def can_see(self, infrastructure, cavs, hvs):
        """Returns a list of everything that the vehicle can see"""
        in_vision = []
        for vehicle in sorted(cavs + hvs, key=lambda v: self.dist_to(v.loc)):
            if vehicle is self:
                continue
            angle = vehicle.angle_edges(self)
            def leq(a, b):
                """Finds if angle a is less than angle b.
                Needed because of wrapping at pi = -pi"""
                if math.atan2(math.sin(a - b), math.cos(a - b)) <= 0:
                    return True
                return False
            def is_visible(angle_end_val=None):
                """Returns true if vehicle is visible, false
                otherwise"""
                for item in in_vision:
                    if angle_end_val is None:
                        low = item[1][0]
                        mid = angle[0]
                        angle_end = item[1][1]
                    else:
                        low = angle[0]
                        mid = item[1][0]
                        angle_end = angle_end_val
                    if leq(low, mid) and leq(mid, angle_end):
                        if leq(angle[1], item[1][1]):
                            return False
                        angle_end = item[1][1]
                        if angle_end_val is None:
                            return is_visible(angle_end)
                return True
            if is_visible():
                in_vision.append((vehicle, angle))
        return [i[0] for i in in_vision]

    def angle_edges(self, vehicle):
        """Returns the outermost seen angles of the vehicle from
        the given vehicle"""
        lsin = self.length / 2 * math.sin(self.direction)
        lcos = self.length / 2 * math.cos(self.direction)
        wsin = self.width / 2 * math.sin(self.direction)
        wcos = self.width / 2 * math.cos(self.direction)
        points = [(self.loc[0] + lcos + wsin, self.loc[1] + lsin - wcos),
                  (self.loc[0] - lcos - wsin, self.loc[1] + wcos - lsin),
                  (self.loc[0] + lcos - wsin, self.loc[1] + lsin + wcos),
                  (self.loc[0] + wsin - lcos, self.loc[1] - lsin - wcos)]
        angles = [vehicle.angle(i) for i in points]
        min_angle = min(angles)
        max_angle = max(angles)
        # Check if wrapping around pi = -pi
        if math.degrees(min_angle) < -90 and math.degrees(max_angle) > 90:
            return [max_angle, min_angle]
        return [min_angle, max_angle]


class CAV(Vehicle):
    """Connected autonomous vehicles
    Connect, decide action, move
    """
    autonomous = True

    def __str__(self):
        return ("{CAV " + str(self.vehicle_id)
                + "\n   Loc: " + str(self.loc)
                + "\n  Dest: " + str(self.dest)
                + "\n  Size: " + str(self.length) + " x " + str(self.width)
                + "\n Angle: " + str(self.direction) + "\n}")

    def __repr__(self):
        return "(CAV " + str(self.vehicle_id) + ")"

    def connect(self):
        """Gets info from CAVs within range"""
        return [
            v.give_info()
            for v in self.world.cavs_in_range(self.location, 3000)
        ]

    def give_info(self):
        """Returns info regarding vehicle location and speed"""
        return [self.location, self.speed, self.accel]

    def react_time(self):
        """Randomly-generated time it will take to react - for CAVs
        this should be instantaneous because the timesteps in this
        program should account for the small amount of reaction time
        CAVs have
        """
        return 0

    def dijkstras(self, source, dest):
        """Mostly pulled from
        https://gist.github.com/econchick/4666413

        Returns list of intersections from source to destination
        Clone of dijkstras() in HV until we use a different algorithm
        """
        visited = {source: 0}
        path = {}

        nodes = set(self.world.infrastructure.intersections)

        while nodes:
            min_node = None
            for node in nodes:
                if node in visited:
                    if min_node is None:
                        min_node = node
                    elif visited[node] < visited[min_node]:
                        min_node = node

            if min_node is None or min_node is dest:
                break

            nodes.remove(min_node)
            curr_weight = visited[min_node]

            for adj_node in min_node.adjacent():
                weight = curr_weight + adj_node[1].length / adj_node[1].speed
                if adj_node[0] not in visited or weight < visited[adj_node[0]]:
                    visited[adj_node[0]] = weight
                    path[adj_node[0]] = min_node
        solution = []
        curr_node = dest
        while curr_node in path:
            solution.append(curr_node)
            curr_node = path[curr_node]
        if curr_node is source:
            solution.append(source)
        solution.reverse()
        return solution

    def decide_move(self):
        """Uses available information and determines move"""
        if not self.route or self.at_intersection():
            self.route = self.dijkstras(self.loc, self.dest)



class HV(Vehicle):
    """Human-driven vehicles
    Decide action, move
    """
    autonomous = False

    def __str__(self):
        return ("{HV " + str(self.vehicle_id)
                + "\n   Loc: " + str(self.loc)
                + "\n  Dest: " + str(self.dest)
                + "\n  Size: " + str(self.length) + " x " + str(self.width)
                + "\n Angle: " + str(self.direction) + "\n}")

    def __repr__(self):
        return "(HV " + str(self.vehicle_id) + ")"

    def react_time(self):
        """Randomly-generated time it will take to react"""
        mu = 0.5
        sigma = 1
        r_time = random.gauss(mu, sigma)

        # r_time is randomly number but sometimes it will have negative number
        while r_time <= 0:
            r_time = random.gauss(mu, sigma)
        return r_time

    def dijkstras(self, source, dest):
        """Mostly pulled from
        https://gist.github.com/econchick/4666413

        Returns list of intersections from source to destination
        """
        visited = {source: 0}
        path = {}

        nodes = set(self.world.infrastructure.intersections)

        while nodes:
            min_node = None
            for node in nodes:
                if node in visited:
                    if min_node is None:
                        min_node = node
                    elif visited[node] < visited[min_node]:
                        min_node = node

            if min_node is None or min_node is dest:
                break

            nodes.remove(min_node)
            curr_weight = visited[min_node]

            for adj_node in min_node.adjacent():
                weight = curr_weight + adj_node[1].length / adj_node[1].speed
                if adj_node[0] not in visited or weight < visited[adj_node[0]]:
                    visited[adj_node[0]] = weight
                    path[adj_node[0]] = min_node
        solution = []
        curr_node = dest
        while curr_node in path:
            solution.append(curr_node)
            curr_node = path[curr_node]
        if curr_node is source:
            solution.append(source)
        solution.reverse()
        return solution

    def decide_move(self):
        """Looks in immediate vicinity and determines move"""
        if not self.route:
            self.route = self.dijkstras(self.location, self.destination)
