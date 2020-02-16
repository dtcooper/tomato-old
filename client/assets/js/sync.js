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

var wavesurfer = null;
var wait = null;
var assetIdx = 0;
var assets = [];

function shadeColor(color, percent) {

    var R = parseInt(color.substring(1,3),16);
    var G = parseInt(color.substring(3,5),16);
    var B = parseInt(color.substring(5,7),16);

    R = parseInt(R * (100 + percent) / 100);
    G = parseInt(G * (100 + percent) / 100);
    B = parseInt(B * (100 + percent) / 100);

    R = (R<255)?R:255;
    G = (G<255)?G:255;
    B = (B<255)?B:255;

    var RR = ((R.toString(16).length==1)?"0"+R.toString(16):R.toString(16));
    var GG = ((G.toString(16).length==1)?"0"+G.toString(16):G.toString(16));
    var BB = ((B.toString(16).length==1)?"0"+B.toString(16):B.toString(16));

    return "#"+RR+GG+BB;
}

var loadWaveform = function(asset, play = true) {
    if (wavesurfer) {
        wavesurfer.destroy();
        wavesurfer = null;
    }
    $('#waveform').text('');
    wavesurfer = WaveSurfer.create({
        container: '#waveform',
        waveColor: shadeColor('#' + asset.color, -3),
        progressColor: shadeColor('#' + asset.color, -15),
        normalize: true,
        height: 128,
        barWidth: 3,
        minBarHeight: 1,
        barGap: 3,
        hideScrollbar: true,
        responsive: true,
        cursorWidth: 2,
        cursorColor: '#f30000',
        closeAudioContext: true,
        plugins: [
            WaveSurfer.timeline.create({
                container: "#waveform-timeline",
                height: 10
          }),
          WaveSurfer.cursor.create({width: 2})
        ]
    });
    wavesurfer.on('finish', loadNext);
    if (play) {
        wavesurfer.on('ready', function() { wavesurfer.play() });
    }
    wavesurfer.load(asset.url);
    $('#track-title').text(': ' + asset.name + ' (' + asset.length + ' secs)');
    $('.asset-item[data-asset-idx=' + assetIdx + ']').css('background-color', '#90caf9');
}

var loadNext = function(play = true) {
    $('.asset-item').css('background-color', 'initial');
    if (assetIdx < assets.length) {
        loadWaveform(assets[assetIdx], play);
        assetIdx++;
    } else {
        $('#track-title').text(': Waiting...');
        if (wavesurfer) {
            wavesurfer.destroy();
            wavesurfer = null;
        }
        $('#waveform').text('Should wait for ' + wait + ' seconds...');
    }
}

var loadBlock = function() {
    ui.setStatusColor('warning', 'Loading asset block');
    ui.closeModal('first-sync-dialog');
    cef.models.load_asset_block().then(function([context]) {
        assets = Array.from(context.assets);
        assetIdx = 0;
        wait = context.wait;
        cef.template.render('asset_block.html', context).then(function([html]) {
            ui.setStatusColor('success', 'Asset block loaded');
            $('#play-queue').html(html);
            loadNext(false);
        });
    });
};

$(function() {
    $('#next-btn').click(function() { loadNext(false) });
    $('body').on('click', '.asset-item', function() {
        assetIdx = parseInt($(this).data('asset-idx'), 0);
        loadNext(false);
    });
});
