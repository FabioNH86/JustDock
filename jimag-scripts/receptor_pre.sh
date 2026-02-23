#!/bin/bash
#Simula las funciones realizadas por process_pockets en jobs/tasks.py
SCRIPTPATH=$SCRIPTDIR/receptor.py
CHIMERACMD=$HOMEDIR/.local/src/chimera/bin/chimera
#CHIMERADIR=$HOMEDIR/.local/src/chimera/bin
PRANKCMD=$HOMEDIR/.local/src/p2rank_2.4/prank
PRANKCONF=$SCRIPTDIR/configs/blind.groovy

export IF=$ID/receptor.pdb
obabel $ID/receptor.* -O $WD/receptor.pdb
export OF=$WD/receptor.pdb

$CHIMERACMD --nogui $SCRIPTPATH
$PRANKCMD predict -c $PRANKCONF -f $OF -o $WD
