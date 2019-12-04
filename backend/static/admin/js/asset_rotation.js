$(function() {
    var setColor = function() {
        var color = $('#id_color').val();
        $('#id_color_preview').css('background-color', '#' + color);
    }

    $('#id_color').change(setColor);
    setColor();
});
