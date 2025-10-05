function submitLigandForm() {
    document.getElementById('ligandProcessedMessage').style.display = 'block';

    var lForm = document.getElementById('uploadLigandForm');
    var lFormData = new FormData(lForm);
    lFormData.append('type', 'process_ligand');

    //console.log(lFormData);
    //getval = lFormData.get('ligand_file');
    //console.log(getval);

    fetch(lForm.action, {
        method: 'POST',
        body: lFormData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.text())
    .then(data => {
        document.getElementById('processingLigand').style.display = 'none';
        var parsedData = JSON.parse(data);
        document.getElementById('ligandProcessedMessage').innerHTML = parsedData.status;
        var ligand = parsedData.ligand_file;
    })
    .catch(error => {
        console.error('Error:', error)
    });
}
