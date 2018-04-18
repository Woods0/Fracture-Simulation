import pymesh
import pyassimp
import pyassimp.postprocess as pp
import numpy as np
import crackMesh as cm

class Simulation:
    def __init__(self):
        minCorner = np.array([-2.5, -2.5, -2.5])
        maxCorner = np.array([2.5, 2.5, 2.5])
        
        self.crack = cm.CrackMesh([0., 0., 0.])
        
        self.mesh = pymesh.generate_box_mesh(minCorner, maxCorner, num_samples = 1, keep_symmetry=False,subdiv_order=1)
        self.outFile = 'out.obj'
        self.scenes = []
        
        # For CSG debug
        self.cubeVtxArray = [[ .1, .1, .1], [-.1, .1, .1], [-.1,-.1, .1], [ .1,-.1, .1],
                   [ .1,-.1,-.1], [ .1, .1,-.1], [-.1, .1,-.1], [-.1,-.1,-.1]]
        self.cubeIdxArray = [[0,1,2], [0,2,3],  [0,3,4], [0,4,5],  [0,5,6], [0,6,1],
              [1,6,7], [1,7,2],  [7,4,3], [7,3,2],  [4,7,6], [4,6,5]]
        
    def runSim(self, numSteps = 25):
#        self.test()
        crackMesh = None
        
        for i in range(numSteps):
            if self.crack.finishedMarkers < len(self.crack.markers):
                self.crack.propagateCrackFront(self.mesh)
                
                crackV, crackF = self.crack.createCrackMesh()
                
                if crackF:    
                    if crackMesh is None:
                        crackMesh = pymesh.form_mesh(np.array(crackV), np.array(crackF))
                    else:
                        newCrackMesh = pymesh.form_mesh(np.array(crackV), np.array(crackF))
                        crackMesh = pymesh.merge_meshes([crackMesh, newCrackMesh])
                else:
                    print("Crack has finished propagating!")
                    break
                
#                self.mesh = pymesh.boolean(self.mesh, crackMesh, operation="difference", engine="igl")

                pymesh.save_mesh(self.outFile, crackMesh)
                
                scene = pyassimp.load(self.outFile, 'obj', pp.aiProcess_GenNormals)
                
                self.scenes.append(scene)
                
                print("Step {} complete! ({:.2%})".format(i + 1, ((i + 1) / numSteps)))
        
    # Test method to verify that CSG issues are related to using crack mesh being a flat 'sheet' or faces are incorrectly created
    def test(self):
        bm = pymesh.form_mesh(np.array(self.cubeVtxArray), np.array(self.cubeIdxArray))
        self.mesh = pymesh.boolean(self.mesh, bm, operation="difference", engine="igl")
        pymesh.save_mesh(self.outFile, self.mesh)
        
        scene = pyassimp.load(self.outFile, 'obj', pp.aiProcess_GenNormals)
        
        self.scenes.append(scene)