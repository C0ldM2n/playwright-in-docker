#!/bin/bash -e

Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
xvfb_pid=$!

export DISPLAY=:99

poetry run python ./src/main.py

kill $xvfb_pid