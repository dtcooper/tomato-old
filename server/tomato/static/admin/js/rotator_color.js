var django = django || {};

(function($) {
    $(function() {
        function setRotatorColor() {
            var color = $('#id_color').val();
            $('.color-preview').css('background-color', '#' + rotatorColors[color]);
        }

        $('#id_color').change(setRotatorColor);
        setRotatorColor();
    });
})(django.jQuery || $);
