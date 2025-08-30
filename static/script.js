document.addEventListener('DOMContentLoaded', function () {
    const separatorForm = document.getElementById('separator-form');
    const enhancerForm = document.getElementById('enhancer-form');
    const loader = document.getElementById('loader');

    // Function to update file name display
    function updateFileName(fileInputId, fileNameId) {
        const fileInput = document.getElementById(fileInputId);
        const fileNameDisplay = document.getElementById(fileNameId);
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                fileNameDisplay.textContent = fileInput.files[0].name;
            } else {
                fileNameDisplay.textContent = '';
            }
        });
    }

    updateFileName('separator-file', 'separator-file-name');
    updateFileName('enhancer-file', 'enhancer-file-name');

    // Handle Separator Form Submission
    separatorForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('separator-file');
        if (fileInput.files.length === 0) {
            alert('الرجاء اختيار ملف أولاً.');
            return;
        }

        const formData = new FormData();
        formData.append('audio_file', fileInput.files[0]);

        showLoader(true);
        try {
            const response = await fetch('/separate', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('حدث خطأ أثناء المعالجة.');
            }

            const result = await response.json();
            displayResults('separator-results', result);
        } catch (error) {
            alert(error.message);
        } finally {
            showLoader(false);
        }
    });

    // Handle Enhancer Form Submission
    enhancerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('enhancer-file');
        if (fileInput.files.length === 0) {
            alert('الرجاء اختيار ملف أولاً.');
            return;
        }

        const formData = new FormData();
        formData.append('audio_file', fileInput.files[0]);

        showLoader(true);
        try {
            const response = await fetch('/enhance', {
                method: 'POST',
                body: formData,
            });
            
            if (!response.ok) {
                throw new Error('حدث خطأ أثناء المعالجة.');
            }

            const result = await response.json();
            displayResults('enhancer-results', result);
        } catch (error) {
            alert(error.message);
        } finally {
            showLoader(false);
        }
    });

    function showLoader(show) {
        loader.classList.toggle('hidden', !show);
    }

    function displayResults(resultsId, data) {
        const resultsArea = document.getElementById(resultsId);
        resultsArea.innerHTML = '<h3>النتائج جاهزة!</h3>'; // Clear previous results

        if (data.error) {
            resultsArea.innerHTML += `<p style="color: red;">${data.error}</p>`;
        } else {
            for (const key in data.files) {
                const trackName = key === 'vocals' ? 'صوت المغني' : key === 'accompaniment' ? 'الموسيقى' : 'الصوت المحسّن';
                const filePath = data.files[key];
                
                const trackElement = document.createElement('div');
                trackElement.className = 'result-track';
                trackElement.innerHTML = `
                    <span>${trackName}</span>
                    <a href="${filePath}" class="download-btn" download><i class="fas fa-download"></i> تحميل</a>
                `;
                resultsArea.appendChild(trackElement);
            }
        }
        resultsArea.classList.remove('hidden');
    }
});
