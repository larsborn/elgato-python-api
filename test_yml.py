#!/usr/bin/env python3
import argparse
import os
import yaml, sys
from typing import Dict
import colour

parser = argparse.ArgumentParser()
parser.add_argument('--config', default='config.yml')
parser.add_argument('--mode', default='rotate')
args = parser.parse_args()

if not os.path.exists(args.config):
    print(f"could not find config file {args.config}. Exiting")
    sys.exit(1)

with open(args.config, "r") as f:
    yml_config = yaml.safe_load(f)

if args.mode not in yml_config['modes'].keys():
    print(f"mode {args.mode} not specified in config. Exiting")
    sys.exit(2)

colors = {}
for k,v in yml_config['colors'].items():
    r, g, b = map(int, v.split(','))
    print(r/255,g/255,b/255)
    colors[k] = colour.Color(rgb=(r/255,g/255,b/255))
print(colors)