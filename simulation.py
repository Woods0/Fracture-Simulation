import pymesh
import pyassimp
import pyassimp.postprocess as pp
import numpy as np

class Simulation:
    def __init__(self):
        minCorner = np.array([-2.5, -2.5, -2.5])
        maxCorner = np.array([2.5, 2.5, 2.5])
        
        self.box = pymesh.generate_box_mesh(minCorner, maxCorner, num_samples = 2, keep_symmetry=False,subdiv_order=1)
        self.outFile = 'out.obj'
        self.scenes = []
    
    def runSim(self, numSteps = 100):
        radius = 0.001
        
        for i in range(numSteps):
            print("Step {} complete! ({:.2%})".format(i + 1, ((i + 1) / numSteps)))
            
            centre = np.array([0,0,0])
            
            sphere = pymesh.generate_icosphere(radius, centre, refinement_order=4)
            radius += 0.045
            
            ''' 
                Do the boolean operation with the original box. Using the updated box is a HUGE
                performance hit
            '''
            mesh = pymesh.boolean(self.box, sphere, operation="difference", engine="cork")

            pymesh.save_mesh(self.outFile, mesh)
            
            scene = pyassimp.load(self.outFile, 'obj', pp.aiProcess_GenNormals)
            
            self.scenes.append(scene)