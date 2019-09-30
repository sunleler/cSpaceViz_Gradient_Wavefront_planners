import yaml
import math
from BugAlgorithms import factory


#
# @brief      Class for the bug robot
#
class BugRobot:

    #
    # @brief      Constructor for the BugRobot object
    #
    # @param      self            The BugRobot object
    # @param      configFileName  The YAML configuration file name
    #                             which contains the start / goal state coords
    # @param      workspace       The workspace object the robot operates in
    # @param      algorithmStr    A string containing name of the control
    #                             / planning algorithmStr the robot uses:
    #                                 - 'bug1'
    #                                 - 'bug2'
    #
    def __init__(self, configFileName, workspace, algorithmStr):

        self.workspace = workspace

        (q0, qG) = self.getStartAndGoalStatesFromFile(configFileName)
        self.startState = q0
        self.goalState = qG

        self.stateHistory = []
        self.currentState = self.startState
        self.stateHistory.append(self.currentState)

        self.headingHistory = []
        self.rotateToGoal()

        self.timeStepHistory = []

        # defines the linear velocity of the robot when moving
        self.velocityMag = 0.5

        # 2-norm radius tolerance to be considered "at the goal"
        self.atGoalTolerance = 0.1

        # define how far in front of the robot the bump sensor is
        # this is effectively the distance detection limit, and how far away
        # the robot will stay from obstacles
        self.sensorLengthFromBody = 0.1

        bugAlgorithm = factory.get_BugAlgorithm(self,
                                                algorithmType=algorithmStr)
        self.bugAlgorithm = bugAlgorithm

    #
    # @brief      returns the start and goal location lists for the robot
    #
    # @param      configFileName  The YAML configuration file name
    #
    # @return     The start and goal states lists from the config filename
    #
    @staticmethod
    def getStartAndGoalStatesFromFile(configFileName):

        with open(configFileName, 'r') as stream:
            config_data = yaml.safe_load(stream)

        startLoc = config_data['qStart']
        goalLoc = config_data['qGoal']

        return (startLoc, goalLoc)

    #
    # @brief      Trys to move BugRobot from startState to goalState using
    #             bugAlgorithm as a controller
    #
    # @param      self  The BugRobot object
    #
    # @return     True if the robot reaches goalState, False if not
    #
    def deploy(self):

        self.bugAlgorithm.controlRobotToGoal()
        return True

    #
    def moveForward(self, heading, delta_t):

        velocityMag = self.velocityMag

        deltaX = velocityMag * heading[0] * delta_t
        deltaY = velocityMag * heading[1] * delta_t

        newXPos = self.currentState[0] + deltaX
        newYPos = self.currentState[1] + deltaY

        return (newXPos, newYPos)

    def isAtGoal(self):

        (xDist, yDist) = vectorComponentDiff(self.goalState, self.currentState)
        distToGoal = vectorMag([xDist, yDist])

        return (distToGoal <= self.atGoalTolerance)

    def rotateToGoal(self):

        goalHeading = computeHeading(self.currentState, self.goalState)
        self.currentHeading = goalHeading
        self.headingHistory.append(self.currentHeading)

    def getCollisionStatus(self, robotLoc):

        sensorLoc = self.getSensorLocation(robotLoc)

        # three cases:
        #     - robot and sensor NOT COLLIDED -> all good
        #     - robot and sensor COLLIDED -> need to back up
        #     - robot NOT COLLIDED, sensor COLLIDED -> real collision, stop
        robotCollided = self.workspace.objectCollides(robotLoc)
        sensorCollided = self.workspace.objectCollides(sensorLoc)

        if (not robotCollided) and (not sensorCollided):
            status = 'OK'
        elif robotCollided and sensorCollided:
            status = 'INSIDE_OBSTACLE'
        elif (not robotCollided) and sensorCollided:
            status = 'COLLISION'
        else:
            status = 'UNKNOWN'

        return status

    def getSensorLocation(self, robotLoc):

        currHeading = self.currentHeading
        currHeadingX = currHeading[0]
        currHeadingY = currHeading[1]

        currLocX = robotLoc[0]
        currLocY = robotLoc[1]

        sensorX = currLocX + currHeadingX * self.sensorLengthFromBody
        sensorY = currLocY + currHeadingY * self.sensorLengthFromBody

        return [sensorX, sensorY]

    def setRobotState(self, newRobotState):

        self.currentState = newRobotState
        self.stateHistory.append(newRobotState)


def vectorComponentDiff(vec1, vec2):

    diffX = vec2[0] - vec1[0]
    diffY = vec2[1] - vec1[1]

    return (diffX, diffY)


def vectorMag(vec):

    x = vec[0]
    y = vec[1]
    magnitude = math.sqrt(x**2 + y**2)

    return magnitude


def computeHeading(currentPosition, targetObjectPosition):

    (headingX, headingY) = vectorComponentDiff(currentPosition,
                                               targetObjectPosition)

    # need to normalize the heading to get a unit vector heading
    headingMag = vectorMag([headingX, headingY])
    headingX /= headingMag
    headingY /= headingMag

    return [headingX, headingY]
