# T2DM-sim
Quite a few of the classes and logic is adapted from the repository https://github.com/jxx123/simglucose, where this one is a little bit different. It instead uses a T2DM simulator ODE and instead of having an agent directly affect the environment, it is built in such a way to be more of a forecasting and recommendation of actions with a set uncertainty environment rather than directly interacting with it. Most of the code example and docs from simglucose therefore work the same.

The type 2 diabetes simulator classes were adapted from this repository https://gitlab.com/aau-adapt-t2d/aau-t2d-simulator to port from Matlab to Python.

to install for local development, simply enter this repo folder and type "pip install -e ." and it will be available in your environment.
