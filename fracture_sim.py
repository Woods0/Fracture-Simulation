import sys
import numpy as np
import math

import pygame
import pygame.locals
import pygame.constants
import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut
from OpenGL.arrays import vbo
from OpenGL.GL import shaders
from pyassimp import *
from pyassimp.helper import *

import simulation
import defaultCamera

width, height= 1024, 768
viewport = (width, height)
simulationName = "Simulation"
shader = None
clock = None
current_cam = None

wireframe = False
max_extra_frames = 360

def render(scene, wireframe = False, twosided = False):
    global shader
    
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glDepthFunc(gl.GL_LEQUAL)

    gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE if wireframe else gl.GL_FILL)
    gl.glDisable(gl.GL_CULL_FACE) if twosided else gl.glEnable(gl.GL_CULL_FACE)

    gl.glUseProgram(shader)
    gl.glUniform4f(shader.Global_ambient, .4,.25,.25,.1)
    gl.glUniform4f(shader.Light_ambient, .3,.4,.5, 1.0)
    gl.glUniform4f(shader.Light_diffuse, 0.77,0.8,1.,1.0)
    gl.glUniform3f(shader.Light_location, 1,5,10)

    recursive_render(scene.rootnode, shader)

    gl.glUseProgram(0)
    
def recursive_render(node, shader):
    """ Main recursive rendering method.
    """
    # save model matrix and apply node transformation
    gl.glPushMatrix()
    m = node.transformation.transpose() # OpenGL row major
    gl.glMultMatrixf(m)

    for mesh in node.meshes:
        stride = 24 # 6 * 4 bytes

        diffuse = mesh.material.properties["diffuse"]
        if len(diffuse) == 3: diffuse.append(1.0)
        ambient = mesh.material.properties["ambient"]
        if len(ambient) == 3: ambient.append(1.0)

        gl.glUniform4f(shader.Material_diffuse, *diffuse)
        gl.glUniform4f(shader.Material_ambient, *ambient)

        vbo = mesh.gl["vbo"]
        vbo.bind()

        gl.glEnableVertexAttribArray(shader.Vertex_position)
        gl.glEnableVertexAttribArray(shader.Vertex_normal)

        gl.glVertexAttribPointer(
            shader.Vertex_position,
            3, gl.GL_FLOAT,False, stride, vbo
       )

        gl.glVertexAttribPointer(
            shader.Vertex_normal,
            3, gl.GL_FLOAT,False, stride, vbo+12
       )

        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, mesh.gl["faces"])
        gl.glDrawElements(gl.GL_TRIANGLES, len(mesh.faces) * 3, gl.GL_UNSIGNED_INT, None)

        vbo.unbind()
        gl.glDisableVertexAttribArray(shader.Vertex_position)

        gl.glDisableVertexAttribArray(shader.Vertex_normal)

        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

    for child in node.children:
        recursive_render(child, shader)

    gl.glPopMatrix()

def prepare_gl_buffers(mesh):
        mesh.gl = {}

        # Fill the buffer for vertex and normals positions
        v = np.array(mesh.vertices, 'f')
        n = np.array(mesh.normals, 'f')

        mesh.gl["vbo"] = vbo.VBO(np.hstack((v,n)))

        # Fill the buffer for vertex positions
        mesh.gl["faces"] = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, mesh.gl["faces"])
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, 
                    mesh.faces,
                    gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER,0)
    
def set_shader_accessors(uniforms, attributes, shader):
    # add accessors to the shaders uniforms and attributes
    for uniform in uniforms:
        location = gl.glGetUniformLocation(shader,  uniform)
        
        setattr(shader, uniform, location)

    for attribute in attributes:
        location = gl.glGetAttribLocation(shader, attribute)
        
        setattr(shader, attribute, location)
    
