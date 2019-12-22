var django = django || {};

(function($) {
    var rotatorColors = JSON.parse(document.getElementById(
        'rotator-colors').textContent);

    $(function() {
        /* Rotators admin */
        var setColorRotatorAdmin = function() {
            var color = $('#id_color').val();
            $('.color-preview').css('background-color', '#' + color);
        }

        $('#id_color').change(setColorRotatorAdmin);
        setColorRotatorAdmin();
    });
})(django.jQuery || $);
