#!/usr/bin/env python3

import datetime
import getpass
import time
import sys
from os.path import dirname, abspath, join as pathjoin
import argparse

from praytimes import PrayTimes
from crontab import CronTab

ROOT_DIR = dirname(abspath(__file__))
SETTINGS_FILE = pathjoin(ROOT_DIR, '.settings')
JOB_COMMENT = 'rpiAdhanClockJob'

# Cron schedule for the daily job that recalculates prayer times and
# reinstalls the cron entries.
UPDATE_JOB_HOUR = 3
UPDATE_JOB_MINUTE = 15

# Cron schedule for the monthly log-truncation job.
CLEAR_LOGS_DAY_OF_MONTH = 1
CLEAR_LOGS_HOUR = 0
CLEAR_LOGS_MINUTE = 0

# Prayers for which an adhan is played, in the order they occur during the day.
PRAYER_NAMES = ('fajr', 'dhuhr', 'asr', 'maghrib', 'isha')

# Default adhan audio file used for each prayer, relative to ROOT_DIR.
DEFAULT_AUDIO_FILES = {
    'fajr': 'Adhan-fajr.mp3',
    'dhuhr': 'Adhan-Madinah.mp3',
    'asr': 'Adhan-Madinah.mp3',
    'maghrib': 'Adhan-Madinah.mp3',
    'isha': 'Adhan-Madinah.mp3',
}

PT = PrayTimes()


# HELPER FUNCTIONS
# ---------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description='Calculate prayer times and install cronjobs to play Adhan')
    parser.add_argument('--lat', type=float, dest='lat',
                         help='Latitude of the location, for example 30.345621')
    parser.add_argument('--lng', type=float, dest='lng',
                         help='Longitude of the location, for example 60.512126')
    parser.add_argument('--method', choices=['MWL', 'ISNA', 'Egypt', 'Makkah', 'Karachi', 'Tehran', 'Jafari'],
                         dest='method',
                         help='Method of calculation')
    parser.add_argument('--fajr-azaan-volume', type=int, dest='fajr_azaan_vol',
                         help='Volume for fajr azaan in millibels, 1500 is loud and -30000 is quiet (default 0)')
    parser.add_argument('--azaan-volume', type=int, dest='azaan_vol',
                         help='Volume for azaan (other than fajr) in millibels, '
                              '1500 is loud and -30000 is quiet (default 0)')
    for prayer in PRAYER_NAMES:
        parser.add_argument('--{}-audio'.format(prayer), dest='{}_audio'.format(prayer),
                             help='Audio file to play for {} (default: {})'.format(
                                 prayer, DEFAULT_AUDIO_FILES[prayer]))
    parser.add_argument('--cron-user', dest='cron_user',
                         help='OS user under which to install the cron jobs (default: current user)')
    parser.add_argument('--dry-run', action='store_true', dest='dry_run',
                         help='Print the cron jobs that would be installed without writing them to crontab')
    return parser


def merge_args(args):
    # load previously saved values, if any
    lat = lng = method = fajr_azaan_vol = azaan_vol = cron_user = None
    audio_files = dict(DEFAULT_AUDIO_FILES)
    try:
        with open(SETTINGS_FILE, 'rt') as f:
            content = f.read().strip()
        fields = [field.strip() for field in content.split(',')]
        # backwards compatible with older .settings files that only stored
        # lat,lng,method,fajr_azaan_vol,azaan_vol
        lat, lng, method, fajr_azaan_vol, azaan_vol = fields[:5]
        if len(fields) > 5 and fields[5]:
            cron_user = fields[5]
        for i, prayer in enumerate(PRAYER_NAMES):
            idx = 6 + i
            if len(fields) > idx and fields[idx]:
                audio_files[prayer] = fields[idx]
    except FileNotFoundError:
        # Expected on first run before any settings have been saved.
        print('No .settings file found')
    except (ValueError, IndexError):
        # Settings file exists but is malformed/corrupt; fall back to
        # whatever was supplied on the command line instead of crashing.
        print('Could not parse .settings file, ignoring its contents')

    # merge args (CLI args take precedence over saved values)
    if args.lat:
        lat = args.lat
    if lat:
        lat = float(lat)
    if args.lng:
        lng = args.lng
    if lng:
        lng = float(lng)
    if args.method:
        method = args.method
    if args.fajr_azaan_vol:
        fajr_azaan_vol = args.fajr_azaan_vol
    if fajr_azaan_vol:
        fajr_azaan_vol = int(fajr_azaan_vol)
    if args.azaan_vol:
        azaan_vol = args.azaan_vol
    if azaan_vol:
        azaan_vol = int(azaan_vol)
    if args.cron_user:
        cron_user = args.cron_user
    if not cron_user:
        cron_user = getpass.getuser()
    for prayer in PRAYER_NAMES:
        cli_value = getattr(args, '{}_audio'.format(prayer))
        if cli_value:
            audio_files[prayer] = cli_value

    # save values
    with open(SETTINGS_FILE, 'wt') as f:
        f.write(','.join(str(v) for v in [
            lat or '', lng or '', method or '', fajr_azaan_vol or 0, azaan_vol or 0,
            cron_user,
        ] + [audio_files[prayer] for prayer in PRAYER_NAMES]))

    return lat or None, lng or None, method or None, fajr_azaan_vol or 0, azaan_vol or 0, cron_user, audio_files


