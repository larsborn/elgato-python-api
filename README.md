# elgato-python-api

A simple API to control an Elgato Light Strip from the CLI. Configure modes with a yaml file and run the strip with the desired colors.

## Getting started

Create a virtual environment with a method of your choice and activate it, e.g.
```
python3 -m venv env
. env/bin/activate
```
Install all the requirements
```
pip install -r requirements.txt
```
Find the IP of your Elgato Light Strip, e.g. `192.168.178.64`, and put it into the `config.yml`. Run the script: 
```python main.py --config config.yml```
Specify a mode from the config with `--mode`, e.g. `--mode random`. See below to add custom modes.

## Adding colors and modes

### Colors

Add colors by expanding the `colors` dictionary in the config file. The syntax is `colorname : r,g,b` with values in `[0,255]`.

### Modes

Define modes with custom names. Every mode needs to define a type, currently there are
- random
- rotate
- linear

`random` just selects a random hue.

`rotate` cycles through the hues from 0 to 255.

`linear` cycles through the specified colors with linear interpolation. You can change the amount of steps between colors by adding `steps: amount` to the mode definition.

