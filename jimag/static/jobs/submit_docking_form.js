function submitDockingForm() {
    //initialize FormData
    var pForm = document.getElementById('uploadProteinForm');
    var pFormData = new FormData(pForm);

    var lForm = document.getElementById('uploadLigandForm');
    var lFormData = new FormData(lForm);

    var settingsForm = document.getElementById('settingsForm');
    var settingsFormData = new FormData(settingsForm);

    var dockingForm = document.getElementById('runJob');
    var dockingFormData = new FormData(dockingForm);
    dockingFormData.append('type', 'run_job');

    //fill formData with form information
    for (const [key, value] of pFormData.entries()) {
        dockingFormData.append(key, value);
    }

    for (const [key, value] of lFormData.entries()) {
        dockingFormData.append(key, value);
    }

    for (const [key, value] of settingsFormData.entries()) {
        dockingFormData.append(key, value);
    }

    //add selected chains (if any)
    var chainSpan = document.getElementById('chainstring');
    var chainString = chainSpan.textContent;
    dockingFormData.append('chainString', chainString);

    //add pockets
    //in the following, option refers to the option that will be passed to the script (maxpockets or pocketstring)
    var pocketSelect = document.getElementById('contentSelector4');
    if (pocketSelect.value === "toppockets") {
        var maxpockets = document.getElementById('maxpockets').value; 
        
        const maxPocketObject = {
            option: '--max_pockets',
            value: maxpockets
        };

        const maxPocketJSON = JSON.stringify(maxPocketObject);
        dockingFormData.append('pockets', maxPocketJSON);
    } else {
    //case: select pockets
        const selectedRanks = []; //array of pocket ranks, used as key for the predictions csv
        const selected = document.querySelectorAll('.pocketcheckbox:checked');

        selected.forEach(checkbox => {
            const rank = checkbox.value; 
            selectedRanks.push(rank);
        });

        const pocketString = selectedRanks.join(',');
        const pocketObject = {
            option: '--pockets',
            value:  pocketString 
        };

        const pocketJSON = JSON.stringify(pocketObject);
        dockingFormData.append('pockets', pocketJSON);
    }

    //add cleanProteinFilename and pocketsFilename if pocket preprocessing was made --from pockets_funcs.js 
    if (preprocDone == true) {
        dockingFormData.append('pocketsFilename', pocketsFilename);
        dockingFormData.append('cleanProteinFilename', cleanProteinFilename);
        dockingFormData.append('preprocDone', 1);
    }

    //send request with filled form
    fetch(dockingForm.action, {
        method: 'POST',
        body: dockingFormData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            }
            else {
                window.location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error)
        });
}
