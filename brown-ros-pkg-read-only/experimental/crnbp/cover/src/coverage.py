#!/usr/bin/env python
#
# This code for a ROS node formulates a guess for how a robot and some
# of its friends should best cover some territory.  The robot has a
# guess about its own position and some knowledge of the position of
# its friends.  They, of course, will have differing opinions, and the
# hope is that through the successive iterations of refining these
# guesses that we converge on a solution (while the robots are each
# moving to the goals they have set for themselves).
#
import roslib ; roslib.load_manifest('cover')
import rospy
from cover.msg import Room, Room2D
from cover.srv import MRFQuery, MRFQueryRequest, MRFQueryResponse
from irobot_create_2_1a.msg import SensorPacket
from perfesser.msg import Belief, Pt
from perfesser_guesser import Guesser
from geometry_msgs.msg import Twist, Quaternion, Pose
from nav_msgs.msg import Odometry
from model_phi import Phi
import numpy as np
import math

class Neighbor(object):
    """
    This class stores information about a neighboring robot, including
    the last message it sent to us and its location (presumably
    measured by AR tag or radio signal strength or something).

    For the purposes of demonstration, we are cheating in how we measure 
    our neighbor robots' positions.  That is, we're simply asking them,
    via the Neighbor.getPos() method.
    """
    def __init__(self, name, pos=(0.0, 0.0, 0.0)):
        self.name = name

        # Use this to substitute for measuring the neighbor's position.
        self.lsub = rospy.Subscriber("/" + self.name + "/guesser/position/guess", 
                                     Belief, self.getPos, 
                                     queue_size = 1, buff_size = 200)

        # Use this to hold a measurement of the neighboring robot's
        # position.
        self.location = Belief(data_type = "location",
                               data_sub_type = self.name,
                               pers = (0.0, 0.0, 2*math.pi))
        # Use this to hold the last question sent to the neighboring
        # robot.  This 'question' would have been a suggestion about
        # appropriate directions for that neighboring robot to move
        # in.
        self.lastQuestion = Belief(data_type = "destination",
                                   data_sub_type = self.name,
                                   pers = (0.0, 0.0, 2*math.pi))
        # This is the reply to the question stored above, a collection
        # of ratings of each of the points in the question above.
        # Each point is a floating-point value x: 0 < x < 1.
        self.lastReply = Belief(data_type = "rating",
                                data_sub_type = "from " + self.name,
                                pers = (0.0, 0.0, 2*math.pi))

        # This is the service by which we send the lastQuestion and
        # receive the lastReply.  Note the absolute service name.
        self.advise = rospy.ServiceProxy("/" + self.name + "/cover/advice",
                                         MRFQuery, persistent=True)

    def str(self):
        out = ""
        out += "Name=%s" % (self.name,)
        out += "Location=%.3f\n" % tuple(self.location.means)
        out += str(self.location)
        out += str(self.lastQuestion)
        return out

    def getPos(self, req):
        """
        Receives a Belief object containing the robot's location
        estimate.
        """
        self.location = req


class CoverageControl(object):
    def __init__(self, name, npoints = 7, away = 1.3, space = 0.6, 
                 avoid = 0.5, seek = 4.0, maxDist = 2.0,
                 velPub = False, goalPub = False):
        print "Starting:" , name
    
        self.name = name
        self.pos = Belief(data_type = "position", data_sub_type = self.name,
                          pers = (0.0, 0.0, 2*math.pi))
        self.npoints = npoints

        # These are coefficients for the opinion formation.
        # Away controls the desire to move apart.
        self.away = away
        # Without this space term, you get an exploding ring more often with
        # nothing in the middle.
        self.space = space 
        # Controls the predilection to avoid previously-encountered obstacles.
        self.avoid = avoid
        # Controls interest in new territory.
        self.seek = seek

        # Poorly named -- the potential function in the phi.away() method 
        # attempts to put this distance between each node.
        self.maxDist = maxDist

        # This is a list of neighboring robots, assumed to contain
        # Neighbor() objects, as defined above.
        self.neighbors = []

        # This is an array of points in configuration space indicating
        # where we need to go next.
        self.deltaConfig = np.array([[]])

        self.twist = Twist()

        #** These are moved to gnav
        self.maxSpeed = 0.25
        self.maxTurn = 0.35
        self.kSpeed = 1.0
        self.kTurn = 1.0

        self.phi = Phi(self.name, 
                       self.away, self.space, self.avoid, self.seek, 
                       self.maxDist)

        self.movePeriod = 3.0
        self.nextMoveTime = rospy.Time.now().to_sec() + self.movePeriod

        # When this is in the future, we are still dealing with a bump.  Don't
        # register other obstacles within a couple of seconds.
        self.bumpFreeTime = 0.0

        # Estimated variance in the position measurements.  This is important
        # in the resampling of the guesses.
        self.std = 0.1

        # When rating a neighbor's opinion about our desired position,
        # use this many bins.  Shouldn't be a radically different
        # order of magnitude from npoints.
        self.nbins = (5,5)

        self.velPub = velPub
        self.goalPub = goalPub

        try:
