document.addEventListener('DOMContentLoaded', function() {
    const deviseSource = document.getElementById('id_devise_source');
    const deviseCible = document.getElementById('id_devise_cible');
    const tauxField = document.getElementById('id_taux');
    const tauxInfo = document.getElementById('taux-info');
    const tauxMessage = document.getElementById('taux-message');

    function checkDevises() {
        if (deviseSource.value && deviseCible.value && deviseSource.value === deviseCible.value) {
            tauxMessage.textContent = "Attention : La devise source et cible sont identiques. Le taux devrait être 1.";
            tauxInfo.style.display = 'block';
            tauxField.value = '1.0';
        } else {
            tauxInfo.style.display = 'none';
        }
    }

    async function checkExistingRate() {
        if (!deviseSource.value || !deviseCible.value || deviseSource.value === deviseCible.value) {
            return;
        }

        try {
            const response = await fetch(`/parametres/tauxdechange/?check_rate=1&source=${deviseSource.value}&cible=${deviseCible.value}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Erreur ${response.status}: ${await response.text()}`);
            }

            const data = await response.json();
            
            if (data.exists) {
                tauxMessage.textContent = "Un taux existe déjà pour cette paire de devises. Vérifiez les taux existants avant de créer un nouveau.";
                tauxInfo.style.display = 'block';
            } else {
                tauxInfo.style.display = 'none';
            }
        } catch (error) {
            console.error('Erreur lors de la vérification du taux:', error);
            tauxMessage.textContent = "Erreur lors de la vérification du taux existant. Veuillez réessayer.";
            tauxInfo.style.display = 'block';
            tauxInfo.classList.add('alert-danger');
        }
    }

    deviseSource.addEventListener('change', function() {
        checkDevises();
        checkExistingRate();
    });

    deviseCible.addEventListener('change', function() {
        checkDevises();
        checkExistingRate();
    });

    checkDevises();
});