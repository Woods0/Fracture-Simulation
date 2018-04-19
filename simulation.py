import pymesh
import pyassimp
import pyassimp.postprocess as pp
import numpy as np
import crackMesh as cm

class Simulation:
    def __init__(self):
        self.min = -5.5
        self.max = 5.5
        minCorner = np.array([self.min, self.min, self.min])
        maxCorner = np.array([self.max, self.max, self.max])
        
        self.crack = cm.CrackMesh([0., -0.55, 0.])
        
        self.box = pymesh.generate_box_mesh(minCorner, maxCorner, num_samples = 1, keep_symmetry=False,subdiv_order=1)
        self.outFile = 'out.obj'
        self.scenes = []
        
        # Setup areas where material toughness is lower so that one is very slightly closer to the crack 
        # than the other, to demonstrate that the crack will favour one over the other
        self.lowToughnessAreas = [self.max - 3.5, self.min - 4., 0.25]
    
    ''' 
    Runs the for loop for the simulation. Terminates once max number of steps has been reached, or all markers have
    intersected with a non-parallel surface.
        1. Propagates the crack front 
        2. Creates the corresponding crack mesh
        3. Uses CSG to merge the crack with the initial object mesh 
        4. Finally converts to a PyAssimp mesh so it can be rendered with OpenGL
    '''
    def runSim(self, numSteps = 25):
        crackMesh = None
        initCrack = True

        for i in range(numSteps):
            if self.crack.finishedMarkers < len(self.crack.markers):
                self.crack.propagateCrackFront(self.box, self.lowToughnessAreas, initCrack)
                initCrack = False
                
                crackV, crackF = self.crack.createCrackMesh()
                
                if crackF:    
                    crackMesh = self.processCrackMesh(crackV, crackF, crackMesh)
                
#                mesh = pymesh.boolean(self.box, crackMesh, operation="difference", engine="cork")

                self.convertPyMeshToPyAssimp(crackMesh)
                
                print("Step {} complete! ({:.2%})".format(i + 1, ((i + 1) / numSteps)))
            else:
                print("Crack has finished propagating!")
                break
                
                
    # Write the PyMesh mesh as an .obj file, then read it back in with PyAssimp and store the resulting
    # scene in a list
    def convertPyMeshToPyAssimp(self, crackMesh):
        pymesh.save_mesh(self.outFile, crackMesh)
                
        scene = pyassimp.load(self.outFile, 'obj', pp.aiProcess_GenNormals)
        
        self.scenes.append(scene)
        
    # Clean up the initial crack mesh by removing duplicate vertices/faces and degenerate triangles
    # Then create the corresponding PyMesh mesh and return it
    def processCrackMesh(self, crackV, crackF, crackMesh):
        crackV, crackF, info = pymesh.remove_duplicated_vertices_raw(crackV, crackF)
        crackV, crackF, info = pymesh.remove_duplicated_faces_raw(crackV, crackF)
        crackV, crackF, info = pymesh.remove_degenerated_triangles_raw(crackV, crackF)
        
        if crackMesh is None:
            crackMesh = pymesh.form_mesh(np.array(crackV), np.array(crackF))
        else:
            newCrackMesh = pymesh.form_mesh(np.array(crackV), np.array(crackF))
            crackMesh = pymesh.merge_meshes([crackMesh, newCrackMesh])
            
        # Process the crack mesh to clean it up
        crackMesh, info = pymesh.remove_duplicated_vertices(crackMesh)
        crackMesh, info = pymesh.remove_duplicated_faces(crackMesh)
            
        return crackMesh