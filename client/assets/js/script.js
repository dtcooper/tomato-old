// Integration with the JS Bridge
cef.close = function() { showModal('close-dialog'); };

// Constants
var STATUS_OFFLINE = 'error',
    STATUS_PENDING = 'warning',
    STATUS_ONLINE = 'success';

// Helpers
function prettyDuration(seconds) {
    seconds = Math.round(seconds);
    minutes = Math.floor(seconds / 60);
    seconds = seconds % 60;
    return minutes + ':' + seconds.toString().padStart(2, '0');
};

var HTMLEntityMap = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;',
                     "'": '&#39;', '/': '&#x2F;', '`': '&#x60;', '=': '&#x3D;'};

function escapeHTML(string) {
    return String(string).replace(/[&<>"'`=\/]/g, function(s) {
        return HTMLEntityMap[s];
    });
}

// Base UI related
var isClosing = false,
    resizeTimer = null;

function setStatusColor(status, text) {
    $('#connection-status').removeClass(
        'is-primary is-success is-warning is-error is-disabled').addClass('is-' + status).attr(
        'data-hover-text', 'TODO: this is a major ' + status + ' ' + status + ' ' + status + '!');
    if (text) {
        $('#connection-status').attr('data-content', text);
    }
}

function closeModal(id) { $('#' + id).get(0).close() };
function showModal(id) { $('#' + id).get(0).showModal(); };

function showError(errorHTML) {
    $('#error-description').html(errorHTML);
    showModal('error-dialog');
};

$(function() {
    $('dialog:not(#close-dialog)').each(function(i, elem) {
        elem.addEventListener('cancel', function(event) {
            event.preventDefault();
        });
    });

    $('body').on('click', 'a', function(event) {
        event.preventDefault();

        var href = $(this).attr('href');
        var linkDescription = $(this).data('description');
        if (!linkDescription) {
            linkDescription = href;
        }

        $('#link-open-btn').data('href', href);
        $('#link-description').text(linkDescription)
        showModal('link-dialog');
    });

    $('#link-open-btn').click(function() {
        window.open($(this).data('href'), '_blank');
    });

    $('#close-btn').click(function(event) {
        event.preventDefault();
        isClosing = true;
        cef.bridge.close_browser();
    });

    $(window).resize(function() {
        if (!isClosing) {  // Avoid a segfault on Mac when closing in fullscreen mode
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {
                if (cef.constants.IS_WINDOWS) {
                    // Windows is funky with resizing and how it computes its window
                    // sizes, so we use win32gui in the backend rather window.innerWidth
                    // and window.innerHeight values.
                    cef.bridge.windows_resize();
                } else {
                    cef.writeconf.update({
                        'width': window.innerWidth,
                        'height': window.innerHeight
                    });
                }
            }, 500);
        }
    });

    window.onerror = function(message, source, lineno, colno, error) {
        if (cef.conf.error) {
            showError(
                'An expected error occurred. You may need to restart '
                + 'Tomato to get it in functioning state.')
        } else {
            showError(escapeHTML(error.stack));
        }
    };
});

// Login related
var doLogin = function([error]) {
    $('#loading').hide();
    $('#login-errors').empty();
    if (error) {
        var elem = $('<span class="nes-text is-error" />').text(error);
        $('#login-errors').append(elem);
        showLoginModal();
    } else {
        setStatusColor(STATUS_ONLINE, 'Logged in!');
        // Reset form back to initial status in case we need it again
        closeModal('login-dialog');
        // TODO: Call a (renamed) check_authorization() func after login
        sync();
        $('#login-dialog form').get(0).reset();
    }
};

var showLoginModal = function() {
    setStatusColor(STATUS_PENDING, 'Logging in...');
    $('#loading').show();
    $('#hostname').val(cef.conf.hostname);
    $('input[name=protocol][value=' + cef.conf.protocol + ']').prop('checked', true);
    showModal('login-dialog');
};

$(function() {
    $('#login-dialog').submit(function(event) {
        $('#loading').show();
        setTimeout(function() {
            cef.auth.login(
                $('input[name=protocol]:checked').val(), $('#hostname').val(),
                $('#username').val(), $('#password').val()
            ).then(doLogin).catch(doLogin);
        }, 350); // A few ms here looks like something is happening
    });

    $('#confirm-logout-btn').click(function(event) {
        cef.auth.logout().then(showLoginModal);
    });

    // TODO: Call this after login
    cef.auth.check_authorization().then(function([isLoggedIn, isConnected, hasSynced]) {
        if (isLoggedIn) {
            $('#loading').hide();
            if (hasSynced) {
                loadBlock();
            } else {
                sync();
            }
            setStatusColor(isConnected ? STATUS_ONLINE : STATUS_OFFLINE, 'Checked authorization');
        } else {
            showLoginModal();
        }
    }).catch(function([error, serverVersion]) {
        showLoginModal();
        if (error == cef.constants.API_ERROR_DB_MIGRATION_MISMATCH) {
            showError(
                '<span class="nes-text is-error">Incompatible Tomato version on the server.</span><br>'
                + 'Our version: ' + cef.constants.VERSION + '<br>'
                + 'Server version: ' + serverVersion);
        }
    });
});

