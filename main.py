#!/usr/bin/env python3
import argparse
import json
import os
import random
import yaml, sys
from typing import Dict
import colour

import requests.adapters


class FixedTimeoutAdapter(requests.adapters.HTTPAdapter):
    def send(self, *pargs, **kwargs):
        if kwargs['timeout'] is None:
            kwargs['timeout'] = 10
        return super(FixedTimeoutAdapter, self).send(*pargs, **kwargs)


class Endpoints:
    def __init__(self, base_url: str):
        self.settings = f'{base_url}/elgato/lights/settings'
        """
        {
          "powerOnBehavior": 1,
          "powerOnHue": 40.0,
          "powerOnSaturation": 15.0,
          "powerOnBrightness": 40,
          "switchOnDurationMs": 150,
          "switchOffDurationMs": 400,
          "colorChangeDurationMs": 150
        }
        """

        self.info = f'{base_url}/elgato/accessory-info'
        """
        {
          "productName": "Elgato Light Strip",
          "hardwareBoardType": 70,
          "firmwareBuildNumber": 219,
          "firmwareVersion": "1.0.4",
          "serialNumber": "AB12C3E45678",
          "displayName": "Elgato Light Strip 123A",
          "features": [
            "lights"
          ],
          "wifi-info": {
            "ssid": "WiFi on ICE",
            "frequencyMHz": 2400,
            "rssi": -53
          }
        }
        """

        self.lights = f'{base_url}/elgato/lights'
        """
        {
          "numberOfLights": 1,
          "lights": [
            {
              "on": 1,
              "hue": 0,
              "saturation": 100.0,
              "brightness": 100
            }
          ]
        }
        """

class ColorRotator:
    def __init__(self, colors_from_config: dict, mode: dict):
        self._step = 0
        self._gradient_steps = 10
        # prepare our color dictionary from config
        self._colors = {}
        for k, v in colors_from_config.items():
            r, g, b = map(int, v.split(','))
            self._colors[k] = colour.Color(rgb=(r/255,g/255,b/255))

        # create the gradients:
        gradient_color_generators = []
        for i in range(len(mode['colors']) - 1):
            c1 = self._colors[mode['colors'][i]]
            c2 = self._colors[mode['colors'][i + 1]]
            gradient_color_generators.append(c1.range_to(c2, self._gradient_steps))
        self._color_rotation = []
        for range_generator in gradient_color_generators:
            for color in range_generator:
                self._color_rotation.append(color)

    def get_next_color(self):
        color = self._color_rotation[self._step]
        self._step + 1
        if self._step == len(self._color_rotation):
            self._step = 0
        return color

class ElgatoConfig:
    def __init__(self, yml_config: dict, mode: str):
        self._ip = yml_config['ip']
        self.base_url = f"http://{self._ip}:9123"
        self.verbose = yml_config['verbose']
        self._mode = yml_config['modes'][mode]
        self._hue_change_type = self._mode['type']

        if self._hue_change_type == 'random':
            self.get_next_hue = self.get_next_hue_random
        if self._hue_change_type == 'rotate':
            self.get_next_hue = self.get_next_hue_rotate
        if self._hue_change_type == 'linear':
            if len(self._mode['colors']) < 2:
                print(f"mode {self._mode} has less than 2 colors. Please specify at least two. Exiting")
                sys.exit(3)
            self._colorRotator = ColorRotator(
                yml_config['colors'],
                self._mode)
            self.get_next_hue = self.get_next_hue_linear

    def get_next_hue_random(self):
        return random.randint(0, 359)

    def get_next_hue_rotate(self, hue: int):
        return (hue + 1) % 360

    def get_next_hue_linear(self):
        color = self._colorRotator.get_next_color()
        return color.hue * 360

class ElgatoApi:
    def __init__(self, config: ElgatoConfig):
        self._config = config
        self._endpoints = Endpoints(config.base_url)
        self._light_id = 0

        self._session = requests.session()
        self._session.mount('https://', FixedTimeoutAdapter())
        self._session.mount('http://', FixedTimeoutAdapter())

    def get_light_raw(self) -> Dict:
        response = self._session.get(self._endpoints.lights)
        response.raise_for_status()
        data = response.json()
        return data['lights'][self._light_id]
    
    def run(self):
        while True:
            data = self.get_light_raw()
            if (self._config.verbose):
                print(json.dumps(data))
            data['hue'] = self._config.get_next_hue(data['hue'])
            response = self._session.put(self._endpoints.lights, json={'lights': [data]})
            response.raise_for_status()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.yml')
    parser.add_argument('--mode', default='rotate')
    args = parser.parse_args()

    # check if config file exists
    if not os.path.exists(args.config):
        print(f"could not find config file {args.config}. Exiting")
        sys.exit(1)

    # read config file
    with open(args.config, "r") as f:
        yml_config = yaml.safe_load(f)

    # check if specified mode is defined in config
    if args.mode not in yml_config['modes'].keys():
        print(f"mode {args.mode} not specified in config. Exiting")
        sys.exit(2)

    # for every color in every mode, check if we have a definition for it
    color_lists = [v['colors'] for _, v in yml_config['modes'].items() if 'colors' in v]
    # flatten
    all_colors = [i for sublist in color_lists for i in sublist]
    for color in all_colors:
        if color not in yml_config['colors'].keys():
            print(f"did not recognize color {color}, please define it in the config. Exiting")
            sys.exit(3)
    
    # create config obj and api, run it
    conf = ElgatoConfig(yml_config, args.mode)
    api = ElgatoApi(conf)
    api.run()

if __name__ == '__main__':
    main()
