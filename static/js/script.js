document.addEventListener('DOMContentLoaded', function () {
    var flashAlerts = document.querySelectorAll('.alert.alert-dismissible');

    flashAlerts.forEach(function (alert) {
        window.setTimeout(function () {
            if (window.bootstrap && window.bootstrap.Alert) {
                window.bootstrap.Alert.getOrCreateInstance(alert).close();
                return;
            }

            alert.remove();
        }, 5000);
    });


    var copyButton = document.querySelector('[data-copy-target]');
    if (copyButton) {
        copyButton.addEventListener('click', function () {
            var target = document.getElementById(copyButton.dataset.copyTarget);
            var outputText = target ? target.innerText.trim() : '';

            if (!outputText || !navigator.clipboard) {
                return;
            }

            navigator.clipboard.writeText(outputText).then(function () {
                var originalText = copyButton.textContent;
                copyButton.textContent = 'Copied!';

                window.setTimeout(function () {
                    copyButton.textContent = originalText;
                }, 1800);
            });
        });
    }

    var downloadButton = document.querySelector('[data-download-target]');
    if (downloadButton) {
        downloadButton.addEventListener('click', function () {
            var target = document.getElementById(downloadButton.dataset.downloadTarget);
            var outputText = target ? target.innerText.trim() : '';

            if (!outputText) {
                return;
            }

            var blob = new Blob([outputText + '\n'], { type: 'text/plain;charset=utf-8' });
            var downloadLink = document.createElement('a');
            downloadLink.href = URL.createObjectURL(blob);
            downloadLink.download = downloadButton.dataset.downloadFilename || 'marketmind-content.txt';
            document.body.appendChild(downloadLink);
            downloadLink.click();
            downloadLink.remove();
            URL.revokeObjectURL(downloadLink.href);
        });
    }

    var analyzeForm = document.querySelector('form[action*="analyze"]');

    if (!analyzeForm) {
        return;
    }

    var submitButton = analyzeForm.querySelector('button[type="submit"]');
    var isSubmitting = false;

    analyzeForm.addEventListener('submit', function (event) {
        if (isSubmitting) {
            event.preventDefault();
            return;
        }

        isSubmitting = true;

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.dataset.originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Generating...';
        }
    });
});
