// main.js

// Ensure jQuery is loaded first.
// Initialize tooltips and popovers, auto-dismiss alerts, and theme switcher
$(function () {
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-bs-toggle="popover"]').popover();
    
    // Auto-dismiss alerts
    $('.alert').delay(5000).fadeOut('slow');
    
    // Theme switcher
    $('#theme-switcher').on('click', function() {
        const currentTheme = $('html').attr('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        $('html').attr('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
    
    // Check for saved theme preference
    if (localStorage.getItem('theme')) {
        $('html').attr('data-bs-theme', localStorage.getItem('theme'));
    }
});

// Use vanilla JS for the table calculations as it's more efficient
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

// AJAX loading indicator (can also use vanilla JS for this)
$(document).ajaxStart(function() {
    $('#page-loader').removeClass('d-none');
});

$(document).ajaxStop(function() {
    $('#page-loader').addClass('d-none');
});