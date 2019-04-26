"""This determines everything to do with the vehicles."""
import random
import math


class Vehicle():
    """Includes CAVs and HVs"""
    def __init__(self, world, attribs=(None, 20, 8, 0),
                 speed=(60, 0), locs=(None, None)):
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
        self.following = False
        self.in_front = None
        self.during_turn = False
        self.turn = None
        self.curr_road = None
        self.next_road = None

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

    def get_road(self):
        """Returns road vehicle is currently on"""
        for road in self.world.infrastructure.roads:
            if self in road.vehicles_on:
                return road
        return None

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

    def decide_accel(self):
        """Based on code from
            https://github.com/titaneric/trafficModel
            Decides acceleration based on car following or approach to
            intersections;
            """
        a = 12
        b = 10.3
        closeby = self.can_see(self.world.cavs, self.world.hvs)
        if not closeby:
            if self.veloc[0] < self.get_road().speed:
                return a
            return 0
        # sort array by angle relativity to current vehicle
        closeby.sort(key=lambda v: abs(self.veloc[1] - math.degrees(self.angle(v.loc))))
        for i in closeby:
            if i.veloc[1] != self.veloc[1]:
                closeby.remove(i)

        if not closeby:
            if self.veloc[0] < self.get_road().speed:
                return a
            return 0

        if -1 < self.veloc[1] - math.degrees(self.angle(closeby[0].loc)) < 1 and abs(self.veloc[1] - closeby[0].veloc[1]) < 45:
            self.in_front = closeby[0]
            self.following = True

        if self.in_front is None:
            self.following = False
            if self.veloc[0] < 60:
                return a
            return 0
        # if vehicle that is in front is further than 60 feet away, move freely
        if self.dist_to(self.in_front.loc) > 60:
            # if vehicle is going speed limit, do not accelerate
            if self.veloc[0] >= self.get_road().speed:
                return 0
            return a

        dist_to_intersection = self.dist_to(self.plan[1][0].loc)

        # set values for acceleration(a) and deceleration(b)
        b = 3.735684
        # Stimulus Coefficient = 0.74
        coef = 0.74
        # Reaction Time = 2.2 s, Time gap between the decelerations.
        deltat = 2.2
        # Deceleration Rate of the First Vehicle (ft/s^2)
        rate = -4.6
        # Initial Headway between each Vehicle = 114 ft
        hini = -114

        # if self.veloc[0] + self.accel * 0.1 > 0:
        #     self.veloc[0]

        if self.in_front is not None:
            delta_speed = (self.veloc[0] - self.in_front.veloc[0])
        else:
            delta_speed = 0
        # coefficient if no car in front
        free_coeff = (self.veloc[0] / 60) ** 4
        # distance gap
        d_gap = 2
        # time gap
        t_gap = self.veloc[0] + 1.5
        # braking gap
        b_gap = self.veloc[0] * delta_speed / (2 * math.sqrt(a * b))
        safe_dist_follow = d_gap + t_gap + b_gap
        # coefficient if car following
        if self.in_front is not None:
            try:
                follow_coeff = (safe_dist_follow / self.dist_to(self.in_front.loc)) ** 2
            except ZeroDivisionError:
                follow_coeff = 0
        else:
            follow_coeff = 0

        safe_dist_intersection = 1 + t_gap + self.veloc[0] ** 2 / (2 * b)
        if dist_to_intersection != 0:
            intersection_coeff = ((safe_dist_intersection / dist_to_intersection) ** 2)
        else:
            intersection_coeff = 0
        if self.in_front is None:
            coeff = (1 - free_coeff)
        else:
            coeff = 1 - free_coeff - follow_coeff - intersection_coeff
        return self.accel * coeff

    def can_go(self, turn):
        """Returns True if direction passed is allowed through intersection,
            False if not.
        """
        curr_road = self.get_road()
        i = 0
        for count, r in enumerate(self.world.infrastructure.closest_intersection(self.loc).roads):
            if r is None:
                continue
            if curr_road.road_id == r.road_id:
                i = count
        return self.world.infrastructure.closest_intersection(self.loc).roads_list[i][turn]

    def update_coords(self):
        """Updates location coordinates depending on passed time and
        direction
        """
        movement = self.veloc[0] * 528 / 3600
        d_x = movement * math.cos(math.radians(self.veloc[1]))
        d_y = movement * math.sin(math.radians(self.veloc[1]))
        self.loc = (d_x + self.loc[0], d_y + self.loc[1])

    def turn_dir(self):
        """Returns 0 for left turn, 1 for straight, 2 for right turn"""
        curr_road = self.get_road()
        inter_1 = self.plan[1][0]
        inter_2 = self.plan[1][1]
        road_index = 0
        for count, r in enumerate(inter_1.roads):
            if r is None:
                continue
            if curr_road.road_id == r.road_id:
                road_index = count
        for i, road_id in enumerate(inter_1.roads):
            if road_id in inter_2.roads:
                connecting_road_index = i
                break
        return (connecting_road_index + 4 - road_index) % 4 - 1

    def get_side_road(self, rid):
        """While vehicle turning direction, get road information on
        one side
        """
        for road in self.world.infrastructure.roads:
            if rid == road.road_id:
                return road
        return None

    def turning_point(self):
        """This function used to find the turning lane middle point
        """
        # turning point
        turning_point = [[], []]
        # find intersection location and id
        inter1_id = 0
        inter2_id = 0
        v_road_id = 0
        curr_road = self.get_road()
        inter_1 = self.plan[1][0]
        if not self.plan[1][1]:
            inter_2 = None
        else:
            inter_2 = self.plan[1][1]
        inter1_loc = []
        inter2_loc = []
        # intersections connecting roads
        inter1_roads = []
        inter2_roads = []
        # connecting road id with next intersection
        connect_rid = 0
        # for intersection in self.world.infrastructure.intersections:
        #     print(self.dist_to(intersection.loc))
        #     if self.dist_to(intersection.loc) < 30:
        inter1_id = self.plan[1][0].intersection_id
        v_road_id = self.get_road().road_id
        inter1_loc = self.plan[1][0].loc
        # turn left or right need to find next intersection id
        for i in range(len(self.plan[1])):
            if inter1_loc == self.plan[1][i].loc:
                inter2_loc = self.plan[1][i + 1].loc
        for intersection in self.world.infrastructure.intersections:
            if inter2_loc == intersection.loc:
                inter2_id = intersection.intersection_id
        # find two intersection roads list
