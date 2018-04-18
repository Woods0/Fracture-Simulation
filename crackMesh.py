import numpy as np
import marker as m
import pymesh

class CrackMesh:
    def __init__(self, startLocation):
        self.markers = []        
        numMarkers = 60

        # TODO: Figure out how to determine the initial orientation of the crack
        direction = np.array([1.0, 0.0, 0.0])
        
        # Rotate the direction of the vector relative to the initial number of markers being used
        theta = np.radians(360. / numMarkers)
        self.finishedMarkers = 0
        
        for i in range(numMarkers):
            marker = m.Marker(startLocation, direction)
            self.markers.append(marker)
            
            c, s = np.cos(theta), np.sin(theta)
            R = np.array(((c, 0., s), (0., 1., 0.), (-s, 0., c)))
            
            direction = np.matmul(R, direction)
            
    def propagateCrackFront(self, mesh):
        # TODO: Consider making the number of markers increase/decrease relative to the
        # length of the current crack front, to preserve resolution throughout the simulation
        for marker in self.markers:
            # Only propagate markers that have not intersected with the mesh
            if not marker.finished:
                marker.propagate()
                iPoint, intersection = self.checkIntersection(marker, mesh)
                
                if intersection:
                    marker.finished = True
                    self.finishedMarkers += 1
                    
    def createCrackMesh(self):
        #TODO: Change crack from simple 'sheet' mesh into a proper enclosed mesh by creating an identical
        # mesh, offsetting in in the y direction, and connecting the two meshes
        vertices = []
        faces = []
        numMarkers = len(self.markers)
        # Use adjacent markers to create triangles
        for i in range(numMarkers - 1):
            marker = self.markers[i]
            nextMarker = self.markers[(i + 1) % (numMarkers - 1)]
            prevMarker = self.markers[len(self.markers) - 1 if i == 0 else i - 1]
            
            # Don't create a face connecting two markers that have already finished propagating, since they'll just
            # be duplicates of faces create in a previous iteration
            if marker.finished and nextMarker.finished and prevMarker.finished:
                continue
            
            v1 = marker.currLocation
            v2 = marker.prevLocation
            v3 = nextMarker.currLocation
            v4 = nextMarker.prevLocation
            
            i1 = self.findIndexOfVertex(vertices, v1)
            
            if i1 == -1:
                i1 = len(vertices)
                vertices.append(v1)
                
            i2 = self.findIndexOfVertex(vertices, v2)
                
            if i2 == -1:
                i2 = len(vertices)
                vertices.append(v2)
                
            i3 = self.findIndexOfVertex(vertices, v3)
            
            if i3 == -1:
                i3 = len(vertices)
                vertices.append(v3)
                
            i4 = self.findIndexOfVertex(vertices, v4)
                
            if i4 == -1:
                i4 = len(vertices)
                vertices.append(v4)
            
            f1 = [i3, i4, i2]
            f2 = [i1, i3, i2]
            
            faces.append(f1)
            faces.append(f2)
        
        return vertices, faces
    
    def findIndexOfVertex(self, vertices, vertex):
        index = -1
        for i in range(len(vertices)):
            if np.array_equal(vertices[i], vertex):
                index = i
                
        return index
            
    # Neither PyMesh nor Pyassimp provide a line-mesh intersection method, so have to implement our own
    # Based on the algorithm found at http://geomalgorithms.com/a06-_intersect-2.html#intersect3D_RayTriangle()
    def checkIntersection(self, marker, mesh):
        SMALL_NUM = 0.000001 # Tolerance for floats
        isectPoint = np.zeros(3)
        intersection = False
        
        p0 = marker.prevLocation
        p1 = marker.currLocation
        
        # Segment direction vector
        dir = p1 - p0
        
        for face in mesh.faces:
            v0 = mesh.vertices[face[0]]
            v1 = mesh.vertices[face[1]]
            v2 = mesh.vertices[face[2]]
            
            # Get triangle edge vectors and plane normal
            u = v1 - v0
            v = v2 - v0
            n = np.cross(u, v)
            if np.count_nonzero(n) == 0:     # Triangle is degenerate
                continue                     # Do not deal with this case

            w0 = p0 - v0
            a = -np.dot(n,w0)
            b = np.dot(n,dir)
            
            if abs(b) < SMALL_NUM:        # Ray is parallel to triangle plane or lies in the plane
                continue

            # Get intersect point of ray with triangle plane
            r = a / b;
            
            if r < 0.0:                     # Triangle is behind the segment's p0 if (r < 0.0)
                continue                    # Therefore no intersection
            elif r > 1.0:                   # For a segment, also test if (r > 1.0)
                continue                    # Triangle is past segment's p1 => no intersect
            
            isectPoint = p0 + (r * dir)     # Intersect point of segment and plane
        
            # Is isectPoint inside the triangle?
            uu = np.dot(u,u);
            uv = np.dot(u,v);
            vv = np.dot(v,v);
            w = isectPoint - v0;
            wu = np.dot(w,u);
            wv = np.dot(w,v);
            D = uv * uv - uu * vv;
        
            # get and test parametric coords
            s = (uv * wv - vv * wu) / D;
            if (s < 0.0 or s > 1.0):        # isectPoint is outside T?
                continue
            
            t = (uv * wu - uu * wv) / D;
            if (t < 0.0 or (s + t) > 1.0):   # isectPoint is outside T?
                continue
            
            intersection = True
            break
        
        return isectPoint, intersection