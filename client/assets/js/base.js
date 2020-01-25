var cef = {
    'internal': _cefInternal,
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
        cef.internal.close_browser();
    });
});
