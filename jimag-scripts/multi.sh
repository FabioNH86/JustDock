#!/bin/bash
set -x
set -e
#Para simular el comportamiento de este script, correr primero blind.sh y luego dejar predictions solo en output
#example: ./multi.sh --vinalvl 2 --num_modes 5 --pockets 1,3
#NOTE: max_pockets = 1 and pockets = 1 should yield the same result

# Detecta la carpeta donde reside este script (multi.sh)
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export SCRIPTDIR

export OBABEL="/usr/bin/obabel"

#Defaults
export WD=$(pwd)
export ID=$(pwd)/input
export OD=$(pwd)

export VINALVL=4
export NUM_MODES=5

echo "Running $@"

usage() {
	echo "Usage: $O [options] [--] [input file]"
	echo "Options:"
	echo "  --input <value>    Input directory (default: $ID)"
	echo "  --output <value>    Output directory (default: $OD)"
	echo "  --wd <value>    Working directory (default: $WD)"
	echo "  --vinalvl <value>    Level of exhaustiveness used by vina (default: $VINALVL)"
	echo "  --num_modes <value>    Maximum number of binding modes to generate (default: $NUM_MODES)"
	echo "  --chains <chain1,chain2,...>    Chains to run the docking on (default: all)"
	echo "  --pockets <rank1, rank2, rank3,...>    Rank of pockets to run the docking on (default: 1)"
	echo "  --max_pockets <value>    Maximum number of pockets to use (default: 1)"
	echo "  --preproc_done    Intended for webapp usage. Assumes clean protein and pocket files are already in output dir"
	echo "  --run_mode [predock,dock_only]   Intended for webapp usage."
}

while [[ "$#" -gt 0 ]]; do
	case $1 in 
		--input) export ID="$2"; shift ;;
		--output) export OD="$2"; shift ;;
		--wd) export WD="$2"; shift ;;
		--vinalvl) export VINALVL="$2"; shift ;;
		--num_modes) export NUM_MODES="$2"; shift ;;
		--chains) export CHAINS="$2"; shift ;;
		--pockets) export POCKETS="$2"; shift ;;
		--max_pockets) export MAX_POCKETS="$2"; shift ;;
		--preproc_done) export PREPROC=1; shift ;;
		--run_mode) run_mode="$2"; shift ;;
		--) shift; break ;;
		*) usage; exit 1;;
	esac
	shift
done

# Validación de Directorio de Trabajo y Ajuste de Salida
if [ -d "$WD" ]; then
    cd "$WD"
    # Convertimos a rutas absolutas reales para evitar confusiones de bash
    export WD=$(pwd)
    export ID=$(readlink -f "$ID")

    # --- INICIO DEL FIX DE RUTAS PARA DJANGO ---
    # Guardamos la ruta que viene del argumento para analizarla
    ORIGINAL_OD="$OD"
    
    # Si OD apunta a la raíz del contenedor (/app/media...), lo forzamos dentro del WD
    if [[ "$ORIGINAL_OD" == "/app/media"* ]]; then
        FOLDER_NAME=$(basename "$ORIGINAL_OD")
        export OD="$WD/$FOLDER_NAME"
    else
        export OD=$(readlink -f "$ORIGINAL_OD")
    fi
    # --- FIN DEL FIX ---

    echo "DEBUG: WD=$WD | ID=$ID | OD=$OD"
    
    # Crear la carpeta de salida (ej: docking_25) dentro de la carpeta del job
    mkdir -p "$OD" 
else
    echo "ERROR: El directorio de trabajo $WD no existe."
    exit 1
fi

#export ID=$(readlink -f "$ID")
#export WD=$(pwd)

#$SCRIPTDIR/sanitize

if [[ "$run_mode" != "dock_only" ]]; then
    if [[ -z "$PREPROC" ]]; then
        $SCRIPTDIR/receptor_pre.sh
    fi
    $SCRIPTDIR/ligand.sh
    $SCRIPTDIR/receptor_multi.sh

    # Gestión de pockets (Mantenemos tu lógica de P2Rank)
    if [[ -n "$MAX_POCKETS" && -n "$POCKETS" ]]; then
        export MAX_POCKETS=""
    fi
    # ... (Tu lógica de PRANK_ROWS se mantiene igual) ...
    
    if [[ -z "$MAX_POCKETS" && -z "$POCKETS" ]]; then
        export POCKETS=1
    fi
    echo $POCKETS > "$WD/pockets"
fi

if [[ "$run_mode" != "predock" ]]; then
    # Cargamos los pockets desde el archivo generado
    POCKETS_LIST=$(cat "$WD/pockets")
    
    # IMPORTANTE: Cambiamos el IFS localmente para el loop
    IFS=',' read -ra P_ARRAY <<< "$POCKETS_LIST"
    
    for rank in "${P_ARRAY[@]}"; do
        # Limpiamos espacios en blanco si los hubiera
        rank=$(echo $rank | tr -d '[:space:]')
        
        echo -e "\e[1m\e[36m>>\e[39m processing pocket $rank...\033[0m"
        export CURRENT_POCKET=$rank
        export CURRENT_POCKET_DIR="$OD/pocket_$rank"
        
        # Crear directorio de salida si no existe
        mkdir -p "$CURRENT_POCKET_DIR"
        
        # Ejecutar submódulos
        $SCRIPTDIR/box_multi.sh
        $SCRIPTDIR/dock_multi.sh
        
        echo -e "\e[1m\e[36m>>\e[39m splitting conformers...\033[0m"
        
        # AISLAMIENTO: Ejecutamos obabel sin que ADFR interfiera
        (
            unset LD_LIBRARY_PATH
            $OBABEL -ipdbqt "$CURRENT_POCKET_DIR/modes.pdbqt" -opdbqt -O "$CURRENT_POCKET_DIR/mode_.pdbqt" -m || echo "Aviso: No se pudo splitear (¿Vina falló?)"
        )
    done
fi