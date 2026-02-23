#!/bin/bash

# --- LÓGICA PARA ENLACES SIMBÓLICOS ---
# Esto detecta la ruta real del archivo, incluso si lo lanzas desde un link como ./inicio
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # Mientras sea un enlace simbólico...
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" 
done
PROJECT_ROOT="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

# --- VARIABLES ---
VENV_ACTIVATE="$PROJECT_ROOT/.venv/bin/activate"
export HOMEDIR="$HOME"
export SCRIPTDIR="$HOME/.local/src/jimag-scripts"
SESSION="jimag"

# --- LIMPIEZA ---
tmux kill-session -t $SESSION 2>/dev/null
fuser -k 8000/tcp 6380/tcp 2>/dev/null 

# --- COMANDOS ---
CMD_DJANGO="cd '$PROJECT_ROOT' && source '$VENV_ACTIVATE' && python manage.py runserver"
CMD_REDIS="redis-server --port 6380"
CMD_WORKER="cd '$PROJECT_ROOT' && source '$VENV_ACTIVATE' && export HOMEDIR='$HOMEDIR' && export SCRIPTDIR='$SCRIPTDIR' && python manage.py rqworker"

# --- EJECUCIÓN (Worker arriba, Django y Redis abajo) ---
tmux new-session -d -s $SESSION -n "Server"

# 1. El primer comando ocupa el panel principal (SUPERIOR)
# Ahora ponemos aquí el Worker
tmux send-keys -t $SESSION "$CMD_WORKER" C-m

# 2. Creamos el panel inferior (se divide el espacio de abajo)
tmux split-window -v -t $SESSION

# 3. Ponemos Django en el panel inferior izquierdo
tmux send-keys -t $SESSION "$CMD_DJANGO" C-m

# 4. Dividimos el panel inferior a la mitad para Redis (inferior derecho)
tmux split-window -h -t $SESSION
tmux send-keys -t $SESSION "$CMD_REDIS" C-m

# Seleccionamos el panel 0 (Worker) para que el cursor empiece ahí
tmux select-pane -t 0

tmux resize-pane -D 5

gnome-terminal --title="Jimag System" -- tmux attach-session -t $SESSION &

# --- NAVEGADOR ---
echo "Iniciando servicios desde la ruta real: $PROJECT_ROOT"
sleep 3
xdg-open "http://localhost:8000"