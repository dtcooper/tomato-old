$(function() {
    $('a.link').click(function(event) {
        event.preventDefault();
        openLink($(this).attr('href'));
    });
});
