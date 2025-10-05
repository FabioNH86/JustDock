BEGIN { 
	scaling = 1.1 #TODO: make this a config param
	letrs[1] = "x"; letrs[2] = "y"; letrs[3] = "z"
	min[1] = 9000; min[2] = 9000; min[3] = 9000 
	max[1] = -9000; max[2] = -9000; max[3] = -9000 
	#print the 11nth entry of the 2nd record
	#(surf_atom_ids), then write to atom_string
	"awk -v WD="$WD" 'BEGIN { FS = \", \" } NR == ('$CURRENT_POCKET'+1) { print $11 }'\
	< $WD/receptor.pdb_predictions.csv" | getline atom_string
	n = split(atom_string, atoms, " "); j = 1 #loop vars
}

/^ATOM/ && $2 == atoms[j] { #compare pdbqt and surf_atom_ids
	for (i in letrs) {
		coords[i] = $(6+i) #x = coords[1] = $7 in pdbqt
		max[i] = (coords[i] > max[i]) ? coords[i] : max[i]
		min[i] = (coords[i] < min[i]) ? coords[i] : min[i]
	} 
	j++
}

END { #write the box parameters
	for (i in letrs) {
		center[i] = (max[i] + min[i]) / 2
		size[i] = (max[i] - min[i]) * scaling
		printf("center_%s = %.3f\n", letrs[i], center[i])
		printf("size_%s = %.1f\n", letrs[i], size[i])
	}
}
