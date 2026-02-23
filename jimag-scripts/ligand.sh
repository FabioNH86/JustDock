#!/bin/bash

# 1. Intentamos usar el Link Simbólico que es la ruta "oficial" que el soft espera
ADFR_HOME="/home/fabio-noriega/ADFRsuite-1.0"

# 2. Si el link no existe, usamos la ruta larga (dinámica vía HOMEDIR)
if [ ! -d "$ADFR_HOME" ]; then
    [ -z "$HOMEDIR" ] && HOMEDIR="$HOME"
    ADFR_HOME="$HOMEDIR/.local/src/adfr/ADFRsuite-1.0"
fi

ADFRBIN="$ADFR_HOME/bin"

# 3. IMPORTANTE: Para que encuentre libpython2.7, debemos añadir el lib interno al LD_LIBRARY_PATH
export LD_LIBRARY_PATH="$ADFR_HOME/lib:$LD_LIBRARY_PATH"
export PATH="$ADFRBIN:$PATH"

echo -e ">> optimizing geometry for ligand..."
# Usamos el obabel del SISTEMA si el de ADFR falla, o el de ADFR si ya tiene el link
obabel "$ID"/ligand.* -O "$WD"/ligand.mol2 --gen3d

echo -e ">> preparing ligand..."
# Llamamos al script asegurando que use su entorno
if [ -f "$ADFRBIN/prepare_ligand" ]; then
    "$ADFRBIN/prepare_ligand" -l "$WD/ligand.mol2" -o "$WD/ligand.pdbqt"
else
    echo "ERROR: ADFRsuite no encontrado en $ADFRBIN"
    exit 1
fi