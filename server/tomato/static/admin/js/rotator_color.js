var django = django || {};

(function($) {
    $(function() {
        var setRotatorColor = function() {
            var color = $('#id_color').val();
            $('.color-preview').css('background-color', '#' + color);
        }

        $('#id_color').change(setRotatorColor);
        setRotatorColor();
    });
})(django.jQuery || $);
