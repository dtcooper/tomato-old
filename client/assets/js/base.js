window.addEventListener('pywebviewready', function() {
    $(function() {
        $('a.link').click(function(event) {
            event.preventDefault();
            $('#link-url').text($(this).attr('href'));
            $('#link-dialog').get(0).showModal();
        });

        $('#link-open').click(function() {
            openLink($('#link-url').text());
        });
    });
});
