$(function() {

    $('a.link').click(function(event) {
        event.preventDefault();
        open_link($(this).attr('href'));
    });
});
