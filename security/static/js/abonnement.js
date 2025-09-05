document.addEventListener('DOMContentLoaded', function() {
    // Validation des dates
    const dateFin = document.getElementById('id_date_fin');
    const prochainPaiement = document.getElementById('id_prochain_paiement');
    
    if (dateFin && prochainPaiement) {
        dateFin.addEventListener('change', function() {
            if (this.value && prochainPaiement.value && new Date(this.value) < new Date(prochainPaiement.value)) {
                alert("La date de fin ne peut pas être antérieure au prochain paiement");
                this.value = '';
            }
        });
        
        prochainPaiement.addEventListener('change', function() {
            if (this.value && dateFin.value && new Date(this.value) > new Date(dateFin.value)) {
                alert("Le prochain paiement ne peut pas être postérieur à la date de fin");
                this.value = '';
            }
        });
    }
});