document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('items-table');
    
    function calculateTotals() {
        let totalHT = 0;
        let totalTVA = 0;
        
        table.querySelectorAll('tbody tr').forEach(row => {
            const qte = parseFloat(row.querySelector('[name$="-quantite"]').value) || 0;
            const prix = parseFloat(row.querySelector('[name$="-prix_unitaire"]').value) || 0;
            const tva = parseFloat(row.querySelector('[name$="-taux_tva"]').value) || 0;
            
            const montantHT = qte * prix;
            const montantTVA = montantHT * (tva / 100);
            
            row.querySelector('.montant-ht').textContent = montantHT.toFixed(2);
            totalHT += montantHT;
            totalTVA += montantTVA;
        });
        
        const remise = parseFloat(document.getElementById('id_remise').value) || 0;
        const totalTTC = totalHT + totalTVA - remise;
        
        document.getElementById('total-ht').textContent = totalHT.toFixed(2);
        document.getElementById('total-tva').textContent = totalTVA.toFixed(2);
        document.getElementById('total-ttc').textContent = totalTTC.toFixed(2);
    }
    
    table.addEventListener('change', function(e) {
        if (e.target.matches('[name$="-quantite"], [name$="-prix_unitaire"], [name$="-taux_tva"]')) {
            calculateTotals();
        }
    });
    
    document.getElementById('id_remise').addEventListener('change', calculateTotals);
    
    // Initial calculation
    calculateTotals();
});