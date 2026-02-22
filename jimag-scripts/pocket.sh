#!/bin/bash

PRANK=$HOMEDIR/.local/src/p2rank_2.4

echo -e "\e[1m\e[36m>>\e[39m looking for pockets...\033[0m"
$PRANK/prank predict -c configs/blind.groovy -f $WD/receptor.pdbqt -o $WD
