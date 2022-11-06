# elgato-python-api

A simple API to control an Elgato Light Strip from the CLI. Currently the script either cycles through the hue from 0 to 359 or changes the hue randomly. Saturation and brigthness are kept as is.

## Getting started

Find the IP of your Elgato Light Strip, e.g. `192.168.178.64`. 

Run the script: `python3 main.py --base-url "http://192.168.178.64:9123"`. If you want the colors to be selected randomly, add the `--random` flag: 

`python3 main.py --base-url "http://192.168.178.64:9123" --random`.
