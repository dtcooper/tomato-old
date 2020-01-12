var cef = {
    'internal': _cefInternal,
    'is_windows': false,
    'is_macos': false,
    'client': {}
};

var afterLoad = function(func) {
    window.addEventListener('cefReady', function() { $(func); })
};

var showModal = function(id) {
    $('#' + id).get(0).showModal();
};

cef.client.showCloseModal = function() {
    showModal('close-dialog')
};

var setStatusColor = function(cssClass) {
    $('#connection-status-text').removeClass(
        'is-primary is-success is-warning is-error is-disabled').addClass('is-' + cssClass).attr(
        'data-tooltip', 'TODO: this is a major ' + cssClass + ' ' + cssClass + ' ' + cssClass + '!');

};

afterLoad(function() {
    $('a.link').click(function(event) {
        event.preventDefault();
        $('#link-url').text($(this).attr('href'));
        showModal('link-dialog');
    });

    $('#link-open-btn').click(function() {
        window.open($('#link-url').text(), '_blank');
    });

    $('#close-btn').click(function(event) {
        event.preventDefault();
        cef.internal.close_browser();
    });

    if (cef.is_windows) {
        $('.windows-only').show();
    }
});
