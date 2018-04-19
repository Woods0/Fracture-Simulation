import numpy as np
import random
import math

class Marker:
    def __init__(self, startLocation, direction):
        self.currLocation = np.array(startLocation)
        self.prevLocation = np.array(startLocation)
        self.direction = np.array(direction)
        self.moveSpeed = .095
        self.finished = False
        self.normal = np.array([0.,1.,0.])
        
    def propagate(self, lowToughnessAreas, initCrack):
        rng = 0 if initCrack else random.uniform(.15, 1.)
        
        rng *= self.calcMovementWeight(lowToughnessAreas)
        
        self.prevLocation = np.copy(self.currLocation)
        
        # Ensure energy conservation
        forwardSpeed = self.moveSpeed * self.direction * (1. - abs(rng))
        normalSpeed = rng * self.moveSpeed * self.normal
        
        self.currLocation += forwardSpeed + normalSpeed
        
    def calcMovementWeight(self, lowToughnessAreas):
        deltaY = 1000.
        lowestToughnessArea = 0.
        maxWeight = .67
        maxThreshold = 3.1
        
        for y in lowToughnessAreas:
            if abs(self.currLocation[1] - y) < deltaY:
                lowestToughnessArea = y
                deltaY = abs(self.currLocation[1] - y)
            
        # Ideally we should set the max threshold to be the point of highest toughness between the marker and either
        # the edge of the surface mesh, or the next low toughness area
        maxThreshold = lowestToughnessArea
        
        constant = maxThreshold / (maxThreshold + .35)
        
        # Determined this equation through trial and error
        scalarVal = pow(math.exp(.357 * pow(((constant * deltaY) - maxThreshold), 3.)), math.pi / 10.) + .004
        
        # Clamp value
        scalarVal = min(scalarVal, 1.)
        scalarVal = max(scalarVal, 0.)
        
        weight = maxWeight * scalarVal
        
        if lowestToughnessArea < self.currLocation[1]:
            weight = -weight
                
        return weight
                    