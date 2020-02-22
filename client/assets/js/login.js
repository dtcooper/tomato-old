var doLogin = function([error]) {
    $('#loading').hide();
    $('#login-errors').empty();
    if (error) {
        var elem = $('<span class="nes-text is-error" />').text(error);
        $('#login-errors').append(elem);
        showLoginModal();
    } else {
        ui.setStatusColor(STATUS_ONLINE, 'Logged in!');
        // Reset form back to initial status in case we need it again
        ui.closeModal('login-dialog');
        // TODO: Call a (renamed) check_authorization() func after login
        sync();
        $('#login-dialog form').get(0).reset();
    }
};

var showLoginModal = function() {
    ui.setStatusColor(STATUS_PENDING, 'Logging in...');
    $('#loading').show();
    $('#hostname').val(cef.conf.hostname);
    $('input[name=protocol][value=' + cef.conf.protocol + ']').prop('checked', true);
    ui.showModal('login-dialog');
};

$(function() {
    $('#login-dialog').submit(function(event) {
        $('#loading').show();
        setTimeout(function() {
            cef.auth.login(
                $('input[name=protocol]:checked').val(), $('#hostname').val(),
                $('#username').val(), $('#password').val()
            ).then(doLogin).catch(doLogin);
        }, 350); // A few ms here looks like something is happening
    });

    $('#confirm-logout-btn').click(function(event) {
        cef.auth.logout().then(showLoginModal);
    });

    // TODO: Call this after login
    cef.auth.check_authorization().then(function([isLoggedIn, isConnected, hasSynced]) {
        if (isLoggedIn) {
            $('#loading').hide();
            if (hasSynced) {
                loadBlock();
            } else {
                sync();
            }
            ui.setStatusColor(isConnected ? STATUS_ONLINE : STATUS_OFFLINE, 'Checked authorization');
        } else {
            showLoginModal();
        }
    }).catch(function([error, serverVersion]) {
        showLoginModal();
        if (error == cef.constants.API_ERROR_DB_MIGRATION_MISMATCH) {
            ui.showError(
                '<span class="nes-text is-error">Incompatible Tomato version on the server.</span><br>'
                + 'Our version: ' + cef.constants.VERSION + '<br>'
                + 'Server version: ' + serverVersion);
        }
    });
});
