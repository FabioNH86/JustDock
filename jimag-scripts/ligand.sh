#!/bin/bash

# 1. Rutas de herramientas
ADFR_BIN="/opt/ADFRsuite/bin"
ADFR_LIB="/opt/ADFRsuite/lib"
SYSTEM_OBABEL="/usr/bin/obabel"

# 2. CONVERTIR RUTAS A ABSOLUTAS (Usando rutas completas para evitar el error de ZLIB)
ABS_WD=$(/usr/bin/readlink -f "$WD")
ABS_ID=$(/usr/bin/readlink -f "$ID")

echo -e ">> optimizing geometry for ligand..."
$SYSTEM_OBABEL "$ABS_ID"/ligand.* -O "$ABS_WD"/ligand.mol2 --gen3d

echo -e ">> preparing ligand..."

if [ ! -f "$ABS_WD/ligand.mol2" ]; then
    echo "ERROR: obabel no generó $ABS_WD/ligand.mol2"
    /bin/ls -l "$ABS_WD" 
    exit 1
fi

echo "DEBUG: Ejecutando prepare_ligand en $ABS_WD"

# --- EL CAMBIO CRÍTICO AQUÍ ---
# 1. Aseguramos que el PATH de ADFR esté disponible pero NO el LD_LIBRARY_PATH global
# 2. Ejecutamos el comando de forma aislada
(
  # Limpiamos cualquier rastro de librerías que rompan el shell (sh)
  unset LD_LIBRARY_PATH
  
  # Ejecutamos el comando inyectando la librería SOLO para ese proceso
  # Esto evita que el comando 'sh' interno de prepare_ligand falle
  LD_LIBRARY_PATH="$ADFR_LIB" "$ADFR_BIN/prepare_ligand" \
    -l "$ABS_WD/ligand.mol2" \
    -o "$ABS_WD/ligand.pdbqt" \
    -A hydrogens \
    -U nps_lps
)