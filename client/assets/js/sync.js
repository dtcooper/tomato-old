var reportSyncProgress = function(percent) { $('#sync-progress').attr('value', percent); }

var sync = function() {
    console.log('Syncing');
    cef.conf.get('last_sync').then(function([lastSync]) {
        console.log('last sync: ' + lastSync);

        if (!lastSync) {
            ui.showModal('first-sync-dialog');
        }

        cef.models.sync().then(loadBlock).catch(function([error]) {
            ui.closeModal('first-sync-dialog');
            // If we get an access denied or we've never sync'd before, force new login.
            if (error == cef.constants.API_ERROR_ACCESS_DENIED || !lastSync) {
                $('#login-errors').html('<span class="nes-text is-error">An error occurred while'
                        + " synchronizing with the server. <br>Please try logging in again.</span>");
                cef.auth.logout().then(showLoginModal);
            } else {
                ui.setStatusColor('error', 'Error syncing');
                loadBlock();
            }
        })
    });
};

var loadBlock = function() {
    ui.setStatusColor('warning', 'Loading asset block');
    ui.closeModal('first-sync-dialog');
    cef.models.load_asset_block().then(function([context]) {
        cef.template.render('asset_block.html', context).then(function([html]) {
            ui.setStatusColor('success', 'Asset block loaded');
            $('#play-queue').html(html);
        });
    });
};
