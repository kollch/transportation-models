class Infrastructure():
    """Holds all of the intersections and roads"""
    def __init__(self, intersections, roads):
        self.intersections = intersections
        self.roads = roads

    def on_road(self, current_x, current_y, i):
        """check if a point on the road i"""
        start_x = start_y = end_x = end_y = 0
        if type(self.roads[i].ends[0]) == int:
            start_x = self.intersections[self.roads[i].ends[0] - 1].location[0]
            start_y = self.intersections[self.roads[i].ends[0] - 1].location[1]
        else:
            start_x = self.roads[i].ends[0][0]
            start_y = self.roads[i].ends[0][1]
        if type(self.roads[i].ends[1]) == int:
            end_x = self.intersections[self.roads[i].ends[1] - 1].location[0]
            end_y = self.intersections[self.roads[i].ends[1] - 1].location[1]
        else:
            end_x = self.roads[i].ends[1][0]
            end_y = self.roads[i].ends[1][1]
        k = b1 = b2 = 0
        if self.roads[i].lanes % 2 == 0:
            #linear function y = kx + b
            if (end_x - start_x) != 0:
                k = (end_y - start_y) / (end_x - start_x)
                b1 = (end_y + 6) - k * end_x
                b2 = (end_y - 6) - k * end_x
                y1 = k * current_x + b1
                y2 = k * current_x + b2
                # if the lanes is 2 then the road is in +6 or -6 because of road space
                if self.roads[i].lanes / 2 == 1:
                    if float(current_y) == y1 or float(current_y) == y2:
                        return True
                    else:
                        return False
                # if the lanes is larger than 2. the road is  +6 + 12 ...
                else:
                    for i in range(int(self.roads[i].lanes / 2) - 1):
                        if float(current_y) == y1 or float(current_y) == y2:
                            return True
                        else:
                            b1 += 12
                            b2 -= 12
                            y1 = k * current_x + b1
                            y2 = k * current_x + b2
                            if float(current_y) == y1 or float(current_y) == y2:
                                return True
                    return False
                    """need consider when lane is old in one-way roads"""
        return False


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
