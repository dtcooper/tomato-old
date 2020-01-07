$(function() {
    $('#noauth').change(function() {
        var checked = $(this).prop('checked');
        if (checked) {
            $('.auth-field').hide();
        } else {
            $('.auth-field').show();
        }
    });

    $('#login-dialog').submit(function(event) {
        event.preventDefault();
        var user, pass;

        if ($('#noauth').prop('checked')) {
            user = '';
            pass = '';
        } else {
            user = $('#username').val();
            pass = $('#password').val();
        }

        var proto = $('input[name=http-or-https]:checked').val();

        var callback = function(authenticated) {
            if (authenticated) {
                $('#login-dialog').get(0).close();
                $('#login-dialog form').get(0).reset();
                $('.auth-field').show();
            } else {
                // TODO append to $('#login-errors')
            }
        }

        auth.login(user, pass, proto, $('#url').val(), callback);
    });

    $('#open-login').click(function() {
        $('#login-dialog').get(0).showModal();
    });

    setTimeout(function() { $('#loading').hide(); }, 500);
});
