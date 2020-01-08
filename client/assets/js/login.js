var doLogin = function(error) {
    $('#login-errors').empty();
    if (error) {
        var elem = $('<span class="nes-text is-error" />').text(error);
        $('#login-errors').append(elem);
    } else {
        // Reset form back to initial status in case we need it again
        $('#login-dialog').get(0).close();
        $('#login-dialog form').get(0).reset();

        $('#login-status').text('Logged in!');
    }
};

var showLoginModal = function() {
    $('#login-dialog').get(0).showModal();
};

window.addEventListener('pywebviewready', function() {
    $(function() {
        $('#login-dialog').submit(function(event) {
            event.preventDefault();
            pywebview.api.login({
                'username': $('#username').val(),
                'password': $('#password').val(),
                'protocol': $('input[name=protocol]:checked').val(),
                'hostname': $('#hostname').val()
            }).then(doLogin)
        });

        $('dialog').each(function(i, elem) {
            dialogPolyfill.registerDialog(elem);
            elem.addEventListener('cancel', function(event) {
                event.preventDefault();
            });
        });

        $('#login-btn').click(showLoginModal);
        $('#logout-btn').click(function() {
            pywebview.api.logout().then(showLoginModal);
        });

        pywebview.api.check_authorization().then(function(isLoggedIn) {
            if (!isLoggedIn) {
                showLoginModal();
            }
        });
        $('#loading').hide();
    });
});
