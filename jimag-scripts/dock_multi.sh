#!/bin/bash

# Evitar que el script continúe si algo falla
set -e

echo -e "\e[1m\e[36m>>\e[39m Iniciando docking en ${CURRENT_POCKET_DIR}...\033[0m"

# 1. Definir rutas de archivos necesarios
RECEPTOR_PDBQT="$WD/receptor.pdbqt"
LIGAND_PDBQT="$WD/ligand.pdbqt"
BOX_FILE="${CURRENT_POCKET_DIR}/box.txt"
OUTPUT_PDBQT="${CURRENT_POCKET_DIR}/modes.pdbqt"
LOG_FILE="${CURRENT_POCKET_DIR}/vina.log"

# 2. Verificar que los archivos existan
if [ ! -f "$RECEPTOR_PDBQT" ]; then echo "ERROR: No está el receptor.pdbqt"; exit 1; fi
if [ ! -f "$LIGAND_PDBQT" ]; then echo "ERROR: No está el ligand.pdbqt"; exit 1; fi
if [ ! -f "$BOX_FILE" ]; then echo "ERROR: No se encontró box.txt"; exit 1; fi

# 3. Leer los parámetros de la Grid Box desde box.txt
# Usamos un bucle para extraer cada valor ignorando el signo '='
while IFS=' = ' read -r key value; do
    case "$key" in
        center_x) CX="$value" ;;
        center_y) CY="$value" ;;
        center_z) CZ="$value" ;;
        size_x) SX="$value" ;;
        size_y) SY="$value" ;;
        size_z) SZ="$value" ;;
    esac
done < "$BOX_FILE"

# 4. Ejecutar AutoDock Vina
# Nota: Usamos --exhaustiveness $VINALVL y --num_modes $NUM_MODES que vienen de multi.sh
echo "DEBUG: Ejecutando Vina con Exhaustiveness: $VINALVL"

vina --receptor "$RECEPTOR_PDBQT" \
     --ligand "$LIGAND_PDBQT" \
     --center_x "$CX" \
     --center_y "$CY" \
     --center_z "$CZ" \
     --size_x "$SX" \
     --size_y "$SY" \
     --size_z "$SZ" \
     --exhaustiveness "${VINALVL:-8}" \
     --num_modes "${NUM_MODES:-9}" \
     --out "$OUTPUT_PDBQT" \
     --cpu 0 \
     > "$LOG_FILE" 2>&1

# 5. Verificar si se generó el resultado
if [ -f "$OUTPUT_PDBQT" ]; then
    echo -e "\e[1m\e[32mOK:\e[39m Docking completado. Resultados en $OUTPUT_PDBQT\033[0m"
else
    echo "ERROR: Vina terminó pero no generó modes.pdbqt. Revisa $LOG_FILE"
    exit 1
fi