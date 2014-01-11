#!/usr/bin/python
import sys
from threading import Thread
import Queue
import logging

logging.basicConfig(filename='robot.log',level=logging.DEBUG)

Q = Queue.Queue()

class Listener(object):
    def __init__(self):
        self.running = True

    def stop(self):
        self.running = False

    def __call__(self):
        while self.running:
            message=sys.stdin.readline().strip()
            logging.debug("Message Received: %s" % message)
            Q.put(message)

class Robot(object):
    def __init__(self, queue, listener):
        self.queue = queue
        self.listener = listener
        self.run = True
        self.game_started = False

        self.start_listener()

    def start_listener(self):
        while self.run:
            message = self.queue.get(True).split()
            name = message[0]
            params = message[1:]
            logging.debug("Robot Received: %s" % message)
            try:
                getattr(self, message[0])(*params)
            except Exception, e:
                logging.error("No method called %s: %s" % (message, e.message))

    def Quit(self):
        logging.info("Quitting!!")
        self.run = False
        self.listener.stop()

    def Radar(self, distance, type, angle):
        logging.info("Radar received: dist: %s; type: %s; angle: %s" % (distance, type, angle))

    def Energy(self, level):
        self.energy = float(level)
        logging.info("Energy: %s" % self.energy)

    def GameStarts(self):
        self.game_started = True

def start():
    listener = Listener()

    t = Thread(target=listener)
    t.daemon = False
    t.start()

    robot = Robot(Q, listener)

start()
