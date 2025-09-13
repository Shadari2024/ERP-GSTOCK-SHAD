document.addEventListener('DOMContentLoaded', function() {
    // Gestion des modules
    document.querySelectorAll('.module-toggle').forEach(toggle => {
        toggle.addEventListener('change', function() {
            const moduleId = this.dataset.moduleId;
            const isActive = this.checked;
            
            fetch(`/api/modules/${moduleId}/toggle/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({active: isActive})
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    this.checked = !isActive;
                    alert('Erreur lors de la mise à jour');
                }
            });
        });
    });

    // Conversion de devise
    const convertForm = document.getElementById('convert-form');
    if (convertForm) {
        convertForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch('{% url "parametres:convertir_devise" %}', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('result').innerText = data.montant;
            });
        });
    }
});

function getCookie(name) {
    // Fonction utilitaire pour récupérer les cookies
}