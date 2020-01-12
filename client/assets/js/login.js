var doLogin = function(error) {
    $('#loading').hide();
    $('#login-errors').empty();
    if (error) {
        var elem = $('<span class="nes-text is-error" />').text(error);
        $('#login-errors').append(elem);
        showLoginModal();
    } else {
        setStatusColor('success');
        // Reset form back to initial status in case we need it again
        $('#login-dialog').get(0).close();
        $('#login-dialog form').get(0).reset();
        $('#login-status').text('Logged in!');
    }
};

var showLoginModal = function() {
    setStatusColor('warning');
    showModal('login-dialog');
};

var setStatusColor = function(cssClass) {
    $('#connection-status').removeClass(
        'is-primary is-success is-warning is-error is-disabled').addClass('is-' + cssClass);
};


$(function() {
    $('#login-dialog').submit(function(event) {
        $('#loading').show();
        setTimeout(function() {
            cef.auth.login(
                $('#username').val(),
                $('#password').val(),
                $('input[name=protocol]:checked').val(),
                $('#hostname').val(),
                doLogin
            );
        }, 350); // A few ms here looks like something is happening
    });

    $('dialog:not(#close-dialog)').each(function(i, elem) {
        elem.addEventListener('cancel', function(event) {
            event.preventDefault();
        });
    });

    $('#logout-btn').click(function() {
        showModal('logout-dialog')
    });
    $('#confirm-logout-btn').click(function(event) {
        cef.auth.logout(showLoginModal);
    });

    cef.auth.check_authorization(function(isLoggedIn, isConnected) {
        if (!isLoggedIn) {
            showLoginModal()
        } else {
            setStatusColor(isConnected ? 'success' : 'error');
        }
    });

    $('#loading').hide();
});
