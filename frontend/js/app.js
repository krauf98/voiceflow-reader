const API_URL = "/api";

// Elements
const fileInput = document.getElementById('file-input');
const uploadView = document.getElementById('upload-view');
const readerView = document.getElementById('reader-view');
const playerBar = document.getElementById('player-bar');
const playBtn = document.querySelector('.play-btn');
const speedSelect = document.querySelector('.speed-select');
const langSelect = document.querySelector('.lang-select');
const engineSelect = document.querySelector('.engine-select');
const progressBar = document.querySelector('.progress-bar');
const progressFill = document.querySelector('.progress-fill');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const progressContainer = document.getElementById('progress-container');
const timeCurrent = document.getElementById('time-current');
const timeTotal = document.getElementById('time-total');

// State
let currentText = "";
let currentAudio = null;
let isPlaying = false;

const settingsBtn = document.querySelector('.settings-btn');
if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
        if (confirm("Reload app to upload a new file?")) {
            window.location.reload();
        }
    });
}

// Handle File Upload
fileInput.addEventListener('change', async function (e) {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('file', file);

        // UI Loading State
        const btn = document.querySelector('.btn-primary');
        const originalText = btn.innerText;
        btn.innerText = "Extracting Text...";
        btn.disabled = true;
        btn.style.opacity = 0.7;

        try {
            const response = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                currentText = data.text;

                // Update UI
                uploadView.classList.add('hidden');
                readerView.style.display = 'block';
                playerBar.classList.remove('hidden');

                // Populate Reader
                renderText(currentText);

                // Auto-set language
                if (['en', 'es', 'fr', 'de', 'zh', 'ar'].includes(data.language)) {
                    langSelect.value = data.language;
                }
            } else {
                alert("Error: " + data.error);
                resetUploadUI(btn, originalText);
            }
        } catch (err) {
            console.error(err);
            alert("Failed to upload file: " + err.message);
            resetUploadUI(btn, originalText);
        }
    }
});

// Handle Text Input
const pasteTextBtn = document.getElementById('paste-text-btn');
const textInputContainer = document.getElementById('text-input-container');
const submitTextBtn = document.getElementById('submit-text-btn');
const cancelTextBtn = document.getElementById('cancel-text-btn');
const directTextInput = document.getElementById('direct-text-input');

pasteTextBtn.addEventListener('click', () => {
    textInputContainer.classList.remove('hidden');
    pasteTextBtn.classList.add('hidden');
    // Optionally hide browse button or other elements if needed
});

cancelTextBtn.addEventListener('click', () => {
    textInputContainer.classList.add('hidden');
    pasteTextBtn.classList.remove('hidden');
    directTextInput.value = '';
});

submitTextBtn.addEventListener('click', () => {
    const text = directTextInput.value;
    if (!text.trim()) {
        alert("Please enter some text.");
        return;
    }

    currentText = text;

    // Auto-detect Language (Basic)
    // Check if text contains Arabic characters
    const arabicPattern = /[\u0600-\u06FF]/;
    if (arabicPattern.test(text)) {
        langSelect.value = 'ar';
    } else {
        langSelect.value = 'en'; // Default
    }

    // Update UI
    uploadView.classList.add('hidden');
    readerView.style.display = 'block';
    playerBar.classList.remove('hidden');

    renderText(currentText);
});

function resetUploadUI(btn, originalText) {
    btn.innerText = originalText;
    btn.disabled = false;
    btn.style.opacity = 1;
}

function renderText(text) {
    const paragraphs = text.split(/\n\s*\n/);
    readerView.innerHTML = paramsToHTML(paragraphs);
}

function paramsToHTML(paragraphs) {
    return paragraphs.map(p => `<p dir="auto">${p}</p>`).join('');
}

// Play/Pause
playBtn.addEventListener('click', async () => {
    if (isPlaying) {
        pauseAudio();
    } else {
        if (!currentAudio) {
            await fetchAndPlayAudio();
        } else {
            resumeAudio();
        }
    }
});

// Skip -10s
if (prevBtn) {
    prevBtn.addEventListener('click', () => {
        if (currentAudio) {
            currentAudio.currentTime = Math.max(0, currentAudio.currentTime - 10);
        }
    });
}

// Skip +10s
if (nextBtn) {
    nextBtn.addEventListener('click', () => {
        if (currentAudio) {
            currentAudio.currentTime = Math.min(currentAudio.duration, currentAudio.currentTime + 10);
        }
    });
}

// Seek Bar Click
if (progressContainer) {
    progressContainer.addEventListener('click', (e) => {
        if (currentAudio && currentAudio.duration) {
            const width = progressContainer.clientWidth;
            const clickX = e.offsetX;
            const duration = currentAudio.duration;
            currentAudio.currentTime = (clickX / width) * duration;
        }
    });
}

async function fetchAndPlayAudio() {
    const icon = playBtn.querySelector('i');
    icon.className = "fa-solid fa-spinner fa-spin";

    try {
        const speed = parseFloat(speedSelect.value);
        const lang = langSelect.value;
        const engine = engineSelect ? engineSelect.value : 'edge';

        const textToRead = currentText.length > 5000 ? currentText.substring(0, 5000) : currentText;

        const response = await fetch(`${API_URL}/synthesize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: textToRead,
                language: lang,
                speed: speed,
                engine: engine
            })
        });

        const data = await response.json();

        if (data.success) {
            playAudioFromUrl(data.audio_url);
        } else {
            alert("TTS Error: " + data.error);
            resetPlayIcon();
        }

    } catch (err) {
        console.error(err);
        resetPlayIcon();
    }
}

function playAudioFromUrl(url) {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }

    currentAudio = new Audio(url);

    currentAudio.addEventListener('loadedmetadata', () => {
        resumeAudio();
        if (timeTotal) timeTotal.innerText = formatTime(currentAudio.duration);
    });

    currentAudio.addEventListener('timeupdate', () => {
        if (currentAudio.duration) {
            const percent = (currentAudio.currentTime / currentAudio.duration) * 100;
            if (progressFill) progressFill.style.width = `${percent}%`;
            if (timeCurrent) timeCurrent.innerText = formatTime(currentAudio.currentTime);
        }
    });

    currentAudio.addEventListener('ended', () => {
        isPlaying = false;
        resetPlayIcon();
        if (progressFill) progressFill.style.width = '0%';
        if (timeCurrent) timeCurrent.innerText = "00:00";
    });
}

function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return "00:00";
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min < 10 ? '0' + min : min}:${sec < 10 ? '0' + sec : sec}`;
}

function resumeAudio() {
    if (currentAudio) {
        currentAudio.play();
        isPlaying = true;
        const icon = playBtn.querySelector('i');
        icon.className = "fa-solid fa-pause";
    }
}

function pauseAudio() {
    if (currentAudio) {
        currentAudio.pause();
        isPlaying = false;
        const icon = playBtn.querySelector('i');
        icon.className = "fa-solid fa-play";
    }
}

function resetPlayIcon() {
    const icon = playBtn.querySelector('i');
    icon.className = "fa-solid fa-play";
}

// Settings Change Listeners (Reset Audio to Model New Request)
function resetAudioState() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    isPlaying = false;
    resetPlayIcon();
    if (progressFill) progressFill.style.width = '0%';
    if (timeCurrent) timeCurrent.innerText = "00:00";
}

speedSelect.addEventListener('change', resetAudioState);
langSelect.addEventListener('change', resetAudioState);
if (engineSelect) engineSelect.addEventListener('change', resetAudioState);