#        print(inter1_id)
        for intersection in self.world.infrastructure.intersections:
#            print(intersection.intersection_id)
            if inter1_id == intersection.intersection_id:
                # for i in range (4):
                #     try:
                inter1_roads = intersection.roads
                #     except TypeError:

            if inter2_id == intersection.intersection_id:
                inter2_roads = intersection.roads
        # find connecting road
        for i in inter1_roads:
            if i in inter2_roads:
                connect_rid = i
        # determine turn left or turn right by two road id order in intersection, 0 -- left, 1 -- right
        turn_d = 0
        # Entering lane
        lane_side = 0
        ori_lane_side = 0
        # If vehicle go straight 0 -- no, 1 -- yes
        straight = 0
        for i in range(4):
#            print("v_roadId: ", v_road_id, inter1_roads[i])
            if v_road_id == inter1_roads[i].road_id:
                # for r in range(2):
                #     try:
                #         ends_coord_1.append((road.ends[r][0], road.ends[r][1]))
                #     except TypeError:
                #         ends_coord_1.append(road.ends[r].loc)
#                print("v_roadId: ", v_road_id, inter1_roads[i])
                for j in range(4):
                    if connect_rid == inter1_roads[j]:
                        if i != 3:
                            if i == j - 1:
                                turn_d = 0
                            if i == j + 1:
                                turn_d = 1
                            else:
                                straight = 1
                        if i == 3:
                            if j == 0:
                                turn_d = 0
                            if j == 2:
                                turn_d = 1
                            else:
                                straight = 1
                        ori_lane_side = i
                        lane_side = j
        # find the road line width later
