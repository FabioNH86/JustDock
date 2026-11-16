#!/bin/bash

# --- LÓGICA PARA ENLACES SIMBÓLICOS ---
# Detecta la ruta real del archivo, incluso si se lanza desde un enlace como ./inicio
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
PROJECT_ROOT="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

# --- VARIABLES ---
# jimag/ y jimag-scripts/ son carpetas hermanas dentro del mismo directorio raíz
REPO_ROOT="$(dirname "$PROJECT_ROOT")"
VENV_ACTIVATE="$PROJECT_ROOT/.venv/bin/activate"
export HOMEDIR="$HOME"
export PROJECTROOT="$PROJECT_ROOT"
export SCRIPTDIR="$REPO_ROOT/jimag-scripts"
SESSION="jimag"
URL="http://localhost:8000"

if [ ! -d "$SCRIPTDIR" ]; then
  echo "AVISO: no se encontró $SCRIPTDIR" >&2
fi

# --- LIMPIEZA ---
tmux kill-session -t "$SESSION" 2>/dev/null
fuser -k 8000/tcp 6380/tcp 2>/dev/null

# --- COMANDOS ---
CMD_ENV="export HOMEDIR='$HOMEDIR' PROJECTROOT='$PROJECTROOT' SCRIPTDIR='$SCRIPTDIR'"
CMD_DJANGO="cd '$PROJECT_ROOT' && source '$VENV_ACTIVATE' && $CMD_ENV && python manage.py runserver"
CMD_REDIS="redis-server --port 6380"
CMD_WORKER="cd '$PROJECT_ROOT' && source '$VENV_ACTIVATE' && $CMD_ENV && python manage.py rqworker"

# --- EJECUCIÓN (Worker arriba, Django y Redis abajo) ---
tmux new-session -d -s "$SESSION" -n "Server"

# 1. Worker en el panel superior
tmux send-keys -t "$SESSION" "$CMD_WORKER" C-m

# 2. Panel inferior: Django a la izquierda
tmux split-window -v -t "$SESSION"
tmux send-keys -t "$SESSION" "$CMD_DJANGO" C-m

# 3. Redis a la derecha
tmux split-window -h -t "$SESSION"
tmux send-keys -t "$SESSION" "$CMD_REDIS" C-m

tmux select-pane -t "$SESSION:0.0"
tmux resize-pane -t "$SESSION:0.0" -D 5

echo "Iniciando servicios desde la ruta real: $PROJECT_ROOT"
echo "Scripts de acoplamiento: $SCRIPTDIR"

# --- NAVEGADOR (en segundo plano, solo si hay entorno gráfico) ---
if [ -n "$DISPLAY$WAYLAND_DISPLAY" ] && command -v xdg-open >/dev/null; then
  ( sleep 3; xdg-open "$URL" >/dev/null 2>&1 ) &
else
  echo "Abre $URL en el navegador."
fi

# --- CONECTARSE A LA SESIÓN (sin depender de gnome-terminal) ---
# Para salir sin detener los servicios: Ctrl+B y luego D
# Para volver a entrar más tarde: tmux attach -t jimag
if [ -n "$TMUX" ]; then
  tmux switch-client -t "$SESSION"
elif [ -t 1 ]; then
  tmux attach-session -t "$SESSION"
else
  echo "Servicios corriendo en segundo plano. Conéctate con: tmux attach -t $SESSION"
fi
