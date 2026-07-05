import argparse
import sys
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(abspath(__file__))))

import updateAzaanTimers as uat  # noqa: E402


def make_args(**overrides):
    defaults = dict(
        lat=None, lng=None, method=None, fajr_azaan_vol=None, azaan_vol=None,
        cron_user=None, dry_run=False, disable_random_audio=False,
    )
    for prayer in uat.PRAYER_NAMES:
        defaults['{}_audio'.format(prayer)] = None
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def test_merge_args_requires_no_settings_file(tmp_path, monkeypatch):
    settings_file = tmp_path / '.settings'
    monkeypatch.setattr(uat, 'SETTINGS_FILE', str(settings_file))

    args = make_args(lat=30.0, lng=60.0, method='Egypt')
    lat, lng, method, fajr_vol, azaan_vol, cron_user, audio_files = uat.merge_args(args)

    assert lat == 30.0
    assert lng == 60.0
    assert method == 'Egypt'
    assert fajr_vol == 0
    assert azaan_vol == 0
    assert cron_user  # defaults to current user
    assert audio_files == uat.DEFAULT_AUDIO_FILES
    assert settings_file.exists()


def test_merge_args_persists_and_reloads_settings(tmp_path, monkeypatch):
    settings_file = tmp_path / '.settings'
    monkeypatch.setattr(uat, 'SETTINGS_FILE', str(settings_file))

    first_args = make_args(lat=30.0, lng=60.0, method='Egypt', cron_user='testuser',
                            fajr_audio='custom-fajr.mp3')
    uat.merge_args(first_args)

    # A subsequent run without CLI args should reuse the saved settings.
    second_args = make_args()
    lat, lng, method, fajr_vol, azaan_vol, cron_user, audio_files = uat.merge_args(second_args)

    assert lat == 30.0
    assert lng == 60.0
    assert method == 'Egypt'
    assert cron_user == 'testuser'
    assert audio_files['fajr'] == 'custom-fajr.mp3'
    assert audio_files['dhuhr'] == uat.DEFAULT_AUDIO_FILES['dhuhr']


def test_merge_args_cli_overrides_saved_settings(tmp_path, monkeypatch):
    settings_file = tmp_path / '.settings'
    monkeypatch.setattr(uat, 'SETTINGS_FILE', str(settings_file))

    uat.merge_args(make_args(lat=30.0, lng=60.0, method='Egypt'))
    lat, lng, method, *_ = uat.merge_args(make_args(method='ISNA'))

    assert method == 'ISNA'
    assert lat == 30.0


def test_merge_args_handles_corrupt_settings_file(tmp_path, monkeypatch):
    settings_file = tmp_path / '.settings'
    settings_file.write_text('not,enough,fields')
    monkeypatch.setattr(uat, 'SETTINGS_FILE', str(settings_file))

    args = make_args(lat=30.0, lng=60.0, method='Egypt')
    lat, lng, method, *_ = uat.merge_args(args)

    assert lat == 30.0
    assert method == 'Egypt'


def test_get_available_athans_excludes_fajr_and_dua_files(tmp_path, monkeypatch):
    monkeypatch.setattr(uat, 'ROOT_DIR', str(tmp_path))
    for name in ['Adhan-fajr.mp3', 'Adhan-Madinah.mp3', 'Adhan-Makkah.mp3',
                 'Adhan-Makkah-Dua.mp3', 'DuaAfterAdhan.mp3', 'notes.txt']:
        (tmp_path / name).write_text('')

    athans = uat.get_available_athans()

    assert athans == ['Adhan-Madinah.mp3', 'Adhan-Makkah.mp3']


def test_randomize_audio_files_skips_cli_override(tmp_path, monkeypatch):
    monkeypatch.setattr(uat, 'ROOT_DIR', str(tmp_path))
    for name in ['Adhan-fajr.mp3', 'Adhan-Madinah.mp3', 'Adhan-Makkah.mp3']:
        (tmp_path / name).write_text('')

    audio_files = dict(uat.DEFAULT_AUDIO_FILES)
    args = make_args(dhuhr_audio='Adhan-Makkah.mp3')
    audio_files['dhuhr'] = 'Adhan-Makkah.mp3'

    result = uat.randomize_audio_files(audio_files, args)

    assert result['dhuhr'] == 'Adhan-Makkah.mp3'
    assert result['fajr'] == uat.DEFAULT_AUDIO_FILES['fajr']


def test_randomize_audio_files_skips_settings_customization(tmp_path, monkeypatch):
    monkeypatch.setattr(uat, 'ROOT_DIR', str(tmp_path))
    for name in ['Adhan-fajr.mp3', 'Adhan-Madinah.mp3', 'Adhan-Makkah.mp3']:
        (tmp_path / name).write_text('')

    audio_files = dict(uat.DEFAULT_AUDIO_FILES)
    audio_files['asr'] = 'Adhan-Makkah.mp3'  # previously customized via settings
    args = make_args()

    result = uat.randomize_audio_files(audio_files, args)

    assert result['asr'] == 'Adhan-Makkah.mp3'


def test_randomize_audio_files_randomizes_uncustomized_prayers(tmp_path, monkeypatch):
    monkeypatch.setattr(uat, 'ROOT_DIR', str(tmp_path))
    for name in ['Adhan-fajr.mp3', 'Adhan-Madinah.mp3', 'Adhan-Makkah.mp3', 'Adhan-Turkish.mp3']:
        (tmp_path / name).write_text('')
    monkeypatch.setattr(uat.random, 'choice', lambda seq: 'Adhan-Turkish.mp3')

    audio_files = dict(uat.DEFAULT_AUDIO_FILES)
    args = make_args()

    result = uat.randomize_audio_files(audio_files, args)

    assert result['fajr'] == uat.DEFAULT_AUDIO_FILES['fajr']
    for prayer in ('dhuhr', 'asr', 'maghrib', 'isha'):
        assert result[prayer] == 'Adhan-Turkish.mp3'