def add_azaan_time(prayer_name, prayer_time, cron, command, comment):
    try:
        hour, minute = prayer_time.split(':')
        hour, minute = int(hour), int(minute)
    except (ValueError, AttributeError):
        raise ValueError(
            "Could not compute a valid time for '{}' (got {!r}). "
            "Check that --lat/--lng/--method are correct for your location."
            .format(prayer_name, prayer_time))
    job = cron.new(command=command, comment=comment)
    job.minute.on(minute)
    job.hour.on(hour)
    print(job)


def add_update_cron_job(cron, command, comment):
    job = cron.new(command=command, comment=comment)
    job.minute.on(UPDATE_JOB_MINUTE)
    job.hour.on(UPDATE_JOB_HOUR)
    print(job)


def add_clear_logs_cron_job(cron, command, comment):
    job = cron.new(command=command, comment=comment)
    job.day.on(CLEAR_LOGS_DAY_OF_MONTH)
    job.minute.on(CLEAR_LOGS_MINUTE)
    job.hour.on(CLEAR_LOGS_HOUR)
    print(job)
# ---------------------------------
# HELPER FUNCTIONS END


def main():
    parser = parse_args()
    args = parser.parse_args()

    lat, lng, method, fajr_azaan_vol, azaan_vol, cron_user, audio_files = merge_args(args)
    print(lat, lng, method, fajr_azaan_vol, azaan_vol, cron_user)

    # Complain if any mandatory value is missing
    if not lat or not lng or not method:
        parser.print_usage()
        sys.exit(1)

    # Set calculation method, utcOffset and dst here
    # By default system timezone will be used
    PT.setMethod(method)
    utc_offset = -(time.timezone / 3600)
    is_dst = time.localtime().tm_isdst
    if is_dst:
        print('Note: Daylight Saving Time is currently in effect; '
              'times will be recalculated automatically at the next scheduled run.')

    now = datetime.datetime.now()

    commands = {}
    for prayer in PRAYER_NAMES:
        vol = fajr_azaan_vol if prayer == 'fajr' else azaan_vol
        commands[prayer] = '{}/playAzaan.sh {}/{} {}'.format(
            ROOT_DIR, ROOT_DIR, audio_files[prayer], vol)
    update_command = '{}/updateAzaanTimers.py >> {}/adhan.log 2>&1'.format(ROOT_DIR, ROOT_DIR)
    clear_logs_command = 'truncate -s 0 {}/adhan.log 2>&1'.format(ROOT_DIR)

    # Calculate prayer times
    times = PT.getTimes((now.year, now.month, now.day), (lat, lng), utc_offset, is_dst)
    for prayer in PRAYER_NAMES:
        print(times[prayer])

    cron = CronTab(user=cron_user)
    # Remove existing jobs created by this script
    cron.remove_all(comment=JOB_COMMENT)

    # Add times to crontab
    for prayer in PRAYER_NAMES:
        add_azaan_time(prayer, times[prayer], cron, commands[prayer], JOB_COMMENT)

    # Run this script again overnight
    add_update_cron_job(cron, update_command, JOB_COMMENT)

    # Clear the logs every month
    add_clear_logs_cron_job(cron, clear_logs_command, JOB_COMMENT)

    if args.dry_run:
        print('Dry run: cron jobs were not written to crontab')
    else:
        cron.write_to_user(user=cron_user)

    print('Script execution finished at: ' + str(now))


if __name__ == '__main__':
    main()
