// Initialize tooltips
$(function () {
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

// AJAX loading indicator
$(document).ajaxStart(function() {
    $('#page-loader').removeClass('d-none');
});

$(document).ajaxStop(function() {
    $('#page-loader').addClass('d-none');
});