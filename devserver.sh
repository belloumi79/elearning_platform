#!/bin/sh
source myvenv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=/home/user/elearning_platform/config/serviceAccountKey.json
python -m flask --app /home/user/elearning_platform/run run -p $PORT
