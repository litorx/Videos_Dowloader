document.getElementById('video-form').addEventListener('submit', handleFormSubmit);

function handleFormSubmit(event) {
    event.preventDefault();
    const url = document.getElementById('video-url').value;

    showSearchingIndicator();
    
    fetchVideoInfo(url)
        .then(data => processVideoInfo(data, url))
        .catch(error => alert('Erro: ' + error.message))
        .finally(() => hideSearchingIndicator());
}

function fetchVideoInfo(url) {
    return fetch('/get_info', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: new URLSearchParams({'url': url})
    }).then(response => response.json());
}

function processVideoInfo(data, url) {
    if (data.error) {
        alert('Erro: ' + data.error);
        return;
    }

    const qualityOptions = document.getElementById('quality-options');
    qualityOptions.innerHTML = '';

    data.formats.forEach(format => {
        if (format.resolution !== 'Áudio') {
            createQualityButton(format, url, qualityOptions);
        }
    });

    document.getElementById('quality-selection').classList.remove('hidden');
}

function createQualityButton(format, url, container) {
    const button = document.createElement('button');
    button.innerText = format.resolution;
    button.onclick = () => downloadVideo(url, format.format_id);
    container.appendChild(button);
}

function downloadVideo(url, quality) {
    const progressSpan = document.getElementById('progress');
    const loadingIndicator = document.getElementById('loading-indicator');
    const completionMessage = document.getElementById('completion-message');

    loadingIndicator.classList.remove('hidden');
    progressSpan.textContent = 'Baixando...';

    fetch('/download', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: new URLSearchParams({'url': url, 'quality': quality})
    }).then(response => {
        if (response.ok) {
            return response.blob().then(blob => {
                const downloadLink = document.createElement('a');
                downloadLink.href = URL.createObjectURL(blob);
                downloadLink.download = `${quality}.mp4`;
                downloadLink.click();
                
                // Update the message after download
                progressSpan.textContent = '';
                completionMessage.classList.remove('hidden');
                setTimeout(() => {
                    loadingIndicator.classList.add('hidden');
                    completionMessage.classList.add('hidden');
                }, 3000); // Hide message after 3 seconds
            });
        } else {
            return response.json().then(data => { throw new Error(data.error); });
        }
    }).catch(error => {
        alert('Erro: ' + error.message);
        progressSpan.textContent = 'Erro ao baixar o vídeo';
        loadingIndicator.classList.add('hidden');
    });
}

function showSearchingIndicator() {
    document.getElementById('searching-indicator').classList.remove('hidden');
}

function hideSearchingIndicator() {
    document.getElementById('searching-indicator').classList.add('hidden');
}
