if (!$) { $ = django.jQuery; }

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


        /* StopSets + Assets admin */
        var setColorStopSetsAndAssetsAdmin = function($elem) {
            var color = rotatorColors[$elem.val()];
            if (!color) {
                color = 'ffffff';
            }
            $elem.closest('tr, fieldset').find('.color-preview').css(
                'background-color', '#' + color);
        }
        $('body').on('change', 'select[name$="rotator"]', function() {
            setColorStopSetsAndAssetsAdmin($(this));
        });

        $('select[name$="rotator"]').each(function(i, elem) {
            setColorStopSetsAndAssetsAdmin($(elem));
        });
    });
})($ || django.jQuery);
