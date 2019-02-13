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
        #TODO: should use InvisibleHand's cavs_in_range function to determine neraby vehicles,
        # then use that information in dijkstra's to determine next location and update
        # the self.* parameters above.
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

    def decide_move(self):
        """Uses available information and determines move"""
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

    def decide_move(self):
        """Looks in immediate vicinity and determines move"""
        return
