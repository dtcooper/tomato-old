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

$(function() {
    $('#login-dialog').submit(function(event) {
        event.preventDefault();
        auth.login($('#username').val(), $('#password').val(),
                   $('input[name=protocol]:checked').val(), $('#hostname').val());
    });

    $('dialog').each(function(i, elem) {
        dialogPolyfill.registerDialog(elem);
    });

    $('#login-btn').click(showLoginModal);

    //auth.check_authorization();
    $('#loading').hide();
});
