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

var assetLoadTest = function() {
    cef.models.test_load_assets().then(function(assets) {
        var html = '<div class="nes-table-responsive">'
            +'<table class="nes-table is-bordered is-centered">'
            + '<thead><th>Asset</th><th>Player</th></thead><tbody>';

        if (assets.length == 0) {
            html += '<tr><td colspan="2">No assets found!</td></tr>'
        } else {
            for (var i = 0; i < assets.length; i++) {
                var asset = assets[i];
                var url = cef.constants.MEDIA_URL + asset.audio;
                html += '<tr><td><a href="' + url + '">' + asset.name
                    + '</a></td><td><audio src="' + url + '" controls></audio></td></tr>\n';
            }
        }
        html += '</tbody></table></div>';
        $('#asset-list').html(html);
    });
};

var sync = function() {
    cef.models.sync().catch(function([error]) {
        if (error == cef.constants.API_ERROR_ACCESS_DENIED) {
            $('#login-errors').html('<span class="nes-text is-error">Access denied '
                    + "when sync'ing with server. Please log in again.</span>");
            cef.auth.logout().then(showLoginModal);
        }
    });
}

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
        console.log(html);
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
});
