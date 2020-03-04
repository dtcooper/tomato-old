ACTION_PARTIAL_STOPSET = 'partial_stopset'
ACTION_PLAYED_ASSET = 'played_asset'
ACTION_PLAYED_STOPSET = 'played_stopset'
ACTION_SKIPPED_ASSET = 'skipped_asset'
ACTION_SKIPPED_STOPSET = 'skipped_stopset'
ACTION_WAITED = 'waited'

CLIENT_CONFIG_KEYS = {
    # Map to default values
    'clickable_waveform': False,
    'fade_assets_ms': 0,
    'wait_interval_minutes': 20,
    'wait_interval_subtracts_stopset_playtime': False,
}

# Snarfed from https://materializecss.com/color.html
COLORS = (
    ('red', 'f44336'),
    ('red-light', 'e57373'),
    ('red-dark', 'c62828'),
    ('pink', 'e91e63'),
    ('pink-light', 'f06292'),
    ('pink-dark', 'ad1457'),
    ('purple', '9c27b0'),
    ('purple-light', 'ba68c8'),
    ('purple-dark', '6a1b9a'),
    ('deep-purple', '673ab7'),
    ('deep-purple-light', '9575cd'),
    ('deep-purple-dark', '4527a0'),
    ('indigo', '3f51b5'),
    ('indigo-light', '7986cb'),
    ('indigo-dark', '283593'),
    ('blue', '2196f3'),
    ('blue-light', '64b5f6'),
    ('blue-dark', '1565c0'),
    ('light-blue', '03a9f4'),
    ('light-blue-light', '4fc3f7'),
    ('light-blue-dark', '0277bd'),
    ('cyan', '00bcd4'),
    ('cyan-light', '4dd0e1'),
    ('cyan-dark', '00838f'),
    ('teal', '009688'),
    ('teal-light', '4db6ac'),
    ('teal-dark', '00695c'),
    ('green', '4caf50'),
    ('green-light', '81c784'),
    ('green-dark', '2e7d32'),
    ('light-green', '8bc34a'),
    ('light-green-light', 'aed581'),
    ('light-green-dark', '558b2f'),
    ('lime', 'cddc39'),
    ('lime-light', 'dce775'),
    ('lime-dark', '9e9d24'),
    ('yellow', 'ffeb3b'),
    ('yellow-light', 'fff176'),
    ('yellow-dark', 'f9a825'),
    ('amber', 'ffc107'),
    ('amber-light', 'ffd54f'),
    ('amber-dark', 'ff8f00'),
    ('orange', 'ff9800'),
    ('orange-light', 'ffb74d'),
    ('orange-dark', 'ef6c00'),
    ('deep-orange', 'ff5722'),
    ('deep-orange-light', 'ff8a65'),
    ('deep-orange-dark', 'd84315'),
)
