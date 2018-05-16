from vector2d import Vector2D
from random import random, randrange, uniform
from math import sin, cos, radians
from graphics import egi, KEY


class Obstacle(object):

    def __init__(self, world=None):
        self.world = world
        self.radius = randrange(10, 40)
        self.agent = None
        self.tagged = False #for obstacle avoidance
        self.pos = Vector2D(randrange(world.cx), randrange(world.cy))

        self.color = 'BLUE'

    def render(self):
        egi.color = self.color
        egi.circle(self.pos, self.radius)
