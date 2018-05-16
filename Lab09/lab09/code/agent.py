'''An agent with Seek, Flee, Arrive, Pursuit behaviours

Created for COS30002 AI for Games by Clinton Woodward cwoodward@swin.edu.au

'''
import pdb
from vector2d import Vector2D
from vector2d import Point2D
from graphics import egi, KEY
from math import *
from random import random, randrange, uniform
from path import Path

GUN_MODES = {
    KEY._1: 'Rifle',
    KEY._2: 'Rocket',
    KEY._3: 'Pistol',
    KEY._4: 'Grenade',
}


class Agent(object):

    # NOTE: Class Object (not *instance*) variables!
    def __init__(self, world=None, scale=10.0, mass=1.0, mode='Rifle'):
        # keep a reference to the world object
        self.world = world
        self.mode = mode
        self.tagged = False
        # where am i and where am i going? random start pos
        dir = radians(random()*360)
        self.pos = Vector2D(randrange(world.cx), randrange(world.cy))
        self.vel = Vector2D()
        self.heading = Vector2D(sin(dir), cos(dir))
        self.side = self.heading.perp()
        self.scale = Vector2D(scale, scale)  # easy scaling of agent size
        self.force = Vector2D()  # current steering force
        self.accel = Vector2D() # current acceleration due to force
        self.mass = mass

        # data for drawing this agent
        self.color = 'ORANGE'
        self.vehicle_shape = [
            Point2D(-1.0,  0.6),
            Point2D( 1.0,  0.0),
            Point2D(-1.0, -0.6)
        ]

        ### wander details
        # self.wander_?? ...
        self.wander_target = Vector2D(1,0)
        self.wander_dist = 1.0 * scale
        self.wander_radius = 1.0 * scale
        self.wander_jitter = 10.0 * scale
        self.bRadius = scale

        # limits?
        self.max_speed = 20.0 * scale
        ## max_force ??
        self.max_force = 500.0

        # debug draw info?
        self.show_info = False

    def calculate(self, delta):
        if self is not self.world.hunter:
            force = Vector2D()
            # calculate the current steering force
            force += self.wander(delta)
            self.force = force
            return force
        else:
            fire(self, self.world.agent)


    def update(self, delta):
        ''' update vehicle position and orientation '''
        force = self.calculate(delta)  # <-- delta needed for wander
        ## limit force? <-- for wander
        # ...
        force.truncate(self.max_force)
        # determine the new acceleration
        self.accel = force / self.mass  # not needed if mass = 1.0
        # new velocity
        self.vel += self.accel * delta
        # check for limits of new velocity
        self.vel.truncate(self.max_speed)
        # update position
        self.pos += self.vel * delta
        # update heading is non-zero velocity (moving)
        if self.vel.length_sq() > 0.00000001:
            self.heading = self.vel.get_normalised()
            self.side = self.heading.perp()
        # treat world as continuous space - wrap new position if needed
        self.world.wrap_around(self.pos)

    def render(self, color=None):
        ''' Draw the triangle agent with color'''
        # draw the ship
        if(color == None):
            egi.set_pen_color(name=self.color)
        else:
            egi.set_pen_color(name=color)
        pts = self.world.transform_points(self.vehicle_shape, self.pos,
                                          self.heading, self.side, self.scale)
        # draw it!
        egi.closed_shape(pts)

        # draw wander info?
        if self.mode == 'wander':
            ## ...
            wnd_pos = Vector2D(self.wander_dist,0)
            wld_pos = self.world.transform_point(wnd_pos, self.pos, self.heading, self.side)

            egi.green_pen()
            egi.circle(wld_pos, self.wander_radius)

            egi.red_pen()
            wnd_pos = (self.wander_target + Vector2D(self.wander_dist,0))
            wld_pos = self.world.transform_point(wnd_pos, self.pos, self.heading,self.side)
            egi.circle(wld_pos,3)

        # add some handy debug drawing info lines - force and velocity
        if self.show_info:
            s = 0.5 # <-- scaling factor
            # force
            egi.red_pen()
            egi.line_with_arrow(self.pos, self.pos + self.force * s, 5)
            # velocity
            egi.grey_pen()
            egi.line_with_arrow(self.pos, self.pos + self.vel * s, 5)
            # net (desired) change
            egi.white_pen()
            egi.line_with_arrow(self.pos+self.vel * s, self.pos+ (self.force+self.vel) * s, 5)
            egi.line_with_arrow(self.pos, self.pos+ (self.force+self.vel) * s, 5)

    def speed(self):
        return self.vel.length()

    #--------------------------------------------------------------------------

    def seek(self, target_pos):
        ''' move towards target position '''
        desired_vel = (target_pos - self.pos).normalise() * self.max_speed
        return (desired_vel - self.vel)


    def pursuit(self, evader):

        ## OPTIONAL EXTRA... pursuit (you'll need something to pursue!)
        self.toEvader = evader.pos - self.pos
        self.relHeading = Vector2D.dot(evader.heading, self.heading)

        if(Vector2D.dot(self.toEvader, self.heading) > 0 and self.relHeading < -0.95):
            return self.seek(evader.pos)

        lookAheadTime = Vector2D.length(self.toEvader) / (self.max_speed + evader.speed())
        return self.seek(evader.pos + evader.vel * lookAheadTime)


    def wander(self, delta):
        wt = self.wander_target
        jitter_tts = self.wander_jitter * delta
        wt += Vector2D(uniform(-1,1) * jitter_tts, uniform(-1,1) * jitter_tts)
        wt.normalise()

        wt *= self.wander_radius
        target = wt + Vector2D(self.wander_dist,0)
        wld_target = self.world.transform_point(target, self.pos, self.heading, self.side)
        return self.seek(wld_target)


    def fire(self, target):

        if self.mode is "Rifle":
            self.world.add(RifleFire(self.pos, target.pos))
        elif self.mode is "Pistol":
            self.world.add(PistolFire(self.pos, target.pos))
        elif self.mode is "Rocket":
            self.world.add(RocketFire(self.pos, target.pos))
        elif self.mode is "Grenade":
            self.world.add(GrenadeFire(self.pos, target.pos))

    # -------------------------------------------------------------------------

    class Bullet(object):
        def __init__(self, x, y):
            self.world = None
            self.active = True
            self.position = Vector2D(x, y)
            self.vel = Vector2D()

        def update(self):
            self.position = self.direction * self.speed


        def RifleFire(self, start_pos, target_pos):
            direction = Vector2D.normalise(start_pos - target_pos)
            radius = 5
            speed = 25