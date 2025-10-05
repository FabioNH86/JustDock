#!/bin/bash

#WD=$SCRIPTDIR
#VINADIR=$HOMEDIR/.local/src/autodock_vina_1_1_2_linux_x86/bin
VINADIR=$HOMEDIR/.local/src/vina_1.2.5

echo -e "\e[1m\e[36m>>\e[39m docking...\033[0m"
cd $VINADIR
./vina_1.2.5_linux_x86_64 --receptor $WD/receptor.pdbqt --ligand $WD/ligand.pdbqt\
	   --config $CURRENT_POCKET_DIR/box.txt --exhaustiveness=$VINALVL\
	   --out $CURRENT_POCKET_DIR/modes.pdbqt --num_modes $NUM_MODES \
	   | tee $CURRENT_POCKET_DIR/scores.txt && sed -i -n '/^mode/,$p' $CURRENT_POCKET_DIR/scores.txt
	   #| awk '/Refining/,/Writing/' | sed '1,2d;$d' > $CURRENT_POCKET_DIR/scores.txt
cd $WD
