import numpy as np
import random

class Marker:
    def __init__(self, startLocation, direction):
        self.currLocation = np.array(startLocation)
        self.prevLocation = np.array(startLocation)
        self.direction = np.array(direction)
        self.moveSpeed = 0.025
        self.finished = False
        self.normal = np.array([0,1,0])
        
    def propagate(self):
        rng = random.uniform(-self.moveSpeed,self.moveSpeed)
        
        # Ensure energy conservation
        forwardSpeed = (1 - abs(rng)) * self.moveSpeed * self.direction
        normalSpeed = rng * self.moveSpeed * self.normal
        
        self.prevLocation = np.copy(self.currLocation)
        self.currLocation = self.currLocation + forwardSpeed + normalSpeed