#        print("turning，straight，into side，out side：", turn_d, straight, ori_lane_side, lane_side)
        x_1 = inter1_loc[0]
        y_1 = inter1_loc[1]
        x_2 = inter2_loc[0]
        y_2 = inter2_loc[1]
        xle = x_2 - x_1
        yle = y_2 - y_1
        zle = math.sqrt(xle ** 2 + yle ** 2)

        # find another two sides width
        road_id_1 = 0
        road_id_2 = 0
        degree_1 = 0
        degree_2 = 0
        # the biggest width about lanes on vehicles' origin sides
        ori_lane_width = 0
        # the width about the lane on turning side
        turn_lane_width = 0
        sides_road_loc_1 = []
        sides_road_loc_2 = []
        road_id_1 = 0
        road_id_2 = 0
        # road ends coord
        ends_coord_1 = []
        ends_coord_2 = []
        # case turning to position 0 and 2
        if straight == 0:
            if lane_side in (0, 2):
                road_id_1 = inter1_roads[1]
                road_id_2 = inter1_roads[3]
#                print("in lane_side 0 or 2, straight 0", road_id_1, road_id_2)
                for road in self.world.infrastructure.roads:
                    if road_id_1 == road.road_id:
                        for r in range(2):
                            try:
                                ends_coord_1.append((road.ends[r][0], road.ends[r][1]))
                            except TypeError:
                                ends_coord_1.append(road.ends[r].loc)
#                        print("straight 0, rd 1: lane_side 0 or 2", ends_coord_1)
                        sides_road_loc_1.append((ends_coord_1[0][0] + ends_coord_1[1][0]) / 2)
                        sides_road_loc_1.append((ends_coord_1[1][0] + ends_coord_1[1][1]) / 2)
                        # sides_road_loc_1[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_1[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_1 = abs(self.get_side_road(road_id_1).lane_direction(sides_road_loc_1))
                    if road_id_2 == road.road_id:
                        for r in range(2):
                            try:
                                ends_coord_2.append((road.ends[r][0], road.ends[r][1]))
                            except TypeError:
                                ends_coord_2.append(road.ends[r].loc)
#                        print("straight 0, rd 2: lane_side 0 or 2", ends_coord_2)
                        sides_road_loc_2.append((ends_coord_2[0][0] + ends_coord_2[1][0]) / 2)
                        sides_road_loc_2.append((ends_coord_2[1][0] + ends_coord_2[1][1]) / 2)
                        # sides_road_loc_2[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_2[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_2 = abs(self.get_side_road(road_id_2).lane_direction(sides_road_loc_2))
                angle_1 = math.radians(abs(degree_1))
                angle_2 = math.radians(abs(degree_2))
                if degree_1 < 180 and degree_1 > 0:
                    if degree_1 > 90:
                        angle_1 = math.radians(abs(degree_1 - 180))
                if degree_2 < 180 and degree_2 > 0:
                    if degree_2 > 90:
                        angle_2 = math.radians(abs(degree_2 - 180))
#                print("degree_1 and degree_2", (degree_1), (degree_2))
#                print("angle_1 and angle_2 ", angle_1, angle_2)
                if degree_1 not in (0, 180) and degree_2 not in (0, 180):
                    if (angle_1 < angle_2) and angle_1 > 0:
                        ori_lane_width = 12 / math.sin(angle_1)
                    if (angle_1 >= angle_2) and angle_2 > 0:
                        ori_lane_width = 12 / math.sin(angle_2)
                if degree_1 in (0, 180) and degree_2 in (0, 180):
                    ori_lane_width = 12
                if degree_1 in (0, 180) and degree_2 not in (0, 180):
                    ori_lane_width = 12 / math.sin(angle_2)
                if degree_1 not in (0, 180) and degree_2 in (0, 180):
                    ori_lane_width = 12 / math.sin(angle_1)
                # calculate turning lane width
                if yle != 0:
                    turn_lane_width = 12 * zle / abs(yle)
                if yle == 0:
                    turn_lane_width = 12
                # find middle point
                if turn_d == 0:
#                    print("turn left")
                    if lane_side == 0:
                        turning_point[1].append(inter1_loc[0] + turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] + ori_lane_width)
                    if lane_side == 2:
                        turning_point[1].append(inter1_loc[0] - turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] - ori_lane_width)
                if turn_d == 1:
