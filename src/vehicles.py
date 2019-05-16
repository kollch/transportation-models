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
        self.following = None
        self.during_turn = False
        self.turn = self.get_turn()
        self.road = None
        self.curr_road = None
        self.next_road = None

    def angle(self, p):
        """Compute angle from vehicle to location or object"""
        try:
            result = math.atan2(p.loc[1] - self.loc[1], p.loc[0] - self.loc[0])
        except AttributeError:
            result = math.atan2(p[1] - self.loc[1], p[0] - self.loc[0])
        return convert(result, 'rad', 'deg')

    def at_dest(self):
        dest = self.plan[0]
        loc = self.loc
        # 9 is a safe value in case of overshooting at 60 mph
        if abs(dest[0] - loc[0]) < 9 and abs(dest[1] - loc[1]) < 9:
            return True
        return False

    def decide_move(self):
        """Determines move. Required to be implemented in CAV and HV"""
        raise NotImplementedError

    def at_inter(self):
        """Determines if vehicle is at an intersection;
        based on proximity to center of intersection

        12 is the width of a lane
        """
        # Account for the width of lanes and length of the vehicle
        inter_bound = 12 + self.size[0] / 2
        for inter in self.world.infrastructure.intersections:
            if (abs(inter.loc[0] - self.loc[0]) < inter_bound
                    and abs(inter.loc[1] - self.loc[1]) < inter_bound):
                return True
        return False

    def get_road(self):
        """Returns road vehicle is currently on"""
        for road in self.world.infrastructure.roads:
            if self in road.vehicles_on:
                return road
        return None

    def dist_to(self, p):
        """Returns the distance between the vehicle and a given
        location"""
        try:
            return math.hypot(p.loc[0] - self.loc[0], p.loc[1] - self.loc[1])
        except AttributeError:
            return math.hypot(p[0] - self.loc[0], p[1] - self.loc[1])

    def can_see(self, cavs, hvs):
        """Returns a list of everything that the vehicle can see"""
        in_vision = []
        for vehicle in sorted(cavs + hvs, key=lambda v: self.dist_to(v.loc)):
            if vehicle is self:
                continue
            angle = vehicle.angle_edges(self)
            # Convert to radians
            for i, a in enumerate(angle):
                angle[i] = convert(a, 'deg', 'rad')

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
        direction = convert(self.veloc[1], 'deg', 'rad')
        lsin = self.size[0] / 2 * math.sin(direction)
        lcos = self.size[0] / 2 * math.cos(direction)
        wsin = self.size[1] / 2 * math.sin(direction)
        wcos = self.size[1] / 2 * math.cos(direction)
        points = [(self.loc[0] + lcos + wsin, self.loc[1] + lsin - wcos),
                  (self.loc[0] - lcos - wsin, self.loc[1] + wcos - lsin),
                  (self.loc[0] + lcos - wsin, self.loc[1] + lsin + wcos),
                  (self.loc[0] + wsin - lcos, self.loc[1] - lsin - wcos)]
        angles = [vehicle.angle(i) for i in points]
        min_angle = min(angles)
        max_angle = max(angles)
        # Check if wrapping around pi = -pi
        if min_angle < -90 and max_angle > 90:
            return [max_angle, min_angle]
        return [min_angle, max_angle]

    def point_no_return(self):
        """Point of no return when approaching an intersection;
        don't have to worry about yellow lights because the model
        supports instant deceleration

        Returns distance to intersection in feet
        """
        # b and v_0 are the same ones that are defined in idm_accel()
        b = 1.67
        v_0 = convert(60, 'mph', 'm/s')
        return convert(v_0 ** 2 / (2 * b), 'm', 'ft')

    def get_next_inter(self):
        """Get next intersection the vehicle is approaching;
        return None if there aren't any
        """
        if not self.plan[1]:
            # No intersections remaining
            return None
        next_inter = self.plan[1][0]
        # Verify that the intersection is connected to our road
        assert any(r.road_id == self.road.road_id for r in next_inter.roads)
        return next_inter

    def get_following(self):
        """Find the vehicle or intersection in front, None otherwise"""
        visible = self.can_see(self.world.cavs, self.world.hvs)
        visible.sort(key=lambda v: abs(self.veloc[1] - self.angle(v)))
        if (visible
                and self.road.road_id == visible[0].road.road_id
                and abs(self.veloc[1] - self.angle(visible[0])) < 1
                and abs(self.veloc[1] - visible[0].veloc[1]) < 45):
            # On the same road, ahead, and facing the same direction
            return visible[0]

        # No vehicles ahead. Now check for intersection
        next_inter = self.get_next_inter()
        if next_inter is None:
            return None
        if (self.dist_to(next_inter) < self.point_no_return()
                and not self.at_inter()
                and not next_inter.is_green(self)):
            # Past the point of no return and light is red
            return next_inter
        return None

    def decide_accel(self):
        """Decides acceleration based on car following or approach to
        intersections
        """
        v = self.veloc[0]
        a_1 = self.following
        if a_1 is None:
            return idm_accel(v)
        try:
            d_v = v - self.following.veloc[0]
        except AttributeError:
            # Intersection instead of a vehicle
            s = math.sqrt(self.dist_to(a_1) ** 2 - 36) - 12 - self.size[0] / 2
            if s == 0:
                s = 0.01
            return idm_accel(v, s_ft=s)
        s = self.dist_to(a_1) - self.size[0] / 2 - a_1.size[0] / 2
        if s == 0:
            s = 0.01
        return idm_accel(v, d_v, s)

    def can_go(self):
        """Returns True if turn is allowed by intersection,
        False if not.
        """
        next_inter = self.get_next_inter()
        index = [r.road_id for r in next_inter.roads].index(self.road.road_id)
        return next_inter.roads_list[index][self.turn]

    def update_speed(self):
        self.veloc[0] = self.veloc[0] + self.accel * 3 / 44
        # Vehicle stopped
        if self.veloc[0] < 0:
            self.veloc[0] = 0

    def update_coords(self):
        """Updates location coordinates depending on passed time and
        direction
        """
        movement = self.veloc[0] * 528 / 3600
        direction = convert(self.veloc[1], 'deg', 'rad')
        d_x = movement * math.cos(direction)
        d_y = movement * math.sin(direction)
        self.loc = (round(d_x + self.loc[0]), round(d_y + self.loc[1]))

    def get_turn(self):
        """Returns 0 for left turn, 1 for straight, 2 for right turn"""
        if not self.plan[1]:
            return 1
        road_ids = [r.road_id for r in self.plan[1][0].roads]
        curr_index = road_ids.index(self.road.road_id)
        for i, road in enumerate(self.plan[1][0].roads):
            if road is None or i == curr_index:
                continue
            if road.on_path(self):
                return (i + 4 - curr_index) % 4 - 1
        raise RuntimeError("Cannot find a road after intersection")

    def turn_to_road(self):
        """Returns the road we will turn onto"""
        if not self.plan[1]:
            return None
        for road in self.plan[1][0].roads:
            if road.on_path(self) and road.road_id != self.road.road_id:
                return road
        raise RuntimeError("Cannot find a road to turn onto")

    def turning_point(self):
        """This function used to find the turning lane middle point
        """
        # turning point
        turning_point = [[], []]
        # find intersection location and id
        inter1_id = 0
        inter2_id = 0
        v_road_id = 0
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
        v_road_id = self.road.road_id
        inter1_loc = self.plan[1][0].loc
        # turn left or right need to find next intersection id
        for i in range(len(self.plan[1])):
            if inter1_loc == self.plan[1][i].loc:
                inter2_loc = self.plan[1][i + 1].loc
        for intersection in self.world.infrastructure.intersections:
            if inter2_loc == intersection.loc:
                inter2_id = intersection.intersection_id
        # find two intersection roads list
        #print(inter1_id)
        for intersection in self.world.infrastructure.intersections:
            #print(intersection.intersection_id)
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
            #print("v_roadId: ", v_road_id, inter1_roads[i])
            if v_road_id == inter1_roads[i].road_id:
                # for r in range(2):
                #     try:
                #         ends_coord_1.append((road.ends[r][0], road.ends[r][1]))
                #     except TypeError:
                #         ends_coord_1.append(road.ends[r].loc)
                #print("v_roadId: ", v_road_id, inter1_roads[i])
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
        #print("turning，straight，into side，out side：", turn_d, straight, ori_lane_side, lane_side)
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
                #print("in lane_side 0 or 2, straight 0", road_id_1, road_id_2)
                for road in self.world.infrastructure.roads:
                    if road_id_1 == road.road_id:
                        for r in range(2):
                            try:
                                ends_coord_1.append((road.ends[r][0], road.ends[r][1]))
                            except TypeError:
                                ends_coord_1.append(road.ends[r].loc)
                        #print("straight 0, rd 1: lane_side 0 or 2", ends_coord_1)
                        sides_road_loc_1.append((ends_coord_1[0][0] + ends_coord_1[1][0]) / 2)
                        sides_road_loc_1.append((ends_coord_1[1][0] + ends_coord_1[1][1]) / 2)
                        # sides_road_loc_1[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_1[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_1 = abs(self.road_from_id(road_id_1).lane_direction(sides_road_loc_1))
                    if road_id_2 == road.road_id:
                        for r in range(2):
                            try:
                                ends_coord_2.append((road.ends[r][0], road.ends[r][1]))
                            except TypeError:
                                ends_coord_2.append(road.ends[r].loc)
                        #print("straight 0, rd 2: lane_side 0 or 2", ends_coord_2)
                        sides_road_loc_2.append((ends_coord_2[0][0] + ends_coord_2[1][0]) / 2)
                        sides_road_loc_2.append((ends_coord_2[1][0] + ends_coord_2[1][1]) / 2)
                        # sides_road_loc_2[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_2[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_2 = abs(self.road_from_id(road_id_2).lane_direction(sides_road_loc_2))
                angle_1 = math.radians(abs(degree_1))
                angle_2 = math.radians(abs(degree_2))
                if 0 < degree_1 < 180:
                    if degree_1 > 90:
                        angle_1 = math.radians(abs(degree_1 - 180))
                if 0 < degree_2 < 180:
                    if degree_2 > 90:
                        angle_2 = math.radians(abs(degree_2 - 180))
                #print("degree_1 and degree_2", (degree_1), (degree_2))
                #print("angle_1 and angle_2 ", angle_1, angle_2)
                if degree_1 not in (0, 180) and degree_2 not in (0, 180):
                    if 0 < angle_1 < angle_2:
                        ori_lane_width = 12 / math.sin(angle_1)
                    if angle_1 >= angle_2 > 0:
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
                    #print("turn left")
                    if lane_side == 0:
                        turning_point[1].append(inter1_loc[0] + turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] + ori_lane_width)
                    if lane_side == 2:
                        turning_point[1].append(inter1_loc[0] - turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] - ori_lane_width)
                if turn_d == 1:
                    #print("turn right")
                    if lane_side == 0:
                        turning_point[1].append(inter1_loc[0] + turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] + ori_lane_width)
                    if lane_side == 2:
                        turning_point[1].append(inter1_loc[0] - turn_lane_width / 2)
                        turning_point[1].append(inter1_loc[1] - ori_lane_width)
                #print(turning_point)
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
                #print("in lane_side 1 or 3, straight 1", road_id_1, road_id_2)
                for road in self.world.infrastructure.roads:
                    if road_id_1 == road.road_id:
                        for r in range(2):
                            try:
                                ends_coord_1.append((road.ends[r][0], road.ends[r][1]))
                            except TypeError:
                                ends_coord_1.append(road.ends[r].loc)
                        #print("straight 0, rd 1: lane_side 1 or 3", ends_coord_1)
                        sides_road_loc_1.append((ends_coord_1[0][0] + ends_coord_1[1][0]) / 2)
                        sides_road_loc_1.append((ends_coord_1[1][0] + ends_coord_1[1][1]) / 2)
                        # sides_road_loc_1[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_1[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_1 = abs(self.road_from_id(road_id_1).lane_direction(sides_road_loc_1))
                    if road_id_2 == road.road_id:
                        for r in range(2):
                            try:
                                ends_coord_2.append((road.ends[r][0], road.ends[r][1]))
                            except TypeError:
                                ends_coord_2.append(road.ends[r].loc)
                        #print("straight 0, rd 2: lane_side 1 or 3", ends_coord_2)
                        sides_road_loc_1.append((ends_coord_2[0][0] + ends_coord_2[1][0]) / 2)
                        sides_road_loc_1.append((ends_coord_2[1][0] + ends_coord_2[1][1]) / 2)
                        # sides_road_loc_2[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_2[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_2 = abs(self.road_from_id(road_id_2).lane_direction(sides_road_loc_2))
                angle_1 = math.radians(abs(degree_1))
                angle_2 = math.radians(abs(degree_2))
                if degree_1 > 90:
                    angle_1 = math.radians(abs(degree_1 - 180))
                if degree_2 > 90:
                    angle_2 = math.radians(abs(degree_2 - 180))
                #print("degree_1 and degree_2", (degree_1), (degree_2))
                #print("angle_1 and angle_2 ", angle_1, angle_2)
                if degree_1 != 90 and degree_2 != 90:
                    if 0 < angle_1 < angle_2:
                        ori_lane_width = 12 / math.sin(angle_1)
                    if angle_1 >= angle_2 > 0:
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
                    #print("v_road_ends: in straight 1", ends_coord_v)
                    v_road_mid.append((ends_coord_v[0][0] + ends_coord_v[1][0]) / 2)
                    v_road_mid.append((ends_coord_v[1][0] + ends_coord_v[1][1]) / 2)
                    degree_v_road = abs(self.road_from_id(v_road_id).lane_direction(v_road_mid))
                    angle_v_rd = math.radians(abs(degree_v_road - 90))
                    if degree_v_road not in (0, 90):
                        v_road_width = 12 / math.sin(angle_v_rd)
                    else:
                        v_road_width = 12
            if lane_side in (0, 2):
                road_id_1 = inter1_roads[1].road_id
                road_id_2 = inter1_roads[3].road_id
                #print("in lane_side 0 or 2, straight 1", road_id_1, road_id_2)
                for road_xx in self.world.infrastructure.roads:
                    if road_id_1 == road_xx.road_id:
                        for r in range(2):
                            try:
                                ends_coord_1.append((road_xx.ends[r][0], road_xx.ends[r][1]))
                            except TypeError:
                                ends_coord_1.append(road_xx.ends[r].loc)
                        #print("straight 1, rd 1: lane_side 0 or 2", ends_coord_1)
                        sides_road_loc_1.append((ends_coord_1[0][0] + ends_coord_1[1][0]) / 2)
                        sides_road_loc_1.append((ends_coord_1[1][0] + ends_coord_1[1][1]) / 2)
                        # sides_road_loc_1[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_1[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_1 = abs(self.road_from_id(road_id_1).lane_direction(sides_road_loc_1))
                    if road_id_2 == road_xx.road_id:
                        for r in range(2):
                            try:
                                ends_coord_2.append((road.ends[r][0], road.ends[r][1]))
                            except TypeError:
                                ends_coord_2.append(road.ends[r].loc)
                        #print("straight 1, rd 2: lane_side 0 or 2", ends_coord_2)
                        sides_road_loc_2.append((ends_coord_2[0][0] + ends_coord_2[1][0]) / 2)
                        sides_road_loc_2.append((ends_coord_2[1][0] + ends_coord_2[1][1]) / 2)
                        # sides_road_loc_2[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_2[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_2 = abs(self.road_from_id(road_id_2).lane_direction(sides_road_loc_2))
                angle_1 = math.radians(abs(degree_1))
                angle_2 = math.radians(abs(degree_2))
                if 0 < degree_1 < 180:
                    if degree_1 > 90:
                        angle_1 = math.radians(abs(degree_1 - 180))
                if 0 < degree_2 < 180:
                    if degree_2 > 90:
                        angle_2 = math.radians(abs(degree_2 - 180))
                #print("degree_1 and degree_2", (degree_1), (degree_2))
                #print("angle_1 and angle_2 ", angle_1, angle_2)
                if degree_1 not in (0, 180) and degree_2 not in (0, 180):
                    if 0 < angle_1 < angle_2:
                        two_road_width = 12 / math.sin(angle_1)
                    if angle_1 >= angle_2 > 0:
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
                #print("in lane_side 1 or 3, straight 1", road_id_1, road_id_2)
                for road_x in self.world.infrastructure.roads:
                    if road_id_1 == road_x.road_id:
                        # print("road_id_1 = road_x in lane_side 1 or 3, straight 1", road_id_1)
                        for r in range(2):
                            try:
                                ends_coord_1.append((road_x.ends[r][0], road_x.ends[r][1]))
                            except TypeError:
                                ends_coord_1.append(road_x.ends[r].loc)
                        #print("straight 1, rd 1: lane_side 1 or 3", ends_coord_1)
                        sides_road_loc_1.append((ends_coord_1[0][0] + ends_coord_1[1][0]) / 2)
                        sides_road_loc_1.append((ends_coord_1[1][0] + ends_coord_1[1][1]) / 2)
                        # sides_road_loc_1[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_1[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_1 = abs(self.road_from_id(road_id_1).lane_direction(sides_road_loc_1))
                    if road_id_2 == road_x.road_id:
                        for r in range(2):
                            try:
                                ends_coord_2.append((road_x.ends[r][0], road_x.ends[r][1]))
                            except TypeError:
                                ends_coord_2.append(road_x.ends[r].loc)
                        #print("straight 1, rd 2: lane_side 1 or 3 ends_2", ends_coord_2)
                        sides_road_loc_2.append((ends_coord_2[0][0] + ends_coord_2[1][0]) / 2)
                        sides_road_loc_2.append((ends_coord_2[1][0] + ends_coord_2[1][1]) / 2)
                        # sides_road_loc_2[0] = (road.ends[0][0] + road.ends[1][0]) / 2
                        # sides_road_loc_2[1] = (road.ends[0][1] + road.ends[1][1]) / 2
                        degree_2 = abs(self.road_from_id(road_id_2).lane_direction(sides_road_loc_2))
                angle_1 = math.radians(abs(degree_1))
                angle_2 = math.radians(abs(degree_2))
                if degree_1 > 90:
                    angle_1 = math.radians(abs(degree_1 - 180))
                if degree_2 > 90:
                    angle_2 = math.radians(abs(degree_2 - 180))
                #print("degree_1 and degree_2", (degree_1), (degree_2))
                #print("angle_1 and angle_2 ", angle_1, angle_2)
                if degree_1 != 90 and degree_2 != 90:
                    if 0 < angle_1 < angle_2:
                        two_road_width = 12 / math.sin(angle_1)
                    if angle_1 >= angle_2 > 0:
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
                #print(inter1_loc, two_road_width, v_road_width, turn_lane_width)
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
                + "\n Angle: " + str(self.veloc[1])
                + "\n Speed: " + str(self.veloc[0]) + "\n}")

    def __repr__(self):
        return "CAV-" + str(self.vehicle_id)

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
        dest_road = self.world.infrastructure.road_at(self.plan[0])
        dest = dest_road.get_next_inter()
        # Not on the last road and time to initialize plans
        if not self.road.has_point(self.plan[0]) and not self.plan[1]:
            self.plan[1] = self.dijkstras(self.road.get_next_inter(), dest)
        # Get next intersection now that we've initialized our plans
        next_inter = self.get_next_inter()
        # Set vehicle turn direction
        self.turn = self.get_turn()
        # Set what the vehicle is following
        self.following = self.get_following()
        self.accel = self.decide_accel()

        if next_inter is None:
            self.update_speed()
            self.update_coords()
            return
        road_index = next_inter.index(self.road)
        stop_line = next_inter.turn_point(self, self.road, 'input')
        exit_road = self.turn_to_road()
        turn_exit = next_inter.turn_point(self, exit_road, 'output')
        # 9 is a safe overshooting value for traveling at 60 mph
        if self.dist_to(turn_exit) < 9 and not self.at_inter():
            self.loc = turn_exit
            self.veloc[1] = exit_road.lane_direction(self.loc)
            self.road.vehicles_on.remove(self)
            self.road = exit_road
            self.road.vehicles_on.append(self)
            self.plan[1].pop(0)
            self.turn = self.get_turn()
        elif self.dist_to(stop_line) < 9 and not self.at_inter():
            # This is the key difference between CAVs and HVs
            self.plan[1] = self.dijkstras(next_inter, dest)
            self.turn = self.get_turn()
            turn_exit = next_inter.turn_point(self, self.turn_to_road(), 'output')

            if next_inter.is_green(self):
                self.loc = stop_line
                self.veloc[1] = self.angle(turn_exit)

        self.update_speed()
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
                + "\n Angle: " + str(self.veloc[1])
                + "\n Speed: " + str(self.veloc[0]) + "\n}")

    def __repr__(self):
        return "HV-" + str(self.vehicle_id)

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
            for r in enumerate(self.world.infrastructure.closest_intersection(self.loc).roads):
                if r is None:
                    continue
                if r.has_point(self.plan[0]):
                    self.next_road = r

        if self.following is not None:
            if self.dist_to(self.following.loc) < 30:
                if self.following.veloc[0] == 0:
                    self.veloc[0] = 0
                    self.accel = 0
                else:
                    self.accel = self.decide_accel()
                    self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)

        if not self.during_turn:
            #            self.veloc[1] = self.road.lane_direction(self.loc)
            self.accel = self.decide_accel()
            self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)
            for count, r in enumerate(self.world.infrastructure.closest_intersection(self.loc).roads):
                if r is None:
                    continue
                if self.road.road_id == r.road_id:
                    self.curr_road = count
            index = self.curr_road

        points = [[(-6, 12), (6, 12)], [(12, 6), (12, -6)], [(6, -12), (-6, -12)], [(-12, -6), (-12, 6)]]

        if self.during_turn:
            x = self.world.infrastructure.closest_intersection(self.loc).loc[0] + points[(self.curr_road + self.turn + 1) % 4][1][0]
            y = self.world.infrastructure.closest_intersection(self.loc).loc[1] + points[(self.curr_road + self.turn + 1) % 4][1][1]
            turning_pt = (x, y)
            if self.dist_to(turning_pt) < 30:
                self.loc = turning_pt
                if self.turn == 0:
                    new_direct = self.veloc[1] + 45
                    if new_direct > 180:
                        new_direct -= 360
                    self.veloc[1] = new_direct
                if self.turn == 2:
                    new_direct = self.veloc[1] - 45
                    if new_direct < -180:
                        new_direct += 360
                    self.veloc[1] = new_direct
            self.accel = self.decide_accel()
            self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)
            self.during_turn = False
            self.curr_road = self.next_road.pop()
            index = self.curr_road.road_id

        if self.dist_to(self.plan[1][0].turn_point(self, index, 'input')) < 10:
            #if light is green
            if self.can_go():
                self.turn = self.get_turn()
                x = self.world.infrastructure.closest_intersection(self.loc).loc[0] + points[index][0][0]
                y = self.world.infrastructure.closest_intersection(self.loc).loc[1] + points[index][0][1]
                turning_pt = (x, y)
                if self.turn != 1 and self.dist_to(turning_pt) <= 10 and not self.during_turn:
                    self.loc = turning_pt
                    self.during_turn = True
                    new_direct = 0
                    if self.turn == 0:
                        new_direct = self.veloc[1] + 45
                        if new_direct > 180:
                            new_direct -= 360
                        self.veloc[1] = new_direct
                    if self.turn == 2:
                        new_direct = self.veloc[1] - 45
                    if new_direct < -180:
                        new_direct += 360
                    self.veloc[1] = new_direct
                self.accel = self.decide_accel()
                self.veloc[0] = self.veloc[0] + self.accel * (528 / 3600)
            #                if light is red
            else:
                # if light is red
                if self.following is None:
                    self.veloc[0] = 0
                    self.accel = 0
                    self.loc = (0, 0)
                    self.world.infrastructure.closest_intersection(self.loc).turn_point(self, index, 'input')

        self.update_coords()


