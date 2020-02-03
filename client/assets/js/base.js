var cef = {
    'bridge': _jsBridge,
    'constants': {},
    'close': function() {
        showModal('close-dialog');
    }
};

var isClosing = false;

var afterLoad = function(func) {
    window.addEventListener('cefReady', function() { $(func); })
};

var showModal = function(id) {
    $('#' + id).get(0).showModal();
};

var STATUS_OFFLINE = 'error', STATUS_PENDING = 'warning', STATUS_ONLINE = 'success';
var setStatusColor = function(status) {
    $('#connection-status').removeClass(
        'is-primary is-success is-warning is-error is-disabled').addClass('is-' + status).attr(
        'data-hover-text', 'TODO: this is a major ' + status + ' ' + status + ' ' + status + '!');
};

var sync = function() {
    cef.models.sync().then(loadBlock).catch(function([error]) {
        if (error == cef.constants.API_ERROR_ACCESS_DENIED) {
            $('#login-errors').html('<span class="nes-text is-error">Access denied '
                    + "when sync'ing with server. Please log in again.</span>");
            cef.auth.logout().then(showLoginModal);
        } else {
            loadBlock();
        }
    })
};

var loadBlock = function() {
    cef.models.load_asset_block().then(function([context]) {
        var playQueueTemplate = $('#play-queue-template').html();
        var html = Mustache.render(playQueueTemplate, context);
        $('#play-queue').html(html);
    });
};

afterLoad(function() {
    var dialogs = [
        // Open link
        {'id': 'link', 'title': 'Open Link',
         'body_html': `Open in external browser?<br>
                       -> <span class="nes-text is-primary" id="link-description">#</span>`,
         'buttons': [{'class': 'is-error', 'text': 'Cancel'},
                     {'class': 'is-success', 'text': 'Yes, open it!', 'id': 'link-open-btn'}]},
        // Login
        {'id': 'login', 'title': 'Please Login', 'buttons': [{'class': 'is-success', 'text': 'Login'}],
         'body_html': $('#login-template').html()},
        // Logout
        {'id': 'logout', 'title': 'Logout', 'body': 'Are you sure you want to logout?',
         'buttons': [{'text': 'Cancel'}, {'text': 'Logout', 'class': 'is-error', 'id': 'confirm-logout-btn'}]},
        // Quit
        {'id': 'close', 'title': 'Quit Tomato', 'text': 'Are you sure you want to quit Tomato?',
         'buttons': [{'text': 'Cancel'}, {'text': 'Quit Tomato', 'class': 'is-error', 'id': 'close-btn'}]}
    ]


    var dialogTemplate = $('#dialog-template').html();
    $(dialogs).each(function(i, context) {
        var html = Mustache.render(dialogTemplate, context);
        $('body').append(html);
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