#                    print("turn right")
                    if lane_side == 0:
                        turning_point[1].append(inter1_loc[0] + turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] + ori_lane_width)
                    if lane_side == 2:
                        turning_point[1].append(inter1_loc[0] - turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] - ori_lane_width)
#                print(turning_point)
                if ori_lane_side == 1:
                    turning_point[0].append(inter1_loc[0] + turn_lane_width)
                    turning_point[0].append(inter1_loc[0] + ori_lane_width / 2)
                if ori_lane_side == 3:
                    turning_point[0].append(inter1_loc[0] - turn_lane_width)
                    turning_point[0].append(inter1_loc[0] - ori_lane_width / 2)
            # case turning to position 1 and 3
            if lane_side in (1, 3):
                road_id_1 = inter1_roads[0]
                road_id_2 = inter1_roads[2]
#                print("in lane_side 1 or 3, straight 1", road_id_1, road_id_2)
                for road in self.world.infrastructure.roads:
                    if road_id_1 == road.road_id:
                        for r in range(2):
                            try:
                                ends_coord_1.append((road.ends[r][0], road.ends[r][1]))
                            except TypeError:
                                ends_coord_1.append(road.ends[r].loc)
#                        print("straight 0, rd 1: lane_side 1 or 3", ends_coord_1)
                        sides_road_loc_1.append((ends_coord_1[0][0] + ends_coord_1[1][0]) / 2)
                        sides_road_loc_1.append((ends_coord_1[1][0] + ends_coord_1[1][1]) / 2)
                        # sides_road_loc_1[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_1[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_1 = abs(self.get_side_road(road_id_1).lane_direction(sides_road_loc_1))
                    if road_id_2 == road.road_id:
                        for r in range(2):
                            try:
                                ends_coord_2.append((road.ends[r][0], road.ends[r][1]))
                            except TypeError:
                                ends_coord_2.append(road.ends[r].loc)
#                        print("straight 0, rd 2: lane_side 1 or 3", ends_coord_2)
                        sides_road_loc_1.append((ends_coord_2[0][0] + ends_coord_2[1][0]) / 2)
                        sides_road_loc_1.append((ends_coord_2[1][0] + ends_coord_2[1][1]) / 2)
                        # sides_road_loc_2[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_2[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_2 = abs(self.get_side_road(road_id_2).lane_direction(sides_road_loc_2))
                angle_1 = math.radians(abs(degree_1))
                angle_2 = math.radians(abs(degree_2))
                if degree_1 > 90:
                    angle_1 = math.radians(abs(degree_1 - 180))
                if degree_2 > 90:
                    angle_2 = math.radians(abs(degree_2 - 180))
#                print("degree_1 and degree_2", (degree_1), (degree_2))
#                print("angle_1 and angle_2 ", angle_1, angle_2)
                if degree_1 != 90 and degree_2 != 90:
                    if (angle_1 < angle_2) and angle_1 > 0:
                        ori_lane_width = 12 / math.sin(angle_1)
                    if (angle_1 >= angle_2) and angle_2 > 0:
                        ori_lane_width = 12 / math.sin(angle_2)
                if degree_1 == 90 and degree_2 == 90:
                    ori_lane_width = 12
                if degree_1 == 90 and degree_2 != 90:
                    ori_lane_width = 12 / math.sin(angle_2)
                if degree_1 != 90 and degree_2 == 90:
                    ori_lane_width = 12 / math.sin(angle_1)
                # calculate turning lane width
                if xle != 0:
                    turn_lane_width = 12 * zle / abs(xle)
                if xle == 0:
                    turn_lane_width = 12
                # find middle point
                if turn_d == 0:
                    if lane_side == 1:
                        turning_point[1].append(inter1_loc[0] + turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] - ori_lane_width)
                    if lane_side == 3:
                        turning_point[1].append(inter1_loc[0] - turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] + ori_lane_width)
                if turn_d == 1:
                    if lane_side == 1:
                        turning_point[1].append(inter1_loc[0] + turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] - ori_lane_width)
                    if lane_side == 3:
                        turning_point[1].append(inter1_loc[0] - turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] + ori_lane_width)
                if ori_lane_side == 0:
                    turning_point[0].append(inter1_loc[0] - ori_lane_width / 2)
                    turning_point[0].append(inter1_loc[1] + turn_lane_width)
                if ori_lane_side == 2:
                    turning_point[0].append(inter1_loc[0] + ori_lane_width / 2)
                    turning_point[0].append(inter1_loc[1] - turn_lane_width)
        v_road_mid = []
        two_road_width = 0
        v_road_width = 0
        ends_coord_v = []
        if straight == 1:
            for road in self.world.infrastructure.roads:
                if v_road_id == road.road_id:
                    for r in range(2):
                        try:
                            ends_coord_v.append((road.ends[r][0], road.ends[r][1]))
                            # v_road_mid[r] = (road.ends[0][r] + road.ends[1][r]) / 2
                        except TypeError:
                            ends_coord_v.append(road.ends[r].loc)
