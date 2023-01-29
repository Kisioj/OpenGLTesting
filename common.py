import ctypes

import numpy as np
import pygame
from OpenGL.GL import *
from PIL import Image
from glm import mat4, translate, vec3, ortho, value_ptr


USE_VBO_FROM_OPENGL_ARRAYS = False
if USE_VBO_FROM_OPENGL_ARRAYS:
    from OpenGL.arrays import vbo

    class VBO(vbo.VBO):
        def offset(self, offset):
            return self + offset


else:
    class VBO:
        def __init__(self, data, target):
            self.id = glGenBuffers(1)
            self.target = target
            glBindBuffer(target, self.id)
            glBufferData(target, data.nbytes, data, GL_STATIC_DRAW)

        def offset(self, offset):
            return ctypes.c_void_p(offset)

        def bind(self):
            glBindBuffer(GL_ARRAY_BUFFER, self.id)

        def unbind(self):
            glBindBuffer(GL_ARRAY_BUFFER, 0)

        def __del__(self):
            buffers = np.array([self.id], dtype=np.uint32)
            glDeleteBuffers(1, buffers)


FPS = 1
FRAME_TIME_MS = 1000 / FPS

VERTEX_SHADER = """
# version 330
layout(location = 0) in vec2 VertexPos2D;
layout(location = 1) in vec2 VertTexCoord;

uniform mat4 ProjectionMatrix;
uniform mat4 ModelViewMatrix;

out vec2 FragTexCoord;
void main()
{
    gl_Position = ProjectionMatrix * ModelViewMatrix * vec4(VertexPos2D.x, VertexPos2D.y, 0.0, 1.0);
    FragTexCoord = VertTexCoord;
}
"""

FRAGMENT_SHADER = """
# version 330
in vec2 FragTexCoord;
out vec4 glFragColor;

uniform sampler2D TextureUnit;

void main()
{
    glFragColor = texture(TextureUnit, FragTexCoord);
}
"""

program_id = None
texture_id = None
tex_coord_location = None
vertex_pos2d_location = None
# tex_unit_location = None
projection_matrix_location = None
model_view_matrix_location = None


def initialize_gl():
    global program_id
    global texture_id
    global tex_coord_location
    global vertex_pos2d_location
    # global tex_unit_location
    global projection_matrix_location
    global model_view_matrix_location

    program_id = glCreateProgram()

    vertex_shader_id = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vertex_shader_id, VERTEX_SHADER)
    glCompileShader(vertex_shader_id)
    glAttachShader(program_id, vertex_shader_id)

    fragment_shader_id = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fragment_shader_id, FRAGMENT_SHADER)
    glCompileShader(fragment_shader_id)
    glAttachShader(program_id, fragment_shader_id)

    glLinkProgram(program_id)
    glDeleteShader(vertex_shader_id)
    glDeleteShader(fragment_shader_id)

    tex_coord_location = glGetAttribLocation(program_id, "VertTexCoord")
    vertex_pos2d_location = glGetAttribLocation(program_id, "VertexPos2D")

    # tex_unit_location = glGetUniformLocation(program_id, "TextureUnit")
    projection_matrix_location = glGetUniformLocation(program_id, "ProjectionMatrix")
    model_view_matrix_location = glGetUniformLocation(program_id, "ModelViewMatrix")

    print(f'{tex_coord_location=}')
    print(f'{vertex_pos2d_location=}')
    # print(f'{tex_unit_location=}')
    print(f'{projection_matrix_location=}')
    print(f'{model_view_matrix_location=}')

    glUseProgram(program_id)
    projection_matrix = ortho(0, 416, 416, 0)
    print(f'{projection_matrix=}')
    glUniformMatrix4fv(projection_matrix_location, 1, GL_FALSE, value_ptr(projection_matrix))
    model_view_matrix = mat4()
    glUniformMatrix4fv(model_view_matrix_location, 1, GL_FALSE, value_ptr(model_view_matrix))
    glUseProgram(0)

    glClearColor(0, 0, 0, 1)
    glEnable(GL_BLEND)
    glDisable(GL_DEPTH_TEST)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_TEXTURE_2D)

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)

    pixel_format = GL_RGBA
    glTexImage2D(GL_TEXTURE_2D, 0, pixel_format, texture_width, texture_height, 0, pixel_format, GL_UNSIGNED_BYTE, pixels)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glBindTexture(GL_TEXTURE_2D, 0)

    global ibo
    ibo = VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)

    global grass_vbo
    grass_vbo = get_vbo(grass_rect)


def paint_gl():
    glViewport(0, 0, screen_width, screen_height)

    glClear(GL_COLOR_BUFFER_BIT)
    glEnableVertexAttribArray(vertex_pos2d_location)
    glEnableVertexAttribArray(tex_coord_location)

    bound_texture_id = None
    for x, y in locs:
        vbo = grass_vbo

        glUseProgram(program_id)
        model_view_matrix = translate(vec3(x, y, 0))
        print(f'{model_view_matrix=}')
        glUniformMatrix4fv(model_view_matrix_location, 1, GL_FALSE, value_ptr(model_view_matrix))

        if bound_texture_id != texture_id:
            glBindTexture(GL_TEXTURE_2D, texture_id)
            bound_texture_id = texture_id
            print(f'{bound_texture_id=}')

        vbo.bind()
        glVertexAttribPointer(vertex_pos2d_location, 2, GL_FLOAT, GL_FALSE, 16, vbo.offset(0))
        glVertexAttribPointer(tex_coord_location, 2, GL_FLOAT, GL_FALSE, 16, vbo.offset(8))

        ibo.bind()
        glDrawElements(GL_TRIANGLE_FAN, 4, GL_UNSIGNED_INT, None)

        glUseProgram(0)

    glDisableVertexAttribArray(vertex_pos2d_location)
    glDisableVertexAttribArray(tex_coord_location)
    glBindTexture(GL_TEXTURE_2D, 0)




def next_power_of_two(num):
    if num != 0:
        num -= 1
        num |= (num >> 1)
        num |= (num >> 2)
        num |= (num >> 4)
        num |= (num >> 8)
        num |= (num >> 16)
        num += 1
    return num


def get_vbo(rect):
    x, y, w, h = rect
    tex_top = y / texture_height
    tex_bottom = (y + h) / texture_height
    tex_left = x / texture_width
    tex_right = (x + w) / texture_width
    quad_width = w
    quad_height = h

    vertices = np.array([
        0, 0, tex_left, tex_top,
        quad_width, 0, tex_right, tex_top,
        quad_width, quad_height, tex_right, tex_bottom,
        0, quad_height, tex_left, tex_bottom,
    ], dtype=np.float32)

    return VBO(vertices, target=GL_ARRAY_BUFFER)


image = Image.open('mapwhite.png').convert('RGBA')

pixels = np.array(image.getdata(), dtype=np.uint8).reshape(image.height, image.width, 4)

texture_width = next_power_of_two(image.width)
texture_height = next_power_of_two(image.height)

if texture_width != image.width or texture_height != image.height:
    zeros = np.zeros((texture_height, texture_width, 4), dtype=np.uint8)
    zeros[:image.height, :image.width, :] = pixels
    pixels = zeros


grass_rect = (32, 0, 32, 32)
tile_name = "grass"
grass_vbo = None

screen_width = 399
screen_height = 507
display = (screen_width, screen_height)


indices = np.array([
    0, 1, 2, 3
], dtype=np.int32)
ibo = None

locs = [(128, 208), (128, 176)]
