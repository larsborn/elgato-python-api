#!/usr/bin/env python3
import argparse
import json
import os
import random
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


class ElgatoApi:
    def __init__(self, base_url: str, light_id: int = 0):
        self._endpoints = Endpoints(base_url)
        self._light_id = light_id

        self._session = requests.session()
        self._session.mount('https://', FixedTimeoutAdapter())
        self._session.mount('http://', FixedTimeoutAdapter())

    def get_light_raw(self) -> Dict:
        response = self._session.get(self._endpoints.lights)
        response.raise_for_status()
        data = response.json()
        return data['lights'][self._light_id]

    def toggle_lights(self):
        data = self.get_light_raw()
        for i in range(360):
            data['hue'] = i
            print(json.dumps(data))
            response = self._session.put(self._endpoints.lights, json={'lights': [data]})
            response.raise_for_status()

    def toggle_random(self):
        data = self.get_light_raw()
        for i in range(500):
            data['hue'] = random.randint(0, 359)
            print(json.dumps(data))
            response = self._session.put(self._endpoints.lights, json={'lights': [data]})
            response.raise_for_status()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default=os.getenv('BASE_URL', 'http://192.168.178.64:9123'))
    parser.add_argument('--random', default=False, action='store_true')
    args = parser.parse_args()
    api = ElgatoApi(args.base_url)
    while True:
      if args.random:
        api.toggle_random()
      else:
        api.toggle_lights()


if __name__ == '__main__':
    main()
