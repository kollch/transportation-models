import math

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
        k = b = b1 = b2 = 0
        # print(start_x," ",start_y," ",end_x," ",end_y)
        # print(self.roads[i].lanes/2)
        if self.roads[i].lanes % 2 == 0:
            #linear function y = kx + b
            if (end_x - start_x) != 0 and (end_y - start_y) == 0:
                y1 = end_y + 6
                y2 = end_y - 6
                # if the lanes is 2 then the road is in +6 or -6 because of road space
                if self.roads[i].lanes / 2 == 1:
                    if (current_y == y1 or current_y == y2) and (current_x >= start_x and current_x <= end_x):
                        return True
                    else:
                        return False
                # if the lanes is larger than 2. the road is  +6 + 12 ...
                else:
                    for i in range(int(self.roads[i].lanes / 2) - 1):
                        if (current_y == y1 or current_y == y2) and (current_x >= start_x and current_x <= end_x):
                            return True
                        else:
                            y1 += 12
                            y2 -= 12
                            if (current_y == y1 or current_y == y2) and (current_x >= start_x and current_x <= end_x):
                                return True
                    return False
            elif (end_x - start_x) != 0 and (end_y - start_y) != 0:
                # when the line is slash
                k = (end_y - start_y) / (end_x - start_x)
                angle = math.atan(k)
                b = start_y - k * start_x
                #calcullate 1st lane center and -1 lane center
                b1 = b + 6/math.cos(angle)
                b2 = b - 6/math.cos(angle)
                y1 = k * current_x + b1
                y2 = k * current_y + b2
                if self.roads[i].lanes / 2 == 1:
                    if (current_y == y1 or current_y == y2) and (current_x >= start_x and current_x <= end_x):
                        return True
                    else:
                        return False
                else:
                    for i in range(int(self.roads[i].lanes / 2) - 1):
                        if (current_y == y1 or current_y == y2) and (current_x >= start_x and current_x <= end_x):
                            return True
                        else:
                            b1 += 12/math.cos(angle)
                            b2 -= 12/math.cos(angle)
                            y1 = k * current_x + b1
                            y2 = k * current_y + b2
                            if (current_y == y1 or current_y == y2) and (current_x >= start_x and current_x <= end_x):
                                return True
                    return False
            else:
                #if end_x - start_x = 0
                if current_y <= max(start_y, end_y) and current_y >= min(start_y, end_y):
                    if (self.roads[i].lanes / 2 == 1) and (current_x == start_x + 6 or current_x == start_x - 6):
                        return True
                    elif self.roads[i].lanes / 2 > 1:
                        x1 = start_x + 6
                        x2 = start_x - 6
                        for i in range(int(self.roads[i].lanes / 2) - 1):
                            if current_x == x1 or current_x == x2:
                                return True
                            else:
                                x1 += 12
                                x2 -= 12
                                if current_x == x1 or current_x == x2:
                                    return True
                        return False
                """TODO: seperate to two funtion One in on_road another in road class"""
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
