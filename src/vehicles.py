import random


class Vehicle():
    """Includes CAVs and HVs"""
    def __init__(self, vehicle_id=None, length=20,
                 location=None, destination=None):
        self.vehicle_id = vehicle_id
        self.length = length
        self.location = location
        self.destination = destination

    def decide_move(self):
        """Determines move. Required to be implemented in CAV and HV"""
        raise NotImplementedError


class CAV(Vehicle):
    """Connected autonomous vehicles
    Connect, decide action, move
    """
    autonomous = True

    def connect(self):
        """Gets info from CAVs within range"""
        for cav in cavs_in_range(current_location, 3000):
            info = cav.give_info()
        return

    def give_info(self):
        return [location, speed, accel]

    def react_time(self):
        """Randomly-generated time it will take to react - for CAVs
        this should be instantaneous because the timesteps in this
        program should account for the small amount of reaction time
        CAVs have
        """
        return 0

    def dijkstras(self,current,adj_map,unvisited, visited, distances, path):
#        print "Currently on node:", current
        prev = current
#        print "Adj_map",adj_map
        options = {}

#        print "UNVISITED:",unvisited
        starting_loc = distances[current]
        for adj in adj_map:
            if adj in unvisited:
#                print "looking at node",adj
                """calc distances from this node to adjacent ones"""
                new_dist = distances[current] + adj_map[adj]
                if new_dist < unvisited[adj]:
                    unvisited[adj] = new_dist
                    options[adj] = new_dist
                else:
                    options[adj] = unvisited[adj]
        """if there are elements in the options dict, we can take into consideration"""
        if options:
#            print "OPTIONS:", options
            """gets lowest value adjacent node and makes it our new current"""
            current = min(options, key = options.get)

            #        print "CURRENT:",current
            weight = adj_map[current]
            #        visited[current] = weight
            ##        print "PREV", path[prev]
            ##        path[current] = path[prev]
            path[current] = ( {prev : weight }) #add previous shortest path for node
            distances[current] = weight
#            print "CHOOSE", current
#            print "paths:",path
#            print
            return current
        """otherwise, no need"""
        else:
#            print "no options"
            return "nothing"

    def print_path(self, path):
        """function to print the found path"""
        route = {}
        step = self.destination

        while step != self.origin:
            route = {}
            route.update(path[step])
            print path[step]
            step = route.iterkeys().next()

        return

    def decide_move(self, map, visited={},distances={},unvisited={}, path={}):
        """Uses available information and determines move"""

        """Currently running with custom main function which feeds a dictionary with with map of infrastructure and custom vehicle"""

        current = self.location

        """If we are at very beginning, set/reset vehicle routing info"""
        if(current == self.origin):
            visited = {current:0}
            distances[current] = 0
            path[current] = 'Begin'

            """Set all adjacency edges to infinity"""
            for node in map:
                if node == self.origin: continue
                unvisited[node] = float('inf')

        """starting with all adjacent nodes surrounding given location"""
        for adj in map[current]:
#            print "FOR LOOP ON", adj,"--------------------------"
            """run dijkstra's and tentatively find most viable next node"""
            current = self.dijkstras(current, map[current], unvisited, visited, distances, path)
#            print "here is current:", current
            """if we haven't visited the node yet, mark as visited and run again"""
            if current in unvisited:
                visited[current] = distances[current]
                del unvisited[current]
            """If we cannot find a viable node that we haven't already checked, just move on"""
            elif current == "nothing":
                current = self.location
                break
            self.dijkstras(current, map[current], unvisited, visited, distances, path)
            current = self.location
#            print current

        """After we check all adjacent, pick node we actually want to move to"""
        current = min(map[current], key = map[current].get) #should be E

#        print current
#        print unvisited
#        print visited
#        print "MOVING TO ANOTHER FUNCTION with",current,"~~~~~~"
        """run this method until we reach the destination"""
        while current != self.destination:
            self.location = current
            current = self.dijkstras(current, map[current], unvisited, visited, distances, path )

        print "Path routed:"
        self.print_path(path)
        return


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

        # r_time is randomly number but sometimes it will has negative number
        while r_time <= 0:
            r_time = random.gauss(mu, sigma)
        return r_time

    def decide_move(self, map, visited={},distances={},unvisited={}, path={}):
        """Uses available information and determines move"""

        """Currently running with custom main function which feeds a dictionary with with map of infrastructure and custom vehicle"""

        current = self.location

        """If we are at very beginning, set/reset vehicle routing info"""
        if(current == self.origin):
            visited = {current:0}
            distances[current] = 0
            path[current] = 'Begin'

            """Set all adjacency edges to infinity"""
            for node in map:
                if node == self.origin: continue
                unvisited[node] = float('inf')

        """starting with all adjacent nodes surrounding given location"""
        for adj in map[current]:
            #            print "FOR LOOP ON", adj,"--------------------------"
            """run dijkstra's and tentatively find most viable next node"""
            current = self.dijkstras(current, map[current], unvisited, visited, distances, path)
            #            print "here is current:", current
            """if we haven't visited the node yet, mark as visited and run again"""
            if current in unvisited:
                visited[current] = distances[current]
                del unvisited[current]
            """If we cannot find a viable node that we haven't already checked, just move on"""
            elif current == "nothing":
                current = self.location
                break
            self.dijkstras(current, map[current], unvisited, visited, distances, path)
            current = self.location
                #            print current

        """After we check all adjacent, pick node we actually want to move to"""
        current = min(map[current], key = map[current].get) #should be E


        """run this method until we reach the destination"""
        while current != self.destination:
            self.location = current
                current = self.dijkstras(current, map[current], unvisited,visited, distances, path )

        print "Path routed:"
        self.print_path(path)
        return
