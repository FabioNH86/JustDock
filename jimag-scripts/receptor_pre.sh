#!/bin/bash
set -e

# 1. Definir rutas internas de Docker (donde instalamos todo)
CHIMERACMD="/app/chimera/bin/chimera"
PRANKCMD="/app/p2rank_2.4/prank"
# Usamos SCRIPTDIR que viene exportado desde multi.sh
SCRIPTPATH="$SCRIPTDIR/receptor.py"
PRANKCONF="$SCRIPTDIR/configs/blind.groovy"

echo ">> sanitizing receptor with obabel..."
# El receptor.pdb ya debería estar en el WD (donde multi.sh hizo 'cd')
#obabel receptor.pdb -O receptor.pdb
/usr/bin/obabel receptor.pdb -O receptor_clean.pdb

# EXPORTAR para que el script de Python las vea
export IF="receptor.pdb"
export OF="receptor.pdb"

# 2. Ejecutar Chimera para limpiar la proteína
echo ">> running chimera script..."
$CHIMERACMD --nogui --script "$SCRIPTPATH"

# 3. Ejecutar P2Rank
# IMPORTANTE: Eliminamos el flag -c si no es estrictamente necesario, 
# o aseguramos que la ruta al .groovy sea absoluta.
echo ">> predicting pockets with P2Rank..."
$PRANKCMD predict -f receptor.pdb -o .