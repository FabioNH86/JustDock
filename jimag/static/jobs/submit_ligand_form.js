function submitLigandForm() {
    var processing = document.getElementById('processingLigand');
    var message = document.getElementById('ligandProcessedMessage');
    message.innerHTML = '';
    message.classList.remove('is-error');
    processing.style.display = 'flex';

    var lForm = document.getElementById('uploadLigandForm');
    var lFormData = new FormData(lForm);
    lFormData.append('type', 'process_ligand');

    fetch(lForm.action, {
        method: 'POST',
        body: lFormData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.text())
    .then(data => {
        processing.style.display = 'none';
        var parsedData = JSON.parse(data);
        message.innerHTML = parsedData.status;
        var ligand = parsedData.ligand_file;
    })
    .catch(error => {
        processing.style.display = 'none';
        message.classList.add('is-error');
        message.innerHTML = 'Something went wrong while preparing the ligand. Please check the file and try again.';
        console.error('Error:', error)
    });
}
