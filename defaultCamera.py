import math

class DefaultCamera:
    def __init__(self, w, h, fov):
        self.clipplanenear = 0.001
        self.clipplanefar = 100000.0
        self.aspect = w/h
        self.horizontalfov = fov * math.pi/180
        self.transformation = [[ 0.68, -0.32, 0.65, 7.48],
                               [ 0.73,  0.31, -0.61, -6.51],
                               [-0.01,  0.89,  0.44,  5.34],
                               [ 0.,    0.,    0.,    1.  ]]
        self.lookat = [0.0,0.0,-1.0]

    def __str__(self):
        return "Default camera"