def prepare_shaders():
    global shader
    
    phong_weightCalc = """
    float phong_weightCalc(
        in vec3 light_pos, // light position
        in vec3 frag_normal // geometry normal
   ) {
        // returns vec2(ambientMult, diffuseMult)
        float n_dot_pos = max(0.0, dot(
            frag_normal, light_pos
       ));
        return n_dot_pos;
    }
    """

    vertex = shaders.compileShader(phong_weightCalc +
    """
    uniform vec4 Global_ambient;
    uniform vec4 Light_ambient;
    uniform vec4 Light_diffuse;
    uniform vec3 Light_location;
    uniform vec4 Material_ambient;
    uniform vec4 Material_diffuse;
    attribute vec3 Vertex_position;
    attribute vec3 Vertex_normal;
    varying vec4 baseColor;
    void main() {
        gl_Position = gl_ModelViewProjectionMatrix * vec4(
            Vertex_position, 1.0
       );
        vec3 EC_Light_location = gl_NormalMatrix * Light_location;
        float diffuse_weight = phong_weightCalc(
            normalize(EC_Light_location),
            normalize(gl_NormalMatrix * Vertex_normal)
       );
        baseColor = clamp(
        (
            // global component
            (Global_ambient * Material_ambient)
            // material's interaction with light's contribution
            // to the ambient lighting...
            + (Light_ambient * Material_ambient)
            // material's interaction with the direct light from
            // the light.
            + (Light_diffuse * Material_diffuse * diffuse_weight)
       ), 0.0, 1.0);
    }""", gl.GL_VERTEX_SHADER)

    fragment = shaders.compileShader("""
    varying vec4 baseColor;
    void main() {
        gl_FragColor = baseColor;
    }
    """, gl.GL_FRAGMENT_SHADER)

    shader = shaders.compileProgram(vertex,fragment)
    set_shader_accessors((
        'Global_ambient',
        'Light_ambient','Light_diffuse','Light_location',
        'Material_ambient','Material_diffuse',
  ), (
        'Vertex_position','Vertex_normal',
   ), shader)

def set_camera_projection(camera = None):
    global cameras, current_cam_index
    
    if not camera:
        camera = cameras[current_cam_index]

    znear = camera.clipplanenear
    zfar = camera.clipplanefar
    aspect = camera.aspect
    fov = camera.horizontalfov

    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()

    # Compute gl frustrum
    tangent = math.tan(fov/2.)
    h = znear * tangent
    w = h * aspect

    # params: left, right, bottom, top, near, far
    gl.glFrustum(-w, w, -h, h, znear, zfar)
    # equivalent to:
    #gluPerspective(fov * 180/math.pi, aspect, znear, zfar)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()


def set_camera(camera):
    set_camera_projection(camera)

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()

    cam = transform([0.0, 0.1, 0.0], camera.transformation)
    at = transform(camera.lookat, camera.transformation)
    glu.gluLookAt(cam[0], cam[2], -cam[1],
                   at[0],  at[2],  -at[1],
                       0,      1,       0)

def initViewer():
    global width, height, current_cam, frames, last_fps_time
    
    pygame.init()
    pygame.display.set_caption(simulationName)
    pygame.display.set_mode((width,height), pygame.OPENGL | pygame.DOUBLEBUF)
    glut.glutInit()
    
    prepare_shaders()

    current_cam = defaultCamera.DefaultCamera(width,height,45.)

    set_camera(current_cam)

def loop():
    global frames, simulationName, last_fps_time, wireframe
    
    clock.tick(60)
    pygame.display.flip()
    pygame.event.pump() # process event queue
    events = pygame.event.get()
    
    for event in events:
        if event.type == pygame.QUIT:
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sys.exit(0)
            elif event.key == pygame.K_q:
                sys.exit(0)
            elif event.key == pygame.K_TAB:
                wireframe = not wireframe

    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    return True
    
#---------Execution----------  
if len(sys.argv) < 2:
    numSteps = 100
else:
    numSteps = int(sys.argv[1])
    
simulation = simulation.Simulation()
simulation.runSim(numSteps)

initViewer()

scenes = simulation.scenes
for scene in scenes:
    for index, mesh in enumerate(scene.meshes):
        prepare_gl_buffers(mesh)

curr_scene = -1
extra_frames = 0

clock = pygame.time.Clock()

while loop():
    curr_scene = min(curr_scene + 1, len(scenes) - 1)
    scene = scenes[curr_scene]
    
    render(scene, wireframe)
    
    if curr_scene == len(scenes) -1:
        extra_frames += 1
        
        if extra_frames == max_extra_frames:
            curr_scene = -1
            extra_frames = 0