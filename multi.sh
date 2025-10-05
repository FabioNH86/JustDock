#!/bin/bash
#Para simular el comportamiento de este script, correr primero blind.sh y luego dejar predictions solo en output
#example: ./multi.sh --vinalvl 2 --num_modes 5 --pockets 1,3
#NOTE: max_pockets = 1 and pockets = 1 should yield the same result

#Defaults
export WD=./output
export ID=./input
export OD=./output

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

#$SCRIPTDIR/sanitize

if [[ "$run_mode" != "dock_only" ]]; then #we surely can do better than this?
	#if no preprocessing has been made, do the following as a part of full auto
	if [[ -z "$PREPROC" ]]; then
		$SCRIPTDIR/receptor_pre.sh
	fi
	$SCRIPTDIR/ligand.sh
	$SCRIPTDIR/receptor_multi.sh

	#manage pockets
	if [[ -n "$MAX_POCKETS" && -n "$POCKETS" ]]; then
		echo "WARNING: SET POCKETS AND MAX_POCKETS. IGNORING MAX_POCKETS"	
		export MAX_POCKETS=""
	fi
	if [[ -n "$MAX_POCKETS" && -z "$POCKETS" ]]; then
		# if max_pockets is greater than the pockets given by p2rank, fall back to the later
		PRANK_ROWS="$(wc -l < $WD/receptor.pdb_predictions.csv)"
		# subtract the headers row
		PREDICTED_POCKETS=$((PRANK_ROWS - 1))
		if [[ "$MAX_POCKETS" -gt "$PREDICTED_POCKETS" ]]; then
			echo "WARNING: MAX_POCKETS GREATER THAN NUMBER OF PREDICTED POCKETS ($PREDICTED_POCKETS)"
			echo "WARNING: FALLING BACK TO PREDICTED_POCKETS"
			MAX_POCKETS="$PREDICTED_POCKETS"
		fi
		#translate max_pockets to a pockets use case
		export POCKETS="$($SCRIPTDIR/max2pockets $MAX_POCKETS)"
	fi
	if [[ -z "$MAX_POCKETS" && -z "$POCKETS" ]]; then
		#take only the first pocket (full auto)
		export POCKETS=1
	fi
	echo $POCKETS > "$WD/pockets" #this file will be used to update the docking instance
fi

if [[ "$run_mode" != "predock" ]]; then
	#perform docking on each pocket
	OLD_IFS=$IFS
	IFS=','

	POCKETS="$(cat $WD/pockets)"
	for rank in $POCKETS; do
		echo -e "\e[1m\e[36m>>\e[39m processing pocket $rank...\033[0m"
		export CURRENT_POCKET=$rank
		export CURRENT_POCKET_DIR="$OD/pocket_$CURRENT_POCKET"
		IFS=$OLD_IFS
		mkdir $CURRENT_POCKET_DIR
		$SCRIPTDIR/box_multi.sh
		$SCRIPTDIR/dock_multi.sh
		echo -e "\e[1m\e[36m>>\e[39m splitting conformers...\033[0m"
		obabel -ipdbqt "$CURRENT_POCKET_DIR/modes.pdbqt" -opdbqt -O "$CURRENT_POCKET_DIR/mode_.pdbqt" -m
	done

	#awk -f $WD/pocketindices.awk $OD/receptor.pdbqt_predictions.csv > $OD/resfile
fi
