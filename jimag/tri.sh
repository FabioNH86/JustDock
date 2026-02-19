#!/bin/bash

cd /home/fabio-noriega/.local/src/jimag/

source .venv/bin/activate

export HOMEDIR="/home/fabio-noriega"
export SCRIPTDIR="/home/fabio-noriega/.local/src/jimag-scripts"

# Abrir ventana 1: Django
gnome-terminal --tab --title="Django" -- bash -c "source .venv/bin/activate; python manage.py runserver; exec bash"

# Abrir ventana 2: Redis
gnome-terminal --tab --title="Redis" -- bash -c "redis-server --port 6380; exec bash"

# Abrir ventana 3: Worker
gnome-terminal --tab --title="Worker" -- bash -c "source .venv/bin/activate; python manage.py rqworker; exec bash"