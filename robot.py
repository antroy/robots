#!/usr/bin/python
import sys
from threading import Thread
import Queue
import logging
import time

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename='/var/log/robots.log',level=logging.DEBUG)

Q = Queue.Queue()

# Option Types:
USE_NON_BLOCKING=3
SIGNAL=2

WARNINGS = [
    "UNKNOWN_MESSAGE",
    "PROCESS_TIME_LOW",
    "MESSAGE_SENT_IN_ILLEGAL_STATE",
    "UNKNOWN_OPTION",
    "OBSOLETE_KEYWORD",
    "NAME_NOT_GIVEN",
    "COLOUR_NOT_GIVEN"
]

GAME_OPTIONS = [
  "ROBOT_MAX_ROTATE",
  "ROBOT_CANNON_MAX_ROTATE",
  "ROBOT_RADAR_MAX_ROTATE",
  "ROBOT_MAX_ACCELERATION",
  "ROBOT_MIN_ACCELERATION",
  "ROBOT_START_ENERGY",
  "ROBOT_MAX_ENERGY",
  "ROBOT_ENERGY_LEVELS",
  "SHOT_SPEED",
  "SHOT_MIN_ENERGY",
  "SHOT_MAX_ENERGY",
  "SHOT_ENERGY_INCREASE_SPEED",
  "TIMEOUT",
  "DEBUG_LEVEL",
  "SEND_ROBOT_COORDINATES"
]

OBJECT_TYPES = [
  "robot",
  "shot",
  "wall",
  "cookie",
  "mine",
  "last_object_type"
]

class Listener(object):
    def __init__(self):
        self.running = True

    def stop(self):
        self.running = False

    def __call__(self):
        while self.running:
            message=sys.stdin.readline().strip()
            if message:
                logging.debug("Message Received: %s" % message)
                Q.put(message)

def send_to_server(*message_parts):
    message = " ".join([str(p) for p in message_parts])
    logging.info("Sending: '%s'" % message)
    sys.stdout.flush()
    sys.stdout.write("%s\n" %  message)
    sys.stdout.flush()

class MessageSender(object):
    def send(self, *message_parts):
        if not self.dead:
            send_to_server(*message_parts)

    def sendName(self):
        self.send("Name", self.name)

    def sendColour(self):
        self.send("Colour", self.colour, self.alt_colour)

    def setBlocking(self, blocking=True):
        if blocking:
            self.option(USE_NON_BLOCKING, 0)
        else:
            self.option(SIGNAL, 10)

    def option(self, type, value):
        self.send("RobotOption", type, value)

    def accelerate(self, amount):
        self.brake(0)
        self.send("Accelerate %.2f" % amount)

    def brake(self, percent):
        self.send("Brake", percent / 100.0)

    def shoot(self, power):
        self.send("shoot", 20)

    def rotate(self, angle, angular_velocity):
        self.send("RotateAmount", 7, angular_velocity, angle)

    def message(self, message):
        self.send("Print", message)

  #ROBOT_OPTION,
  #NAME,
  #COLOUR,
  #//  LOAD_DATA,
  #ROTATE,
  #ROTATE_TO,
  #ROTATE_AMOUNT,
  #SWEEP,
  #ACCELERATE,
  #BRAKE,
  #BREAK,
  #SHOOT,
  #PRINT,
  #DEBUG,
  #DEBUG_LINE,
  #DEBUG_CIRCLE

class Radar(object):
    def __init__(self, dist, obj_type, angle):
        self.distance = dist
        self.type = OBJECT_TYPES[obj_type]
        self.angle = angle

class MessageReceiver(object):
    def Initialize(self, first):
        self.options = {}
        first = int(first)
        if first == 1:
            logging.info("Sending Name and Colour")
            self.sendName()
            self.sendColour()
        self.initialize()

  #YOUR_NAME,
  #YOUR_COLOUR,
  #ROBOT_INFO,
  #ROTATION_REACHED,
  #ROBOTS_LEFT,
  #COLLISION,
    def GameStarts(self):
        self.game_started = True
        self.dead = False
        self.energy = 100.0
        self.time = 0.0
        self.speed = 0.0
        self.x = 0.0
        self.y = 0.0
        self.angle = 0.0
        self.cannon_angle = 0.0
        self.radar_angle = 0.0
        self.last_radar = None
        self.start()

    def Warning(self, type, message):
        logging.warn("%s: %s" % (WARNINGS[int(type)], message))

    def Energy(self, level):
        self.energy = float(level)
        logging.info("Energy: %s" % self.energy)

    def Radar(self, dist, obj_type, radar_angle):
        self.last_radar = Radar(float(dist), int(obj_type), float(radar_angle))

    def Info(self, time, speed, cannon_angle):
        self.time = time
        self.speed = speed
        self.cannon_angle = cannon_angle
        try:
            name = "%s_spotted" % self.last_radar.type
            logging.debug("Method: %s" % name)
            m = getattr(self, name)
            m(self.last_radar)
        except Exception, e:
            logging.error("Error: " + e.message)

    def Coordinates(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle

    def GameFinishes(self):
        pass

    def GameOption(self, opt_no, value):
        self.options[GAME_OPTIONS[int(opt_no)]] = float(value)
        logging.debug("Options: %s" % self.options)

    def Dead(self):
        self.dead = True

    def ExitRobot(self):
        logging.info("Quitting!!")
        self.run = False
        self.listener.stop()
        sys.exit(0)

    def radar_bleep(self, last_radar):
        pass

class Robot(MessageSender, MessageReceiver):
    def __init__(self, queue, listener):
        self.queue = queue
        self.listener = listener
        self.run = True
        self.dead = False
        self.game_started = False

        self.start_listener()

    def on_tick(self, turn):
        #logging.debug("Tick")
        pass

    def start_listener(self):
        while self.run:
            turn = 0
            while True:
                try:
                    #logging.debug("Getting next message:")
                    message = self.queue.get(False).split()
                    name = message[0]
                    params = message[1:]
                    logging.debug("Robot Received: %s" % message)
                    try:
                        getattr(self, message[0])(*params)
                    except AttributeError, e:
                        logging.error("No method called %s: %s" % (name, e.message))
                    except Exception, e:
                        logging.error("Failed to call %s(%s): %s" % (name, ",".join(params), e.message))
                    finally:
                        self.queue.task_done()
                except Queue.Empty:
                    #logging.debug("No more messages atm")
                    break

            turn += 1
            if self.game_started:
                self.on_tick(turn)
            time.sleep(0.1)

def start(classname):
    logging.info("Starting Robot")
    send_to_server("RobotOption", USE_NON_BLOCKING, 0)
    listener = Listener()

    t = Thread(target=listener)
    t.daemon = False
    t.start()

    robot = classname(Q, listener)

