#!/bin/bash

ADFRDIR=$HOMEDIR/.local/src/adfr/ADFRsuite-1.0/bin
#ADFRDIR=$HOMEDIR/ADFRsuite-1.0/bin

echo -e "\e[1m\e[36m>>\e[39m optimizing geometry for ligand...\033[0m"
obabel $ID/ligand.* -O $WD/ligand.mol2 --gen3d
#obabel $OD/ligand_aux.mol2 -O $OD/ligand.mol2 --conformer --nconf 30
#rm -f $OD/ligand_aux.mol2
echo $WD
echo -e "\e[1m\e[36m>>\e[39m preparing ligand...\033[0m"
cd $ADFRDIR
./prepare_ligand -l $WD/ligand.mol2 -o $WD/ligand.pdbqt 
