#!/bin/bash
set -eu
cd /code/dayatani_chatbot/ && python manage.py migrate 
exec "$@"
