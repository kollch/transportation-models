#!/usr/bin/env python
"""This script prompts a user to enter a message to encode or decode
using a classic Caeser shift substitution (3 letter shift)"""

import random

class Vehicle:
    """Includes CAVs and HVs"""
    def __init__(self, length, location, destination, speed, accel):
        self.length = length
        self.location = location
        self.destination = destination
        self.speed = speed
        self.accel = accel

    def decide_move(self):
        """Determines move. Required to be implemented in CAV and HV"""
        raise NotImplementedError

#pep8 required 2 public methods?
    def decide_other_maybe(self):
        raise NotImplementedError

class CAV(Vehicle):
    """Connected autonomous vehicles
    Connect, decide action, move
    """
    def connect(self, cavs_in_range, current_location):
        """Gets info from CAVs within range"""
        self.location = current_location

        for cav in cavs_in_range(current_location, 3000):
            info = cav.give_info() ##?????
        return info  ##??????????

    def give_info(self, location, speed, accel):
        self.location = location
        self.speed = speed
        self.accel = accel

        return [location, speed, accel]

    def react_time():
        """Randomly-generated time it will take to react - for CAVs
        this should be instantaneous because the timesteps in this
        program should account for the small amount of reaction time
        CAVs have
        """
        ##sampleNo = 1  """set the samplenumber as 1, not sure for average number and sigma"""
        mean = 0.01
        sigma = 0.2
        r_time = random.gauss(mean, sigma)

        #"""r_time is randomly number but sometimes it will has negative number"""

        while r_time[0] < 0:
            r_time = random.gauss(mean, sigma)

        return r_time

    def decide_move(self):
        """Uses available information and determines move"""
        return 0

    #pep8 required 2 public methods? we can delete this function
    def decide_other_maybe(self):
        return 0

class HV(Vehicle):
    """Human-driven vehicles
    Decide action, move
    """
    def react_time():
        """Randomly-generated time it will take to react"""

        #sampleNo = 1;  """set the samplenumber as 1"""
        mean = 0.5
        sigma = 1
        r_time = random.gauss(mean, sigma)

        #"""r_time is randomly number but sometimes it will has negative number"""

        while r_time[0] < 0:
            r_time = random.gauss(mean, sigma)

        return r_time

    def decide_move(self):
        """Looks in immediate vicinity and determines move"""
        return 0
        #######
    #pep8 required 2 public methods? we can delete this function
    def decide_other_maybe(self):
        return 0
