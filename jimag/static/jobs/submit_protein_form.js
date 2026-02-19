function submitProteinForm() {
    document.getElementById('proteinProcessedMessage').style.display = 'block';

    var pForm = document.getElementById('uploadProteinForm');
    var pFormData = new FormData(pForm);
    pFormData.append('type', 'process_protein');

    //console.log(pFormData);

    fetch(pForm.action, {
        method: 'POST',
        body: pFormData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.text())
    .then(data => {
        document.getElementById('processingProtein').style.display = 'none';
        var parsedData = JSON.parse(data);
        document.getElementById('proteinProcessedMessage').innerHTML = parsedData.status;
        var receptor = parsedData.protein_file;
        //if the parsed data says success, do the following
        window.loadReceptor(receptor);
    })
    .catch(error => {
        console.error('Error:', error)
    });
}