// Sync related

/* Called from python */
var reportSyncProgress = function(percent) { $('#sync-progress').attr('value', percent); }

var sync = function() {
    console.log('Syncing');
    console.log('last sync: ' + cef.conf.last_sync);

    if (!cef.conf.last_sync) {
        showModal('first-sync-dialog');
    }

    cef.models.sync().then(loadBlock).catch(function([error]) {
        closeModal('first-sync-dialog');
        // If we get an access denied or we've never sync'd before, force new login.
        if (error == cef.constants.API_ERROR_ACCESS_DENIED || !cef.conf.last_sync) {
            $('#login-errors').html('<span class="nes-text is-error">An error occurred while'
                    + " synchronizing with the server. <br>Please try logging in again.</span>");
            cef.auth.logout().then(showLoginModal);
        } else {
            setStatusColor('error', 'Error syncing');
            loadBlock();
        }
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

function updateTrackTime() {
    if (wavesurfer) {
        $('#track-time').text(' {' + prettyDuration(wavesurfer.getCurrentTime())
            + '/' + prettyDuration(wavesurfer.getDuration()) + '}');
    }
}

var loadWaveform = function(asset, play = true) {
    if (wavesurfer) {
        wavesurfer.destroy();
        wavesurfer = null;
    }
    $('#waveform').removeClass('nes-pointer').text('');
    var plugins = [
        WaveSurfer.timeline.create({
            container: "#waveform-timeline",
            formatTimeCallback: prettyDuration,
            fontFamily: 'Tomato Text',
            fontSize: 11,
            height: 11,
            labelPadding: 3
      }),
    ]

    if (cef.conf.clickable_waveform) {
        plugins.push(WaveSurfer.cursor.create());
        $('#waveform').addClass('nes-pointer');
    }

    wavesurfer = WaveSurfer.create({
        container: '#waveform',
        waveColor: shadeColor('#' + asset.color, -3),
        progressColor: shadeColor('#' + asset.color, -22),
        height: 100,
        normalize: true,
        barMinHeight: 1,
        barWidth: 3,
        barGap: 3,
        hideScrollbar: true,
        interact: cef.conf.clickable_waveform,
        responsive: true,
        cursorWidth: 1,
        cursorColor: '#f30000',
        closeAudioContext: true,
        backend: 'MediaElement',  // less modern backend, but loads faster
        plugins: plugins
    });
    wavesurfer.on('finish', loadNext);
    wavesurfer.on('audioprocess', updateTrackTime);
    wavesurfer.on('interaction', updateTrackTime);
    wavesurfer.on('ready', function() {
        updateTrackTime();
        if (play) {
            wavesurfer.play()
        };
    });
    wavesurfer.load(asset.url);
    $('#track-title').text(': ' + asset.name);
    $('#track-time').text(' {0:00/' + prettyDuration(asset.length) + '}');
    $('.asset-item[data-asset-idx=' + assetIdx + ']').css('background-color', '#90caf9');
}

var loadNext = function(play = true) {
    $('.asset-item').css('background-color', 'initial');
    if (assetIdx < assets.length) {
        loadWaveform(assets[assetIdx], play);
        assetIdx++;
    } else {
        $('#track-title').text(': Waiting...');
        $('#track-time').text('');
        if (wavesurfer) {
            wavesurfer.destroy();
            wavesurfer = null;
        }
        $('#waveform').text('Should wait for ' + prettyDuration(wait));
    }
}

var loadBlock = function() {
    setStatusColor('warning', 'Loading asset block');
    closeModal('first-sync-dialog');
    cef.models.load_asset_block().then(function([context]) {
        assets = Array.from(context.assets);
        assetIdx = 0;
        wait = context.wait;
        cef.template.render('asset_block.html', context).then(function([html]) {
            setStatusColor('success', 'Asset block loaded');
            $('#play-queue').html(html);
            loadNext(false);
        });
    });
};

$(function() {
    $('#next-btn').click(function() { loadNext(wavesurfer ? wavesurfer.isPlaying() : false) });
    $('body').on('click', '.asset-item', function() {
        assetIdx = parseInt($(this).data('asset-idx'), 0);
        loadNext(wavesurfer ? wavesurfer.isPlaying() : false);
    });

    $(document).keydown(function(event) {
        if (wavesurfer && cef.conf.clickable_waveform) {
            switch(event.keyCode) {
                case 37:
                    wavesurfer.skipBackward();
                    break;
                case 39:
                    wavesurfer.skipForward();
                    break;
            }
        }
    });
});
