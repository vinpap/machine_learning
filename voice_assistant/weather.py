import logging

import requests
import geocoder

from interfaces import IIntent_slot
from environment import Environment

# This file should contain your API key for openweathermap (not provided here)
import keys



class Weather(IIntent_slot):

    def __init__(self):

        self._env = Environment.get_instance()

        self.intent_id = "weather"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self.lang = self._env.language

        try:
            self.__location = self._env.config["WEATHER"]["Aubière"]
        except KeyError:
            logging.warning("Unable to retrieve city name for the weather forecast feature. Switching to geolocation instead, accuracy may not be as good")
            self.__location = self.__find_current_city()

        logging.info(f"Weather forecast will be based on this location: {self.__location}")

        # On cherche la ville actuelle dans les paramètres
        # Si on ne la trouve pas, on essaie de géolocaliser


    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")

        ...

    def __find_current_city(self):

        coordinates = geocoder.ip('me')
        return coordinates.city

    def __retrieve_weather():

        api_key = keys.openweather_key
        base_url = "http://api.openweathermap.org/data/2.5/weather?"
