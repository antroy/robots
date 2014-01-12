#!/usr/bin/python
import sys
from threading import Thread
import Queue
import logging
from robot import *

class AntBot(Robot):
    name = "DoomBot"
    colour = "000000"
    alt_colour = "FFFF00"

    def start(self):
        self.message("Hello??")
        self.shoot(20)

    def on_tick(self):
        self.shoot(10)

    def Radar(self, distance, type, angle):
        logging.info("Radar received: dist: %s; type: %s; angle: %s" % (distance, type, angle))

    def Energy(self, level):
        self.energy = float(level)
        logging.info("Energy: %s" % self.energy)

    def GameStarts(self):
        self.game_started = True

start(AntBot)
