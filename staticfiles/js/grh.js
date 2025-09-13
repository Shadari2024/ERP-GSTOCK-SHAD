// Fonctions JavaScript pour le module GRH

document.addEventListener('DOMContentLoaded', function() {
    // Gestion des messages flash
    setTimeout(function() {
        let alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirmation des suppressions
    let deleteButtons = document.querySelectorAll('.btn-delete-confirm');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Êtes-vous sûr de vouloir supprimer cet élément ? Cette action est irréversible.')) {
                e.preventDefault();
            }
        });
    });

    // Calcul automatique du nombre de jours de congé
    let dateDebutInput = document.getElementById('id_date_debut');
    let dateFinInput = document.getElementById('id_date_fin');
    let nombreJoursInput = document.getElementById('id_nombre_jours');

    if (dateDebutInput && dateFinInput && nombreJoursInput) {
        function calculerJoursConges() {
            if (dateDebutInput.value && dateFinInput.value) {
                let dateDebut = new Date(dateDebutInput.value);
                let dateFin = new Date(dateFinInput.value);
                
                // Calcul de la différence en jours
                let differenceTemps = dateFin.getTime() - dateDebut.getTime();
                let differenceJours = Math.ceil(differenceTemps / (1000 * 3600 * 24)) + 1; // +1 pour inclure le jour de début
                
                nombreJoursInput.value = differenceJours;
            }
        }

        dateDebutInput.addEventListener('change', calculerJoursConges);
        dateFinInput.addEventListener('change', calculerJoursConges);
    }

    // Gestion des formulaires dynamiques
    let formsets = document.querySelectorAll('.formset-row');
    formsets.forEach(function(formset) {
        formset.addEventListener('click', function(e) {
            if (e.target.classList.contains('add-formset-row')) {
                e.preventDefault();
                let totalForms = document.getElementById('id_form-TOTAL_FORMS');
                let formNum = parseInt(totalForms.value);
                let newRow = document.querySelector('.empty-form').cloneNode(true);
                
                newRow.innerHTML = newRow.innerHTML.replace(/__prefix__/g, formNum);
                newRow.classList.remove('empty-form', 'd-none');
                
                document.querySelector('#formset tbody').appendChild(newRow);
                totalForms.value = formNum + 1;
            }
            
            if (e.target.classList.contains('delete-formset-row')) {
                e.preventDefault();
                let row = e.target.closest('.formset-row');
                let deleteInput = row.querySelector('input[id$="-DELETE"]');
                
                if (deleteInput) {
                    deleteInput.checked = true;
                    row.style.display = 'none';
                } else {
                    row.remove();
                }
            }
        });
    });

    // Filtrage des tableaux
    let filterInputs = document.querySelectorAll('.table-filter');
    filterInputs.forEach(function(input) {
        input.addEventListener('keyup', function() {
            let filter = input.value.toLowerCase();
            let table = input.closest('.card').querySelector('table');
            let rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(function(row) {
                let text = row.textContent.toLowerCase();
                row.style.display = text.indexOf(filter) > -1 ? '' : 'none';
            });
        });
    });
});

// Fonction pour formater les montants avec la devise
function formatMontant(montant) {
    let deviseSymbole = document.querySelector('.footer').textContent.match(/Devise: (.*)/)[1];
    return new Intl.NumberFormat('fr-FR', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
    }).format(montant) + ' ' + deviseSymbole;
}