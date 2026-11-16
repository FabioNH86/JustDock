function submitProteinForm() {
    var processing = document.getElementById('processingProtein');
    var message = document.getElementById('proteinProcessedMessage');
    message.innerHTML = '';
    message.classList.remove('is-error');
    processing.style.display = 'flex';

    var pForm = document.getElementById('uploadProteinForm');
    var pFormData = new FormData(pForm);
    pFormData.append('type', 'process_protein');

    fetch(pForm.action, {
        method: 'POST',
        body: pFormData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.text())
    .then(data => {
        processing.style.display = 'none';
        var parsedData = JSON.parse(data);
        message.innerHTML = parsedData.status;
        var receptor = parsedData.protein_file;
        //if the parsed data says success, do the following
        window.loadReceptor(receptor);
    })
    .catch(error => {
        processing.style.display = 'none';
        message.classList.add('is-error');
        message.innerHTML = 'Something went wrong while preparing the protein. Please check the file and try again.';
        console.error('Error:', error)
    });
}
