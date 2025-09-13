document.addEventListener('DOMContentLoaded', function() {
    // Conversion automatique du code devise en majuscules
    const codeDeviseInputs = document.querySelectorAll('input[name="code"]');
    codeDeviseInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    });

    // Validation des taux de change
    const tauxForms = document.querySelectorAll('form[data-taux-change]');
    tauxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const source = this.querySelector('[name="devise_source"]').value;
            const cible = this.querySelector('[name="devise_cible"]').value;
            
            if (source === cible) {
                e.preventDefault();
                alert("La devise source et cible doivent être différentes");
            }
        });
    });
});