#                    print("v_road_ends: in straight 1", ends_coord_v)
                    v_road_mid.append((ends_coord_v[0][0] + ends_coord_v[1][0]) / 2)
                    v_road_mid.append((ends_coord_v[1][0] + ends_coord_v[1][1]) / 2)
                    degree_v_road = abs(self.get_side_road(v_road_id).lane_direction(v_road_mid))
                    angle_v_rd = math.radians(abs(degree_v_road - 90))
                    if degree_v_road not in (0, 90):
                        v_road_width = 12 / math.sin(angle_v_rd)
                    else:
                        v_road_width = 12
            if lane_side in (0, 2):
                road_id_1 = inter1_roads[1].road_id
                road_id_2 = inter1_roads[3].road_id
#                print("in lane_side 0 or 2, straight 1", road_id_1, road_id_2)
                for road_xx in self.world.infrastructure.roads:
                    if road_id_1 == road_xx.road_id:
                        for r in range(2):
                            try:
                                ends_coord_1.append((road_xx.ends[r][0], road_xx.ends[r][1]))
                            except TypeError:
                                ends_coord_1.append(road_xx.ends[r].loc)
#                        print("straight 1, rd 1: lane_side 0 or 2", ends_coord_1)
                        sides_road_loc_1.append((ends_coord_1[0][0] + ends_coord_1[1][0]) / 2)
                        sides_road_loc_1.append((ends_coord_1[1][0] + ends_coord_1[1][1]) / 2)
                        # sides_road_loc_1[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_1[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_1 = abs(self.get_side_road(road_id_1).lane_direction(sides_road_loc_1))
                    if road_id_2 == road_xx.road_id:
                        for r in range(2):
                            try:
                                ends_coord_2.append((road.ends[r][0], road.ends[r][1]))
                            except TypeError:
                                ends_coord_2.append(road.ends[r].loc)
#                        print("straight 1, rd 2: lane_side 0 or 2", ends_coord_2)
                        sides_road_loc_2.append((ends_coord_2[0][0] + ends_coord_2[1][0]) / 2)
                        sides_road_loc_2.append((ends_coord_2[1][0] + ends_coord_2[1][1]) / 2)
                        # sides_road_loc_2[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_2[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_2 = abs(self.get_side_road(road_id_2).lane_direction(sides_road_loc_2))
                angle_1 = math.radians(abs(degree_1))
                angle_2 = math.radians(abs(degree_2))
                if degree_1 < 180 and degree_1 > 0:
                    if degree_1 > 90:
                        angle_1 = math.radians(abs(degree_1 - 180))
                if degree_2 < 180 and degree_2 > 0:
                    if degree_2 > 90:
                        angle_2 = math.radians(abs(degree_2 - 180))
