var cef = {
    'internal': _cefInternal,
    'is_windows': false,
    'is_macos': false,
    'client': {}
};

var showModal = function(id) {
    $('#' + id).get(0).showModal();
};

cef.client.showCloseModal = function() {
    showModal('close-dialog')
};

$(function() {
    $('a.link').click(function(event) {
        event.preventDefault();
        $('#link-url').text($(this).attr('href'));
        showModal('link-dialog');
    });

    $('#link-open').click(function() {
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