def idm_accel(v_mph, d_v_mph=None, s_ft=None):
    """IDM car following model.
    Params: v_mph   - velocity (mph)
            d_v_mph - approaching rate (mph)
            s_ft    - net distance (ft)
    One param:      nothing to follow
    v_mph and s_ft: following intersection
    Three params:   following vehicle
    """
    v = convert(v_mph, 'mph', 'm/s')
    d_v = convert(d_v_mph, 'mph', 'm/s')
    s = convert(s_ft, 'ft', 'm')
    # Desired velocity
    v_0 = convert(60, 'mph', 'm/s')
    # Max acceleration (m/s^2)
    a = 0.73
    # Complexity
    delta = 4
    def s_optim(v, d_v):
        """Desired gap"""
        # Minimum spacing
        s_0 = 2
        # Desired time headway (s)
        T = 1.6
        # Comfortable deceleration (m/s^2)
        b = 1.67
        if d_v is None:
            # Following an intersection; set some parameters so that we
            # can guarantee the vehicle stops right at the edge
            s_0 = 0
            T = 0
            d_v = v
        return s_0 + v * T + v * d_v / (2 * math.sqrt(a * b))
    if d_v is None and s is None:
        # Nothing to follow
        result = a * (1 - (v / v_0) ** delta)
        return convert(result, 'm/s^2', 'ft/s^2')
    result = a * (1 - (v / v_0) ** delta - (s_optim(v, d_v) / s) ** 2)
    return convert(result, 'm/s^2', 'ft/s^2')

def convert(val, from_unit, to_unit):
    """Convert from one unit to another"""
    if val is None:
        return val
    # From imperial to metric
    if from_unit == 'ft' and to_unit == 'm':
        return val / 3.281
    if from_unit == 'mph' and to_unit == 'm/s':
        return val / 2.237
    if from_unit == 'ft/s^2' and to_unit == 'm/s^2':
        return val / 3.281
    # From metric to imperial
    if from_unit == 'm' and to_unit == 'ft':
        return val * 3.281
    if from_unit == 'm/s' and to_unit == 'mph':
        return val * 2.237
    if from_unit == 'm/s^2' and to_unit == 'ft/s^2':
        return val * 3.281
    # Angles
    if from_unit == 'deg' and to_unit == 'rad':
        return math.radians(val)
    if from_unit == 'rad' and to_unit == 'deg':
        return math.degrees(val)
    # Unit conversion values not supported
    raise ValueError("Unavailable unit conversion")
