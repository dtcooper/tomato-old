cef.close = function() { showModal('close-dialog'); };

var isClosing = false;

function closeModal(id) { $('#' + id).get(0).close() };
function showModal(id) { $('#' + id).get(0).showModal(); };

var STATUS_OFFLINE = 'error', STATUS_PENDING = 'warning', STATUS_ONLINE = 'success';
var setStatusColor = function(status, text) {
    $('#connection-status').removeClass(
        'is-primary is-success is-warning is-error is-disabled').addClass('is-' + status).attr(
        'data-hover-text', 'TODO: this is a major ' + status + ' ' + status + ' ' + status + '!');
    if (text) {
        $('#connection-status').attr('data-content', text);
    }
};

$(function() {
    $('dialog:not(#close-dialog)').each(function(i, elem) {
        elem.addEventListener('cancel', function(event) {
            event.preventDefault();
        });
    });

    $('body').on('click', 'a', function(event) {
        event.preventDefault();

        var href = $(this).attr('href');
        var linkDescription = $(this).data('description');
        if (!linkDescription) {
            linkDescription = href;
        }

        $('#link-open-btn').data('href', href);
        $('#link-description').text(linkDescription)
        showModal('link-dialog');
    });

    $('#link-open-btn').click(function() {
        window.open($(this).data('href'), '_blank');
    });

    $('#close-btn').click(function(event) {
        event.preventDefault();
        isClosing = true;
        cef.bridge.close_browser();
    });

    var resizeTimer;
    $(window).resize(function() {
        if (!isClosing) {  // Avoid a segfault on Mac when closing in fullscreen mode
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {
                if (cef.constants.IS_WINDOWS) {
                    // Windows is funky with resizing and how it computes its window
                    // sizes, so we use win32gui in the backend rather window.innerWidth
                    // and window.innerHeight values.
                    cef.bridge.windows_resize();
                } else {
                    cef.conf.update({
                        'width': window.innerWidth,
                        'height': window.innerHeight
                    });
                }
            }, 500);
        }
    });
});
