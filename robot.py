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

WARNINGS = {
        "0": "UNKNOWN_MESSAGE",
        "1": "PROCESS_TIME_LOW",
        "2": "MESSAGE_SENT_IN_ILLEGAL_STATE",
        "3": "UNKNOWN_OPTION",
        "4": "OBSOLETE_KEYWORD",
        "5": "NAME_NOT_GIVEN",
        "6": "COLOUR_NOT_GIVEN"
  }

def send(*message_parts):
    message = " ".join([str(p) for p in message_parts])
    logging.info("Sending: '%s'" % message)
    sys.stdout.flush()
    sys.stdout.write("%s\n" %  message)
    sys.stdout.flush()

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

class MessageSender(object):
    def sendName(self):
        send("Name", self.name)

    def sendColour(self):
        send("Colour", self.colour, self.alt_colour)

    def setBlocking(self, blocking=True):
        if blocking:
            self.option(USE_NON_BLOCKING, 0)
        else:
            self.option(SIGNAL, 10)

    def option(self, type, value):
        send("RobotOption", type, value)

    def accelerate(self, amount):
        send("Accelerate %.2f" % amount)

    def shoot(self, power):
        send("Shoot", 20)

    def message(self, message):
        send("Print", message)

class Robot(MessageSender):
    def __init__(self, queue, listener):
        self.queue = queue
        self.listener = listener
        self.run = True
        self.game_started = False

        self.start_listener()

    def on_tick(self):
        #logging.debug("Tick")
        pass

    def start_listener(self):
        while self.run:
            while True:
                try:
                    #logging.debug("Getting next message:")
                    message = self.queue.get(False).split()
                    name = message[0]
                    params = message[1:]
                    logging.debug("Robot Received: %s" % message)
                    try:
                        getattr(self, message[0])(*params)
                    except Exception, e:
                        logging.error("No method called %s: %s" % (message, e.message))
                    finally:
                        self.queue.task_done()
                except Queue.Empty:
                    #logging.debug("No more messages atm")
                    break

            self.on_tick()
            time.sleep(0.1)

    def Initialize(self, first):
        first = int(first)
        if first == 1:
            logging.info("Sending Name and Colour")
            self.sendName()
            self.sendColour()
        self.start()

    def Warning(self, type, message):
        logging.warn("%s: %s" % (WARNINGS[type], message))

    def Quit(self):
        logging.info("Quitting!!")
        self.run = False
        self.listener.stop()

def start(classname):
    logging.info("Starting Robot")
    send("RobotOption", USE_NON_BLOCKING, 0)
    listener = Listener()

    t = Thread(target=listener)
    t.daemon = False
    t.start()

    robot = classname(Q, listener)