#                print("degree_1 and degree_2", (degree_1), (degree_2))
#                print("angle_1 and angle_2 ", angle_1, angle_2)
                if degree_1 not in (0, 180) and degree_2 not in (0, 180):
                    if (angle_1 < angle_2) and angle_1 > 0:
                        two_road_width = 12 / math.sin(angle_1)
                    if (angle_1 >= angle_2) and angle_2 > 0:
                        two_road_width = 12 / math.sin(angle_2)
                if degree_1 in (0, 180) and degree_2 in (0, 180):
                    two_road_width = 12
                if degree_1 in (0, 180) and degree_2 not in (0, 180):
                    two_road_width = 12 / math.sin(angle_2)
                if degree_1 not in (0, 180) and degree_2 in (0, 180):
                    two_road_width = 12 / math.sin(angle_1)
                # calculate turning lane width
                if yle != 0:
                    turn_lane_width = 12 * zle / abs(yle)
                if yle == 0:
                    turn_lane_width = 12
                if lane_side == 0:
                    turning_point[0].append(inter1_loc[0] + v_road_width / 2)
                    turning_point[0].append(inter1_loc[1] - two_road_width)
                    turning_point[1].append(inter1_loc[0] + turn_lane_width / 2)
                    turning_point[1].append(inter1_loc[1] + two_road_width)
                if lane_side == 2:
                    turning_point[0].append(inter1_loc[0] - v_road_width / 2)
                    turning_point[0].append(inter1_loc[0] + two_road_width)
                    turning_point[1].append(inter1_loc[1] - turn_lane_width / 2)
                    turning_point[1].append(inter1_loc[1] - two_road_width)
            if lane_side in (1, 3):
                road_id_1 = inter1_roads[0].road_id
                road_id_2 = inter1_roads[2].road_id
#                print("in lane_side 1 or 3, straight 1", road_id_1, road_id_2)
                for road_x in self.world.infrastructure.roads:
                    if road_id_1 == road_x.road_id:
                        # print("road_id_1 = road_x in lane_side 1 or 3, straight 1", road_id_1)
                        for r in range(2):
                            try:
                                ends_coord_1.append((road_x.ends[r][0], road_x.ends[r][1]))
                            except TypeError:
                                ends_coord_1.append(road_x.ends[r].loc)
#                        print("straight 1, rd 1: lane_side 1 or 3", ends_coord_1)
                        sides_road_loc_1.append((ends_coord_1[0][0] + ends_coord_1[1][0]) / 2)
                        sides_road_loc_1.append((ends_coord_1[1][0] + ends_coord_1[1][1]) / 2)
                        # sides_road_loc_1[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_1[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_1 = abs(self.get_side_road(road_id_1).lane_direction(sides_road_loc_1))
                    if road_id_2 == road_x.road_id:
                        for r in range(2):
                            try:
                                ends_coord_2.append((road_x.ends[r][0], road_x.ends[r][1]))
                            except TypeError:
                                ends_coord_2.append(road_x.ends[r].loc)
#                        print("straight 1, rd 2: lane_side 1 or 3 ends_2", ends_coord_2)
                        sides_road_loc_2.append((ends_coord_2[0][0] + ends_coord_2[1][0]) / 2)
                        sides_road_loc_2.append((ends_coord_2[1][0] + ends_coord_2[1][1]) / 2)
                        # sides_road_loc_2[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_2[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_2 = abs(self.get_side_road(road_id_2).lane_direction(sides_road_loc_2))
                angle_1 = math.radians(abs(degree_1))
                angle_2 = math.radians(abs(degree_2))
                if degree_1 > 90:
                    angle_1 = math.radians(abs(degree_1 - 180))
                if degree_2 > 90:
                    angle_2 = math.radians(abs(degree_2 - 180))
#                print("degree_1 and degree_2", (degree_1), (degree_2))
#                print("angle_1 and angle_2 ", angle_1, angle_2)
                if degree_1 != 90 and degree_2 != 90:
                    if (angle_1 < angle_2) and angle_1 > 0:
                        two_road_width = 12 / math.sin(angle_1)
                    if (angle_1 >= angle_2) and angle_2 > 0:
                        two_road_width = 12 / math.sin(angle_2)
                if degree_1 == 90 and degree_2 == 90:
                    two_road_width = 12
                if degree_1 == 90 and degree_2 != 90:
                    two_road_width = 12 / math.sin(angle_2)
                if degree_1 != 90 and degree_2 == 90:
                    two_road_width = 12 / math.sin(angle_1)
                # calculate turning lane width
                if xle != 0:
                    turn_lane_width = 12 * zle / abs(xle)
                if xle == 0:
                    turn_lane_width = 12
                if lane_side == 1:
                    turning_point[0].append(inter1_loc[0] - two_road_width)
                    turning_point[0].append(inter1_loc[1] - v_road_width / 2)
                    turning_point[1].append(inter1_loc[0] + two_road_width)
                    turning_point[1].append(inter1_loc[1] - turn_lane_width / 2)
                if lane_side == 3:
                    turning_point[0].append(inter1_loc[0] + two_road_width)
                    turning_point[0].append(inter1_loc[1] + v_road_width / 2)
                    turning_point[1].append(inter1_loc[0] - two_road_width)
                    turning_point[1].append(inter1_loc[1] + turn_lane_width / 2)
