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
                html += '<tr><td>' + asset.name + '</td><td><audio src="' + cef.constants.MEDIA_URL
                    + asset.audio + '" controls></audio></td></tr>\n';
            }
        }
        html += '</tbody></table></div>'
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
    });c
}

afterLoad(function() {
    $('a.link').click(function(event) {
        event.preventDefault();
        $('#link-url').text($(this).attr('href'));
        showModal('link-dialog');
    });

    $('#close-btn').click(function(event) {
        event.preventDefault();
        isClosing = true;
        cef.internal.close_browser();
    });

    var resizeTimer;
    $(window).resize(function() {
      if (!isClosing) {  // Avoid a segfault on Mac when closing in fullscreen mode
          clearTimeout(resizeTimer);
          resizeTimer = setTimeout(function() {
            cef.conf.update({'width': window.outerWidth,
                             'height': window.outerHeight});
          }, 500);
        }
    });
});
