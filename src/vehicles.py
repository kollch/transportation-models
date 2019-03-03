import random


class Vehicle():
    """Includes CAVs and HVs"""
    def __init__(self, world, attribs=(None, 20),
                 speed=(0, 0), locs=(None, None)):
        """Almost all parameters are grouped into sets of tuples:
        world:   InvisibleHand class.
                 Needed for things like cavs_in_range()
        attribs: (Vehicle ID, Vehicle length)
        speed:   (Speed, Acceleration)
        locs:    (Current location, Destination)
        """
        self.world = world
        self.vehicle_id = attribs[0]
        self.length = attribs[1]
        self.speed = speed[0]
        self.accel = speed[1]
        self.location = locs[0]
        self.destination = locs[1]
        self.route = []

    def decide_move(self):
        """Determines move. Required to be implemented in CAV and HV"""
        raise NotImplementedError

    def at_intersection(self):
        """Determines if vehicle is at an intersection; probably should
        be based on proximity to center of intersection
        """
        return False


class CAV(Vehicle):
    """Connected autonomous vehicles
    Connect, decide action, move
    """
    autonomous = True

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
            self.route = self.dijkstras(self.location, self.destination)


class HV(Vehicle):
    """Human-driven vehicles
    Decide action, move
    """
    autonomous = False

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
