#!/bin/sh
source myvenv/bin/activate
python -m flask --app /home/user/elearning_platform/run run -p $PORT --debug