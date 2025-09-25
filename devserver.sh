#!/bin/sh
source myvenv/bin/activate
# Firebase GOOGLE_APPLICATION_CREDENTIALS removed; we use Supabase.
python -m flask --app run run -p ${PORT:-5000}
