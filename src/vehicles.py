"""This determines everything to do with the vehicles."""
import random
import math
import time

class Vehicle():
    """Includes CAVs and HVs"""
    safe_decel = -3.40909
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
        # (Vehicle length, width)
        self.size = (attribs[1], attribs[2])
        # (Vehicle speed, direction)
        self.veloc = [speed[0], attribs[3]]
        self.accel = speed[1]
        self.loc = locs[0]
        # (Destination, route)
        self.plan = [locs[1], []]

    def angle(self, loc):
        """Compute angle from vehicle to location"""
        return math.atan2(loc[1] - self.loc[1], loc[0] - self.loc[0])

    def decide_move(self):
        """Determines move. Required to be implemented in CAV and HV"""
        raise NotImplementedError

    def at_intersection(self):
        """Determines if vehicle is at an intersection;
        based on proximity to center of intersection
        """
        for intersection in self.world.infrastructure.intersections:
            # proximity currently set at 50 ft, may be changed
            if self.dist_to(intersection.loc) < 50:
                return True
        return False
    
    def nearest_intersection(self, pos, intersections):
        """Take coordinate location of a vehicle and returns
            an intersection object that is closest"""
        min_distance = 100000
        nearest = 0
        for intersection in intersections:
            distance = math.hypot(intersection.loc[0] - pos[0], intersection.loc[1] - pos[1])

            if min_distance > distance:
                nearest = intersection
                min_distance = distance
        return nearest

    def dist_to(self, loc):
        """Returns the distance between the vehicle and a given
        location"""
        return math.hypot(loc[0] - self.loc[0], loc[1] - self.loc[1])

    def can_see(self, cavs, hvs):
        """Returns a list of everything that the vehicle can see"""
        in_vision = []
        for vehicle in sorted(cavs + hvs, key=lambda v: self.dist_to(v.loc)):
            if vehicle is self:
                continue
            angle = vehicle.angle_edges(self)

            def leq(a_1, a_2):
                """Finds if angle a is less than angle b.
                Needed because of wrapping at pi = -pi"""
                if math.atan2(math.sin(a_1 - a_2), math.cos(a_1 - a_2)) <= 0:
                    return True
                return False

            def is_visible(angle, angle_end_val=None):
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
                            return is_visible(angle, angle_end)
                return True
            if is_visible(angle):
                in_vision.append((vehicle, angle))
        return [i[0] for i in in_vision]

    def angle_edges(self, vehicle):
        """Returns the outermost seen angles of the vehicle from
        the given vehicle"""
        lsin = self.size[0] / 2 * math.sin(self.veloc[1])
        lcos = self.size[0] / 2 * math.cos(self.veloc[1])
        wsin = self.size[1] / 2 * math.sin(self.veloc[1])
        wcos = self.size[1] / 2 * math.cos(self.veloc[1])
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
    react_factor = 0

    def __str__(self):
        return ("{CAV " + str(self.vehicle_id)
                + "\n   Loc: " + str(self.loc)
                + "\n  Dest: " + str(self.plan[0])
                + "\n  Size: " + str(self.size[0]) + " x " + str(self.size[1])
                + "\n Angle: " + str(self.veloc[1]) + "\n}")

    def __repr__(self):
        return "(CAV " + str(self.vehicle_id) + ")"

    def connect(self):
        """Gets info from CAVs within range"""
        return [
            v.give_info()
            for v in self.world.cavs_in_range(self.loc, 3000)
        ]

    def give_info(self):
        """Returns info regarding vehicle location and speed"""
        return [self.loc, self.veloc[0], self.accel]

    def react_time(self):
        """Randomly-generated time it will take to react - for CAVs
        this should be instantaneous because the timesteps in this
        program should account for the small amount of reaction time
        CAVs have
        """
        return 0 * self.react_factor

    def dijkstras(self, source, dest):
        """Mostly pulled from
        https://gist.github.com/econchick/4666413

        Returns list of intersections from source to destination
        Clone of dijkstras() in HV until we use a different algorithm
        """
        nodes = set(self.world.infrastructure.intersections)
        source = self.nearest_intersection(source,nodes)
        dest = self.nearest_intersection(dest,nodes)
        visited = {source: 0}
        path = {}
        
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

    def decide_move(self, t):
        """Uses available information and determines move"""
        if not self.plan[1] or self.at_intersection():
            self.plan[1] = self.dijkstras(self.loc, self.plan[0])
        

    def make_move(self, t):
        """Updates location coordinates depending on passed time
        and direction"""
        movement = float(self.veloc[0]) * (time.time() - t)
        
        #if moving East
        if(self.veloc[1] == 0):
            new_x = self.loc[0]
            new_x += movement
            y = self.loc[1]
            self.loc = (new_x, y)
        #if moving West
        if(self.veloc[1] == 180):
            new_x = self.loc[0]
            new_x -= movement
            y = self.loc[1]
            self.loc = (new_x, y)
        #if moving North
        if(self.veloc[1] == 90):
            x = self.loc[0]
            new_y = self.loc[1]
            new_y += movement
            self.loc = (new_x, y)
        #if moving South
        if(self.veloc[1] == 270):
            x = self.loc[0]
            new_y = self.loc[1]
            new_y -= movement
            self.loc = (new_x, y)



class HV(Vehicle):
    """Human-driven vehicles
    Decide action, move
    """
    autonomous = False
    react_factor = 1

    def __str__(self):
        return ("{HV " + str(self.vehicle_id)
                + "\n   Loc: " + str(self.loc)
                + "\n  Dest: " + str(self.plan[0])
                + "\n  Size: " + str(self.size[0]) + " x " + str(self.size[1])
                + "\n Angle: " + str(self.veloc[1]) + "\n}")

    def __repr__(self):
        return "(HV " + str(self.vehicle_id) + ")"

    def react_time(self):
        """Randomly-generated time it will take to react"""
        mean = 0.5
        std_dev = 1
        r_time = random.gauss(mean, std_dev)

        # Could be a negative number; if so, retry
        while r_time <= 0:
            r_time = random.gauss(mean, std_dev)
        return r_time * self.react_factor

    def dijkstras(self, source, dest):
        """Mostly pulled from
        https://gist.github.com/econchick/4666413

        Returns list of intersections from source to destination
        """
        nodes = set(self.world.infrastructure.intersections)
        source = self.nearest_intersection(src,nodes)
        dest = self.nearest_intersection(dest,nodes)
        visited = {source: 0}
        path = {}
        
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
        if not self.plan[1]:
            self.plan[1] = self.dijkstras(self.loc, self.plan[0])
