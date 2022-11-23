#!/usr/bin/env python3
import argparse
import json
import os
import random
import yaml, sys
from typing import Dict

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

class ElgatoConfig:
    def __init__(self, yml_config: dict, mode: str):
        self._ip = yml_config['ip']
        self.base_url = f"http://{self._ip}:9123"
        self.verbose = yml_config['verbose']

        self._colors = yml_config['colors']
        self._mode = yml_config['modes'][mode]
        self._hue_change_type = self.mode['type']

    def get_next_hue(self, hue: int):
        if self._hue_change_type == 'random':
            return random.randint(0, 359)
        if self._hue_change_type == 'rotate':
            return (hue + 1) % 360
        if self._hue_change_type == 'linear':
            # TODO
            return hue
        print(f"hue changing type {self._hue_change_type} not recognized, not changing hue.")
        return hue

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

    if not os.path.exists(args.config):
        print(f"could not find config file {args.config}. Exiting")
        sys.exit(1)

    with open(args.config, "r") as f:
        yml_config = yaml.safe_load(f)
        conf = ElgatoConfig(yml_config, args.mode)

    if args.mode not in yml_config['modes'].keys():
        print(f"mode {args.mode} not specified in config. Exiting")
        sys.exit(2)

    api = ElgatoApi(conf)
    api.run()

if __name__ == '__main__':
    main()
