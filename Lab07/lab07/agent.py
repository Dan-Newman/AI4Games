'''An agent with Seek, Flee, Arrive, Pursuit behaviours

Created for COS30002 AI for Games by Clinton Woodward cwoodward@swin.edu.au

'''
import pdb
from vector2d import Vector2D
from vector2d import Point2D
from graphics import egi, KEY
from math import sin, cos, radians
from random import random, randrange, uniform
from path import Path

AGENT_MODES = {
    KEY._8: 'wander',
}
AGENT_ATTRIBUTES = {
    KEY.Z: 'cohesion',
    KEY.X: 'seperation',
    KEY.C: 'alignment'
}

AGENT_MULTIPLIERS = {
    KEY.I: 'c_up',
    KEY.O: 's_up',
    KEY.P: 'a_up',
    KEY.J: 'c_down',
    KEY.K: 's_down',
    KEY.L: 'a_down'

}

GROUPING_VALUES = {
    'cohesion' : 0.0,
    'alignment' : 0.0,
    'seperation' : 0.0
}

class Agent(object):

    # NOTE: Class Object (not *instance*) variables!
    DECELERATION_SPEEDS = {
        'slow': 0.9,
        'normal': 0.6,
        'fast': 0.3,
        'super': 0.1
    }

    def __init__(self, world=None, scale=10.0, mass=1.0, mode='wander'):
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
        ### path to follow?
        self.path = Path()
        self.randomise_path()
        self.waypoint_threshold = 20

        ### wander details
        # self.wander_?? ...
        self.wander_target = Vector2D(1,0)
        self.wander_dist = 1.0 * scale
        self.wander_radius = 1.0 * scale
        self.wander_jitter = 10.0 * scale
        self.bRadius = scale

        #Neighbourhood radius
        self.tag_radius = 5.0 * scale
        self.cohesion_toggle = False
        self.alignment_toggle = False
        self.seperation_toggle = False

        # limits?
        self.max_speed = 20.0 * scale
        ## max_force ??
        self.max_force = 500.0

        # debug draw info?
        self.show_info = False

    def calculate(self, delta):
        force = Vector2D()
        # calculate the current steering force
        force += self.wander(delta) * 0.5
        if(self.cohesion_toggle):
            force += self.cohesion() * GROUPING_VALUES['cohesion']
        if self.seperation_toggle:
            force += self.seperation() * GROUPING_VALUES['seperation']
        if self.alignment_toggle:
            force += self.alignment() * GROUPING_VALUES['alignment']

        self.force = force
        return force

    def update(self, delta):
        ''' update vehicle position and orientation '''
        # calculate and set self.force to be applied
        ## force = self.calculate()
        self.update_text()
        if self.cohesion_toggle or self.seperation_toggle or self.alignment_toggle is True:
            self.tag_neighbours(self.tag_radius)

        force = self.calculate(delta)  # <-- delta needed for wander
        ## limit force? <-- for wander
        # ...
        force.truncate(self.max_force)
        # determin the new accelteration
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
        # draw the path if it exists and the mode is follow
        if self.mode == 'follow_path':
            self.path.render()


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

    def flee(self, hunter_pos):
        if(Vector2D.distance(self.pos, hunter_pos) < 100):
            desired_vel = (self.pos - hunter_pos).normalise() * self.max_speed
            return (desired_vel - self.vel)
        elif(Vector2D.distance(self.pos, hunter_pos) > 300):
            return self.seek(hunter_pos) #TODO: Replace with wander function call
        else:
            return Vector2D()

    def arrive(self, target_pos, speed):
        ''' this behaviour is similar to seek() but it attempts to arrive at
            the target position with a zero velocity'''
        decel_rate = self.DECELERATION_SPEEDS[speed]
        to_target = target_pos - self.pos
        dist = to_target.length()
        if dist > 0:
            # calculate the speed required to reach the target given the
            # desired deceleration rate
            speed = dist / decel_rate
            # make sure the velocity does not exceed the max
            speed = min(speed, self.max_speed)
            # from here proceed just like Seek except we don't need to
            # normalize the to_target vector because we have already gone to the
            # trouble of calculating its length for dist.
            desired_vel = to_target * (speed / dist)
            return (desired_vel - self.vel)
        return Vector2D(0, 0)

    def pursuit(self, evader):
        evader.mode = 'wander'

        ## OPTIONAL EXTRA... pursuit (you'll need something to pursue!)
        self.toEvader = evader.pos - self.pos
        self.relHeading = Vector2D.dot(evader.heading, self.heading)

        if(Vector2D.dot(self.toEvader, self.heading) > 0 and self.relHeading < -0.95):
            return self.seek(evader.pos)

        lookAheadTime = Vector2D.length(self.toEvader) / (self.max_speed + evader.speed())
        return self.seek(evader.pos + evader.vel * lookAheadTime)


    def randomise_path(self):
        cx = self.world.cx
        cy = self.world.cy
        margin = min(cx,cy)*(1/6)
        self.path.set_pts(self.path.create_random_path(5, (cx + margin)/2, (cy + margin)/2, (cx - margin)/2, (cy - margin)/2, True))


    def follow_path(self):
        if(self.path is None):
            self.path = self.randomise_path()
        if(Vector2D.distance(self.path.current_pt(), self.pos) <= self.waypoint_threshold):
            self.path.inc_current_pt()

        return self.arrive(self.path.current_pt(), 'normal')



    def wander(self, delta):
        wt = self.wander_target
        jitter_tts = self.wander_jitter * delta
        wt += Vector2D(uniform(-1,1) * jitter_tts, uniform(-1,1) * jitter_tts)
        wt.normalise()

        wt *= self.wander_radius
        target = wt + Vector2D(self.wander_dist,0)
        wld_target = self.world.transform_point(target, self.pos, self.heading, self.side)
        return self.seek(wld_target)

    def update_text(self):
        self.attribute = ''
        if self.seperation_toggle:
            self.attribute += 'seperation, '
        if self.cohesion_toggle:
            self.attribute += 'cohesion, '
        if self.alignment_toggle:
            self.attribute += 'alignment, '

    #Steering behaviours
    def tag_neighbours(self, radius):
        self.untag()
        for otherAgents in self.world.agents:
            to = self.pos - otherAgents.pos
            gap = radius + otherAgents.tag_radius
            if Vector2D.length_sq(to) < gap**2:
                otherAgents.tagged = True;

    def untag(self):
        for agent in self.world.agents:
            agent.tagged = False

    def seperation(self):
        steering_force = Vector2D()
        for agent in self.world.agents:
            if(agent is not self and agent.tagged):
                toBot = self.pos - agent.pos
                steering_force += Vector2D.normalise(toBot)/Vector2D.length(toBot)
        return steering_force

    def cohesion(self):
        centre_mass = Vector2D()
        steering_force = Vector2D()
        neighbour_count = 0
        for agent in self.world.agents:
            if agent is not self and agent.tagged:
                centre_mass += agent.pos
                neighbour_count += 1

        if neighbour_count > 0:
            centre_mass /= neighbour_count
            steering_force = self.seek(centre_mass)
        return steering_force

    def alignment(self):
        avg_heading = Vector2D()
        neighbour_count = 0
        for agent in self.world.agents:
            if agent is not self and agent.tagged:
                avg_heading += agent.heading
                neighbour_count += 1
        if neighbour_count > 0:
            avg_heading /= neighbour_count
            avg_heading -= self.heading
        return avg_heading

    @staticmethod
    def update_multipliers(keypress):
            if keypress is 'c_up':
                GROUPING_VALUES['cohesion'] += 0.1
            elif keypress is 'c_down':
                GROUPING_VALUES['cohesion'] -= 0.1
            if keypress is 'a_up':
                GROUPING_VALUES['alignment'] += 0.1
            elif keypress is 'a_down':
                GROUPING_VALUES['alignment'] -= 0.1
            if keypress is 's_up':
                GROUPING_VALUES['seperation'] += 0.1
            elif keypress is 's_down':
                GROUPING_VALUES['seperation'] -= 0.1
