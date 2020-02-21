cef.close = function() { ui.showModal('close-dialog'); };

var STATUS_OFFLINE = 'error', STATUS_PENDING = 'warning', STATUS_ONLINE = 'success';

var prettyDuration = function(seconds) {
    seconds = Math.round(seconds);
    minutes = Math.floor(seconds / 60);
    seconds = seconds % 60;
    return minutes + ':' + seconds.toString().padStart(2, '0');
};

class BaseUI {
    constructor() {
        this.isClosing =false;
        this.resizeTimer = null;
    };

    setStatusColor(status, text) {
        $('#connection-status').removeClass(
            'is-primary is-success is-warning is-error is-disabled').addClass('is-' + status).attr(
            'data-hover-text', 'TODO: this is a major ' + status + ' ' + status + ' ' + status + '!');
        if (text) {
            $('#connection-status').attr('data-content', text);
        }
    }

    closeModal(id) { $('#' + id).get(0).close() };
    showModal(id) { $('#' + id).get(0).showModal(); };

    bindEvents() {
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
            ui.showModal('link-dialog');
        });

        $('#link-open-btn').click(function() {
            window.open($(this).data('href'), '_blank');
        });

        $('#close-btn').click(function(event) {
            event.preventDefault();
            ui.isClosing = true;
            cef.bridge.close_browser();
        });

        $(window).resize(function() {
            if (!ui.isClosing) {  // Avoid a segfault on Mac when closing in fullscreen mode
                clearTimeout(ui.resizeTimer);
                ui.resizeTimer = setTimeout(function() {
                    if (cef.constants.IS_WINDOWS) {
                        // Windows is funky with resizing and how it computes its window
                        // sizes, so we use win32gui in the backend rather window.innerWidth
                        // and window.innerHeight values.
                        cef.bridge.windows_resize();
                    } else {
                        cef.writeconf.update({
                            'width': window.innerWidth,
                            'height': window.innerHeight
                        });
                    }
                }, 500);
            }
        });

        window.onerror = function(message, source, lineno, colno, error) {
            $('#js-error').text(error.stack);
            ui.showModal('error-dialog');
        };
    };

};

var ui = new BaseUI();
$(ui.bindEvents);
