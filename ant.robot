#!/usr/bin/python
import sys
from threading import Thread
import Queue
import logging
from robot import *

class AntBot(Robot):
    name = "AntsBot"
    colour = "000000"
    alt_colour = "FFFF00"

    def initialize(self):
        self.message("New Game Initializing")

    def start(self):
        logging.info("Starting Game")
        self.accelerate(0.5)

    def on_tick(self, turn):
        if turn % 3 == 0:
            self.shoot(10)

    def wall_spotted(self, r):
        logging.debug("Distance from Wall: %s" % r.distance)
        if r.distance < 10.0:
            self.rotate(0.7, 2.0)

start(AntBot)
