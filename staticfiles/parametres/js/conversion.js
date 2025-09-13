document.addEventListener('DOMContentLoaded', function() {
    const convertForm = document.getElementById('convert-form');
    
    if (convertForm) {
        convertForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(convertForm);
            const resultElement = document.getElementById('conversion-result');
            resultElement.textContent = "{% trans 'Calcul en cours...' %}";
            
            try {
                const response = await fetch("{% url 'parametres:convertir_devise' %}", {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.error) {
                    resultElement.textContent = data.error;
                    showAlert('danger', data.error);
                } else {
                    resultElement.textContent = data.montant.toFixed(6);
                }
            } catch (error) {
                console.error('Error:', error);
                resultElement.textContent = "{% trans 'Erreur de conversion' %}";
                showAlert('danger', "{% trans 'Erreur lors de la conversion' %}");
            }
        });
    }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.prepend(alertDiv);
        
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }, 5000);
    }
}