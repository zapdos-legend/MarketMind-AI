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
