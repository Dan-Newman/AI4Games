from vector2d import Vector2D
from vector2d import Point2D
from graphics import egi, KEY
from math import *
from random import random, randrange, uniform



GUN_MODES = {
    KEY._1: 'Rifle',
    KEY._2: 'Rocket',
    KEY._3: 'Pistol',
    KEY._4: 'Grenade',
}


class Hunter(object):
    def __init__(self, world=None):
        self.world = world
        self.pos = Vector2D(world.cx/2,world.cy/2)
        self.radius = 10
        self.gun = Gun(self.pos, world)


    def update(self):
        target = self.world.prey
        self.gun.fire(target)

    def render(self):
        egi.green_pen()
        egi.set_stroke(2)
        egi.circle(self.pos, self.radius, True)





class Prey(object):
    def __init__(self, world=None, scale=10.0):
        self.world = world
        self.pos = Vector2D(randrange(world.cx), randrange(world.cy))
        self.vel = Vector2D()
        self.accel = Vector2D()
        dir = radians(random() * 360)
        self.heading = Vector2D(sin(dir), cos(dir))
        self.side = self.heading.perp()
        self.shape = [
            Point2D(-1.0, 0.6),
            Point2D(1.0, 0.0),
            Point2D(-1.0, -0.6)
        ]

        self.scale = Vector2D(scale, scale)
        self.wander_target = Vector2D(1, 0)
        self.wander_dist = 1.0 * scale
        self.wander_radius = 1.0 * scale
        self.wander_jitter = 10.0 * scale

        # limits?
        self.max_speed = 20.0 * scale
        ## max_force ??
        self.max_force = 500.0

    def update(self, delta):
            # calculate the current steering force
            force = self.wander(delta)

            force.truncate(self.max_force)
            # determine the new acceleration
            self.accel = force  # not needed if mass = 1.0
            # new velocity
            self.vel += self.accel * delta
            # check for limits of new velocity
            self.vel.truncate(self.max_speed)
            # update position
            self.pos += self.vel * delta

            # treat world as continuous space - wrap new position if needed
            self.world.wrap_around(self.pos)

    def render(self):
        egi.red_pen()
        pts = self.world.transform_points(self.shape, self.pos,
                                          self.heading, self.side, self.scale)
        # draw it!
        egi.closed_shape(pts)

    def speed(self):
        return self.vel.length()

    def seek(self, target_pos):
        ''' move towards target position '''
        desired_vel = (target_pos - self.pos).normalise() * self.max_speed
        return desired_vel - self.vel

    def wander(self, delta):
        wt = self.wander_target
        jitter_tts = self.wander_jitter * delta
        inc = Vector2D(uniform(-1, 1) * jitter_tts, uniform(-1, 1) * jitter_tts)
        wt += inc
        wt.normalise()

        wt *= self.wander_radius
        target = wt + Vector2D(self.wander_dist, 0)
        wld_target = self.world.transform_point(target, self.pos, self.heading, self.side)
        return self.seek(wld_target)


class Gun(object):
    def __init__(self, firing_pos, world=None, mode="Rifle"):
        self.init_pos = Vector2D.copy(firing_pos)
        self.world = world
        self.mode = mode

    def fire(self, target):

        if self.mode is "Rifle":
            self.world.add(RifleBullet(self.init_pos, target.pos))
        elif self.mode is "Pistol":
            self.world.add(PistolBullet(self.init_pos, target.pos))
        elif self.mode is "Rocket":
            self.world.add(RocketBullet(self.init_pos, target.pos))
        elif self.mode is "Grenade":
            self.world.add(GrenadeBullet(self.init_pos, target.pos))


class Bullet(object):
    def __init__(self, firing_pos, target_pos):
        self.init_pos = firing_pos
        self.pos = firing_pos
        self.direction = Vector2D.normalise(firing_pos - target_pos)
        self.velocity = 10
        self.radius = 5
        self.collision = None

    def update(self, delta):
       self.pos += (self.direction * self.velocity) * delta



    def render(self):
        egi.white_pen()
        egi.set_stroke(3)
        egi.circle(self.pos, self.radius)


class RifleBullet(Bullet):
    def __init__(self, firing_pos, target_pos):
        Bullet.__init__(self, firing_pos, target_pos)
        self.radius = 10
        self.velocity = 15


class PistolBullet(Bullet):
    def __init__(self, firing_pos, target_pos):
        Bullet.__init__(firing_pos, target_pos)
        self.radius = 10
        self.velocity = 25


class RocketBullet(Bullet):
    def __init__(self, firing_pos, target_pos):
        Bullet.__init__(firing_pos, target_pos)
        self.radius = 15
        self.velocity = 10


class GrenadeBullet(Bullet):
    def __init__(self, firing_pos, target_pos):
        Bullet.__init__(firing_pos, target_pos)
        self.radius = 15
        self.velocity = 10
