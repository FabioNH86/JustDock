BEGIN { 
	FS = ", "
}

NR == 2 {
	res_string = $10
	gsub(/[[:alpha:]]_/, "", res_string)
	gsub(/ /, "\n", res_string)
	print res_string 
}
