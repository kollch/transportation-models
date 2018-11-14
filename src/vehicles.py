class Vehicle():
    """Includes CAVs and HVs"""
    def __init__(self, length, location, destination):
        self.length = length
        self.location = location
        self.destination = destination

    def decide_move():
        """Determines move. Required to be implemented in CAV and HV"""
        raise NotImplementedError

class CAV(Vehicle):
    """Connected autonomous vehicles
    Connect, decide action, move
    """
    def connect():
        """Gets info from CAVs within range"""
        for CAV in cavs_in_range(current_location, 3000):
            info = CAV.give_info()
        return

    def give_info():
        return [location, speed, accel]

    def react_time():
        """Randomly-generated time it will take to react - for CAVs
        this should be instantaneous because the timesteps in this
        program should account for the small amount of reaction time
        CAVs have
        """
        return 0

    def decide_move():
        """Uses available information and determines move"""
        return

class HV(Vehicle):
    """Human-driven vehicles
    Decide action, move
    """
    def react_time():
        """Randomly-generated time it will take to react"""
        return

    def decide_move():
        """Looks in immediate vicinity and determines move"""
        return
