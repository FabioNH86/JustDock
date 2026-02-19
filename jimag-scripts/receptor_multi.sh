#!/bin/bash

ADFRDIR=$HOMEDIR/.local/src/adfr/ADFRsuite-1.0/bin
#ADFRDIR=$HOMEDIR/ADFRsuite-1.0/bin

cd $ADFRDIR
echo -e "\e[1m\e[36m>>\e[39m preparing receptor...\033[0m"
./reduce $WD/receptor.pdb >> $WD/receptorH.pdb
./prepare_receptor -r $WD/receptorH.pdb -o $WD/receptor.pdbqt

rm -f $SCRIPTDIR/receptor.pyc #TODO: es necesario borrar receptor.pyc?
