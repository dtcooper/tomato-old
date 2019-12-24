var django = django || {};

(function($) {
    $(function() {
        $('.show-asset-player').click(function(evt) {
            evt.preventDefault();
            var url = $(this).attr('href');
            var $parent = $(this).parent();
            var urlEscaped = $parent.text(url).text();  // hack to escape HTML in filename
            $parent.html('<audio src="' + urlEscaped
                + '" style="min-width: 300px; width: 100%;" preload="auto" controls />');
        });
    });
})(django.jQuery || $);
