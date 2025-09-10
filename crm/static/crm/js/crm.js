// JavaScript spécifique au CRM
document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Gestion des formulaires modaux
    $('.modal-form').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var url = button.data('url');
        var modal = $(this);
        
        $.get(url, function(data) {
            modal.find('.modal-content').html(data);
        });
    });

    // Auto-refresh des données
    function refreshCRMData() {
        // Implémentez l'auto-refresh si nécessaire
    }

    // Refresh toutes les 30 secondes
    setInterval(refreshCRMData, 30000);
});