#            assert velPub
            assert goalPub
        except:
            print "must specify a goal publisher"

        self.busy = False

    def recordNeighbors(self, req):
        """
        At any time, the self.neighbors list should contain a Neighbor
        object for each robot whose position we can measure directly.

        We are receiving a list of robots and distances (signal
        strengths) via the /olsr/neighbors topic and accumulating.
        Use this as a callback to the /olsr/neighbors topic.  The
        result of calling this is an updated self.neighbors array.
        """
        ### This is a hack until the OLSR ROS node is working.  We just
        ### use a fixed list of all the robots and subtract our name.

        rm = Room(sourceName = self.name)
        rm.names = req
        rm.locations = [ Pt(point = (1.0, 0.0)), Pt(point = (1.0, 0.0)) ]

        rm.names.remove(self.name)

        self.neighbors = []
        for name in rm.names:
            self.neighbors.append(Neighbor(name = name))


    def trackSensors(self, sensors):
        if sensors.bumpLeft or sensors.bumpRight:
            now = rospy.Time.now().to_sec()

            if now > self.bumpFreeTime:
                # Register the obstacle with the phi function.
                obstaclePos = (self.pos.means[0]+0.3*math.cos(self.pos.means[2]),
                               self.pos.means[1]+0.3*math.sin(self.pos.means[2]),
                               0.0 )

                self.phi.addObstacle(obstaclePos)

            # Set bump time (when it's ok to pay attention to the phi again)
            self.bumpFreeTime = rospy.Time.now().to_sec() + 1.0


    def trackPos(self, req):
        """
        This gets called as often as a new position estimate is
        issued by the perfesser.
        """
        if rospy.Time.now().to_sec() > self.bumpFreeTime:
            self.bumpFreeTime = 0.0

        self.pos = req

        # We are relying on the Belief.means to have been filled in by
        # the sending process.  Should check.
        assert sum(self.pos.means) != 0.0

        self.phi.updateOccupancy(self.pos.means)

        now = rospy.Time.now().to_sec()
        if self.nextMoveTime - now < self.movePeriod:
            self.evaluateMove()
            self.nextMoveTime = now + self.movePeriod

    def takeAdvice(self, req):
        """
        Takes a piece of advice from its neighbor, rates it, and
        returns the rating.  The advice is a distribution of points to
        which the other robot thinks this robot ought to go.  We
        compare that advice to our own intentions and return ratings
        indicating the degree of agreement between the two: 1.0 is
        complete agreement and 0.0 is complete disagreement.  We never
        return exactly 0.0 as a matter of policy.
        """
        print "entering takeAdvice:", str(req)

        if not req.question:
            return MRFQueryResponse(no_data = True)
        if not self.deltaConfig.any():
            return MRFQueryResponse(no_data = True)

        # Allocate our intention into bins.
        question = self.ptsToArray(req.question)

        # Establish bins so that there is one point in each outer bin.
        # (The Histogram class in perfesser is set up so the outer
        # bins will be empty, which is why we're not using it here.
        mins = [ min(self.deltaConfig[:,0]), min(self.deltaConfig[:,1]) ]
        maxs = [ max(self.deltaConfig[:,0]), max(self.deltaConfig[:,1]) ]

        bins = [ np.linspace(mn + 1.e-10, mx - 1.e-10, bn - 1) for \
                     mn, mx, bn in zip(mins, maxs, self.nbins) ]
        hist = np.zeros(self.nbins)

        # Create a distribution of points that includes neighbors'
        # opinions, omitting the one asking the question.
        phi = self.deltaConfig[:,(0,1)]
        
        messageProduct = [ 1.0 ] * phi.shape[0]
        for nb in self.neighbors:
            if (nb.name != req.asker) and (nb.lastReply.points):
                messageProduct = [ m * p.point[0] for m,p in \
                                   zip(messageProduct,
                                       nb.lastReply.points) ]

        phi = self.resample(phi, messageProduct)

        # Populate bins
        for delta in phi:
            hist[sum(delta[0] > bins[0])][sum(delta[1] > bins[1])] += 1.0

        n = sum(sum(hist))

        # Formulate a reply by binning the input data.
        m = MRFQueryResponse(no_data = False,
                             source_stamp = req.source_stamp)
        for q in req.question:
            m.reply.append(Pt(point=( \
                        hist[sum(q.point[0] > bins[0])][sum(q.point[1] > bins[1])]/n, )))

        # print "entering service: ", self.name
        # print self.name, "'s opinion: ", self.deltaConfig
        # print "question: ",question
        # print "hist: ", hist
        # print "bins: ", bins
        # print m
        return m

    def ptsToArray(self, pts):
        return np.array([p.point for p in pts])

    def arrayToPts(self, array):
        return [ Pt(point = a) for a in array ]

    def setAdvice(self, name, advice):
        """
        Takes a name of a robot and an array of advice and stores it
        in the neighbor array -- if there is an appropriate entry for
        it there.
        """
        # print "setAdvice:", name, advice

        for nb in self.neighbors:
            if nb.name == name:
                nb.lastQuestion.points = self.arrayToPts(advice)

    def evaluateMove(self):
        """
        Formulates a distribution of points representing a belief
        about the direction in which we should move, along with our
        neighbors.  The belief is based on our measurements of our own
        location, as well as the location of the other robots, along
        with some goals (i.e. spread out, explore, etc).

        To be explicit, inputs are these:
          - Location of self
          - Location of neighbors
          - Suggestions from neighbors about where self should move. 
          - Replies by neighbors to suggestions about where they
        should move.

        The first two form the input to the phi() function.  The third
        is the input to the psi() function, and the fourth is the
        messageProduct referenced below.

        Definition: "configuration space" is the n-dimensional space
        where each point represents a particular configuration of all
        the robots in it.  So a one-dimensional room containing three
        robots corresponds to a three-dimensional configuration
        space.  A two-dimensional room with five robots makes ten
        dimensions in configuration space.  Seems confusing, but it
        makes some of the math easier.
        """
        if self.busy or (self.bumpFreeTime > 0.0):
            return
        self.busy = True

        print "processing... (%s)" % (self.name,)

        # Marshal the inputs: our position and the positions of our
        # neighbors.  Park them all in an array where each row
        # represents a position in configuration space and the
        # collection of rows represent the distribution of those
        # points.
        currentConfig = np.array(self.ptsToArray(self.pos.points))[:,(0,1)]

        # For 2d this should be two entries with X and Y
        self.deltaNames = [ self.name + "/dx", self.name + "/dy" ] 

        print "NEIGHBORS>>>", [nb.name for nb in self.neighbors], "<<<"

        for nb in self.neighbors:
            if nb.location.points:
                currentConfig = \
                    np.hstack([currentConfig, 
                               self.ptsToArray(nb.location.points)[:,(0,1)]])

                self.deltaNames += [ nb.name + "/dx", nb.name + "/dy" ]
        # The currentConfig is now constructed.

        print "got deltaNames: ", self.deltaNames
        print "cc[0]:", currentConfig[0]
        print "cc[1]:", currentConfig[1]
        print "cc[2]:", currentConfig[2]
        #print str(currentConfig)

        # Run through the points in the current configuration and
        # generate predictions for each point in the distribution.
        deltaPts = []
        for cpoint in currentConfig:
            deltaPts.append(self.phi.phi(cpoint))

        self.deltaConfig = np.array(deltaPts)

        # Break up the array, and store the opinions about each
        # neighbor in the neighbor list.  We do it this way in case
        # the neighbor list has changed since the marshaling.
        machineNames = [ self.deltaNames[i].split("/")[0] \
                             for i in range(0, len(self.deltaNames), 2) ]

        print "mnames:", machineNames
        for nm,dc in zip(machineNames, 
                         np.hsplit(self.deltaConfig,
                                   self.deltaConfig.shape[1]/2)):

            # Record the advice given to that robot.
            # print "setting advice", nm, dc
            self.setAdvice(nm, dc)

        #print str(self.deltaConfig)

        # Notify each neighbor of our opinion (and record their
        # responses).
        messageProduct = [ 1.0 ] * self.npoints
        for nb in self.neighbors:
            print "about to advise:", nb.name

            # If we don't already have an opinion about where this
            # robot should be then pass for the moment and we'll get
            # it the next time around.
            if not nb.lastQuestion.points:
                break

            m = MRFQueryRequest(source_stamp = rospy.Time.now(),
                                asker = self.name,
                                asked = nb.name,
                                question = nb.lastQuestion.points)
            print "advising: ", nb.name
            r = nb.advise(m)
            if r.reply:
                nb.lastReply.points = r.reply
                nb.lastReply.source_stamp = r.source_stamp
                messageProduct = [ lr.point[0] * mp \
                                       for lr, mp in zip(r.reply,
                                                         messageProduct) ]

        # Resample based on the neighbor's responses.
        desiredConfig = self.resample(self.deltaConfig, messageProduct)

        # The first set of coordinates in this is the desired place
        # for us to move.
        moves = desiredConfig[:,(0,1)]

        self.goThatWay(moves)

        self.busy = False

    def displayConf(self, name, configArray):
        """
        Print the configuration array, or rather a mean of it.
        """
        out = []
        for row in configArray.transpose():
            out.append(np.mean(row))

        fmt = name + " " + self.name + ": (" + "%.3f," * len(out) + ")"
        return fmt % tuple(out)


    def goThatWay(self, moves):
        """
        Takes an array of directions to move in and selects a point in
        space in that direction.  The choice of point is fairly
        arbitrary.  We try to multiply the direction by a factor large
        enough that it won't be within the gnav.zeroDistance of the
        current location, unless the intent is really that we should
        not move.  (That's what the kGo factor is for.)
        """
        kGo = 2.0

        print "moves", moves

        meanMove =  [ np.mean(moves[:, 0]), np.mean(moves[:, 1]) ]
        sumsq = sum([d**2 for d in meanMove])**0.5

        # If the target point is close, don't normalize.  Otherwise, set
        # a goal in the general direction
        if sumsq > 1.0:
            meanMove = [ kGo * x/sumsq for x in meanMove ]

        self.goal = (self.pos.means[0] + meanMove[0],
                     self.pos.means[1] + meanMove[1], 0.0)

        print "We're at: (%.3f,%.3f)" % (self.pos.means[0], self.pos.means[1])
        print "headed to: (%.3f,%.3f)" % (self.goal[0], self.goal[1])

        # Eventually this should publish to a goal-setting topic, to be
        # read by some goal-setter over at gnav.
        self.goalPub.publish(Pt(point=self.goal))


    def stepThatWay(self):
        """
        Not used.
        """

        fX = self.goal[0] - self.pos.means[0]
        fY = self.goal[1] - self.pos.means[1]

        fM = math.hypot(fX, fY)
        fD = math.atan2(fY, fX)

        # Convert to robot frame
        fDR = fD - self.pos.means[2]
        if math.fabs(fDR) > math.pi:
            fDR -= math.copysign(2 * math.pi, fDR)

        if math.fabs(fDR) > math.pi/10.0:
            provX = 0.0
        else:
            provX = min(self.maxSpeed, self.kSpeed * fM)

        provZ = math.fabs(self.kTurn * fDR)
        provZ = min(self.maxTurn, provZ)
        provZ = math.copysign(provZ, fDR)

        twist = Twist()
        twist.linear.x = provX
        twist.angular.z = provZ

        return twist


    def weightedSample(self, pointProbs, numSamples):
        """
        The following sampling algorithm is adapted from a sneaky
        algorithm for coming up with a selection of N random numbers
        between 0 and Q.  The idea is that the probability that all N
        of the numbers are less than some X is P=(X/Q)**N.  Solve for
        X in terms of P, and you get an equation that will pick the
        largest number in that distribution for some random P.  Do
        that N times, and you get N samples.
    
        The input is an indexed array of probabilities (use
        enumerate(P) for the input, e.g. and the number of samples to
        take from that array.  The output is an iterator that will
        provide the indices you can use to sample the original array
        with, as in:
    
        output = locArray[weightedSample(enumerate(locProbs), n)

        This won't exactly work, since the enumerate has to be turned
        into a sequence before it can be subscripted (as below) and
        the same is true of the function output.

        For more: stackoverflow.com/questions/2140787
        """

        total = sum(prob for i, prob in pointProbs)
        assert(not math.isnan(total))
        j = 0
        i, prob = pointProbs[j]
        while numSamples:
            x = total * (1 - np.random.random() ** (1.0/numSamples))
            total -= x
            while x > prob:
                x -= prob
                j += 1
                i, prob = pointProbs[j]
            prob -= x
            yield i
            numSamples -= 1

    def resample(self, array, ratings):
        """
        Resamples the distribution represented by the samples in
        array, based on the list of ratings.  There should be one
        rating for each row of the array, and each rating should be
        greater than zero and less than or equal to 1.0.  The ratings
        list need not be normed.
        """
        #print "resample according to: ", ratings

        newseq = self.weightedSample([(i,p) for i,p in enumerate(ratings)], 
                                     len(ratings))
        #print "comes up with: ", [p for p in newseq]

        wiggle = lambda x: self.std * (np.random.random() - 0.5) + x

        out = []
 
        for pt in array[ [ i for i in newseq ], :]:
            out.append([ wiggle(pt[0]), wiggle(pt[1]) ])

        return np.array(out)
