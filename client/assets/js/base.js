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
    showModal('close-dialog');
};

var STATUS_OFFLINE = 'error', STATUS_PENDING = 'warning', STATUS_ONLINE = 'success';
var setStatusColor = function(status) {
    $('#connection-status').removeClass(
        'is-primary is-success is-warning is-error is-disabled').addClass('is-' + status).attr(
        'data-hover-text', 'TODO: this is a major ' + status + ' ' + status + ' ' + status + '!');
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
});
