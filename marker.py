import numpy as np
import random

class Marker:
    def __init__(self, startLocation, direction):
        self.currLocation = np.array(startLocation)
        self.prevLocation = np.array(startLocation)
        self.direction = np.array(direction)
        self.moveSpeed = 0.095
        self.finished = False
        self.normal = np.array([0,1,0])
        
    def propagate(self, lowToughnessAreas, initCrack):
        rng = 0 if initCrack else random.uniform(0., 0.75)
        
        rng *= self.calcMovementWeight(lowToughnessAreas)
        
        self.prevLocation = np.copy(self.currLocation)
        
        # Ensure energy conservation
        forwardSpeed = self.moveSpeed * self.direction * (1. - rng)
        normalSpeed = rng * self.moveSpeed * self.normal
        
        self.currLocation += forwardSpeed + normalSpeed
        
    def calcMovementWeight(self, lowToughnessAreas):
        deltaY = 1000.
        lowestToughnessArea = 0
        
        for y in lowToughnessAreas:
            if abs(self.currLocation[1] - y) < deltaY:
                lowestToughnessArea = y
                
        if lowestToughnessArea == self.currLocation[1]:
            weight = 0.05
        else:
            if lowestToughnessArea < self.currLocation[1]:
                weight = -1.
            else:
                weight = 1.
                
        return weight
                    