#                print(inter1_loc, two_road_width, v_road_width, turn_lane_width)
        return turning_point


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
        if not self.plan[1] or self.at_intersection():
            source = self.world.infrastructure.closest_intersection(self.loc)
            for road in self.world.infrastructure.roads:
                if road.has_point(self.plan[0]):
                    on_road = road
            for end in on_road.ends:
                if end in self.world.infrastructure.intersections:
                    dest = end
            self.plan[1] = self.dijkstras(source, dest)

        if len(self.plan[1]) > 1:
            next_inter = self.plan[1][1]
            curr_inter = self.plan[1][0]
            connect = set(next_inter.roads).intersection(curr_inter.roads)
            self.next_road = connect
        else:
            #set flag to show that it is last turn
            final = 1
            for r in enumerate(self.world.infrastructure.closest_intersection(self.loc).roads):
                if r is None:
                    continue
                    if r.has_point(self.plan[0]):
                        self.next_road = r

        if self.following:
            if self.dist_to(self.in_front.loc) < 30:
                if self.in_front.veloc[0] == 0:
                    self.veloc[0] = 0
                    self.accel = 0
                else:
                    self.accel = self.decide_accel()
                    self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)

        if not self.during_turn:
#            self.veloc[1] = self.get_road().lane_direction(self.loc)
            self.accel = self.decide_accel()
            self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)
            for count, r in enumerate(self.world.infrastructure.closest_intersection(self.loc).roads):
                if r is None:
                    continue
                if self.get_road().road_id == r.road_id:
                    self.curr_road = count
            index = self.curr_road

        points = [[(-6, 12), (6, 12)],[(12, 6), (12, -6)],[(6, -12),(-6, -12)],[(-12, -6),(-12, 6)]]


        if self.during_turn:
            x = self.world.infrastructure.closest_intersection(self.loc).loc[0] + points[(self.curr_road + self.turn + 1) % 4][1][0]
            y = self.world.infrastructure.closest_intersection(self.loc).loc[1] + points[(self.curr_road + self.turn + 1) % 4][1][1]
            turning_pt = (x,y)
            if self.dist_to(turning_pt) < 30:
                self.loc = turning_pt
                if self.turn_dir() == 0:
                    new_direct = self.veloc[1] + 45
                    if new_direct > 180:
                        new_direct -= 360
                    self.veloc[1] = new_direct
                if self.turn_dir() == 2:
                    new_direct = self.veloc[1] - 45
                    if new_direct < -180:
                        new_direct += 360
                    self.veloc[1] = new_direct
            self.accel = self.decide_accel()
            self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)
            self.during_turn = False
            self.curr_road = self.next_road.pop()
            index = self.curr_road.road_id

        if self.dist_to(self.plan[1][0].calc_stop_line(index)) < 10:
            #if light is green
            if self.can_go(self.turn_dir()):
                self.turn = self.turn_dir()
                x = self.world.infrastructure.closest_intersection(self.loc).loc[0] + points[index][0][0]
                y = self.world.infrastructure.closest_intersection(self.loc).loc[1] + points[index][0][1]
                turning_pt = (x,y)
                if self.turn_dir != 1 and self.dist_to(turning_pt) <= 10 and not self.during_turn:
                    self.loc = turning_pt
                    self.during_turn = True
                    new_direct = 0
                    if self.turn_dir() == 0:
                        new_direct = self.veloc[1] + 45
                        if new_direct > 180:
                            new_direct -= 360
                        self.veloc[1] = new_direct
                    if self.turn_dir() == 2:
                        new_direct = self.veloc[1] - 45
                    if new_direct < -180:
                        new_direct += 360
                    self.veloc[1] = new_direct
                self.accel = self.decide_accel()
                self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)
