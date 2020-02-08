var reportSyncProgress = function(percent) { $('#sync-progress').attr('value', percent); }

var sync = function() {
    console.log('Syncing');
    cef.conf.get('last_sync').then(function([lastSync]) {
        console.log('last sync: ' + lastSync);

        if (!lastSync) {
            showModal('first-sync-dialog');
        }

        cef.models.sync().then(loadBlock).catch(function([error]) {
            closeModal('first-sync-dialog');
            // If we get an access denied or we've never sync'd before, force new login.
            if (error == cef.constants.API_ERROR_ACCESS_DENIED || !lastSync) {
                $('#login-errors').html('<span class="nes-text is-error">An error occurred while'
                        + " synchronizing with the server. <br>Please try logging in again.</span>");
                cef.auth.logout().then(showLoginModal);
            } else {
                setStatusColor('error');
                loadBlock();
            }
        })
    });
};

var loadBlock = function() {
    closeModal('first-sync-dialog');
    cef.models.load_asset_block().then(function([context]) {
        var playQueueTemplate = $('#play-queue-template').html();
        var html = Mustache.render(playQueueTemplate, context);
        $('#play-queue').html(html);
    });
};
