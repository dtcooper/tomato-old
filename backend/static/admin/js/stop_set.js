$(document).on('formset:added', function(event, $row, formsetName) {
    if (formsetName == 'stopsetentry_set') {
        var orders = [0];

        $('input[name$=ordering]:not(input[name*=__prefix__])').each(function(i, elem) {
            orders.push(parseInt($(elem).val()))
        });

        // Make sure the current row isn't included (default is 1)
        var index = orders.indexOf(1);
        if (index !== -1) {
            orders.splice(index, 1);
        }
        console.log(orders);

        var maxOrder = Math.max.apply(null, orders);
        $row.find('input[name$=ordering]').val(maxOrder + 1);
    }
});