#                if light is red
            else:
                # if light is red
                if not self.following:
                    self.veloc[0] = 0
                    self.accel = 0
                    self.loc = self.world.infrastructure.closest_intersection(self.loc).calc_stop_line(index)

        self.update_coords()


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
        if not self.plan[1]:
            source = self.world.infrastructure.closest_intersection(self.loc)
            for road in self.world.infrastructure.roads:
                if road.has_point(self.plan[0]):
                    on_road = road
            for end in on_road.ends:
                if end in self.world.infrastructure.intersections:
                    dest = end
            self.plan[1] = self.dijkstras(source, dest)
        
        if len(self.plan[1]) > 1:
            next_inter = self.plan[1][1]
            curr_inter = self.plan[1][0]
            connect = set(next_inter.roads).intersection(curr_inter.roads)
            self.next_road = connect
        else:
            #set flag to show that it is last turn
            final = 1
            for r in enumerate(self.world.infrastructure.closest_intersection(self.loc).roads):
                if r is None:
                    continue
                    if r.has_point(self.plan[0]):
                        self.next_road = r
    
        if self.following:
            if self.dist_to(self.in_front.loc) < 30:
                if self.in_front.veloc[0] == 0:
                    self.veloc[0] = 0
                    self.accel = 0
                else:
                    self.accel = self.decide_accel()
                    self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)

        if not self.during_turn:
            #            self.veloc[1] = self.get_road().lane_direction(self.loc)
            self.accel = self.decide_accel()
            self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)
            for count, r in enumerate(self.world.infrastructure.closest_intersection(self.loc).roads):
                if r is None:
                    continue
                if self.get_road().road_id == r.road_id:
                        self.curr_road = count
            index = self.curr_road
        
        points = [[(-6, 12), (6, 12)],[(12, 6), (12, -6)],[(6, -12),(-6, -12)],[(-12, -6),(-12, 6)]]
        
        if self.during_turn:
            x = self.world.infrastructure.closest_intersection(self.loc).loc[0] + points[(self.curr_road + self.turn + 1) % 4][1][0]
            y = self.world.infrastructure.closest_intersection(self.loc).loc[1] + points[(self.curr_road + self.turn + 1) % 4][1][1]
            turning_pt = (x,y)
            if self.dist_to(turning_pt) < 30:
                self.loc = turning_pt
                if self.turn_dir() == 0:
                    new_direct = self.veloc[1] + 45
                    if new_direct > 180:
                        new_direct -= 360
                    self.veloc[1] = new_direct
                if self.turn_dir() == 2:
                    new_direct = self.veloc[1] - 45
                    if new_direct < -180:
                        new_direct += 360
                    self.veloc[1] = new_direct
            self.accel = self.decide_accel()
            self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)
            self.during_turn = False
            self.curr_road = self.next_road.pop()
            index = self.curr_road.road_id

        if self.dist_to(self.plan[1][0].calc_stop_line(index)) < 10:
            #if light is green
            if self.can_go(self.turn_dir()):
                self.turn = self.turn_dir()
                x = self.world.infrastructure.closest_intersection(self.loc).loc[0] + points[index][0][0]
                y = self.world.infrastructure.closest_intersection(self.loc).loc[1] + points[index][0][1]
                turning_pt = (x,y)
                if self.turn_dir != 1 and self.dist_to(turning_pt) <= 10 and not self.during_turn:
                    self.loc = turning_pt
                    self.during_turn = True
                    new_direct = 0
                    if self.turn_dir() == 0:
                        new_direct = self.veloc[1] + 45
                        if new_direct > 180:
                            new_direct -= 360
                        self.veloc[1] = new_direct
                    if self.turn_dir() == 2:
                        new_direct = self.veloc[1] - 45
                    if new_direct < -180:
                        new_direct += 360
                    self.veloc[1] = new_direct
                self.accel = self.decide_accel()
                self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)
            #                if light is red
            else:
                # if light is red
                if not self.following:
                    self.veloc[0] = 0
                    self.accel = 0
                    self.loc = self.world.infrastructure.closest_intersection(self.loc).calc_stop_line(index)

        self.update_coords()

