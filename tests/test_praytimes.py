import sys
from datetime import date
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(abspath(__file__))))

from praytimes import PrayTimes  # noqa: E402


def test_get_times_returns_all_expected_keys():
    pt = PrayTimes('ISNA')
    times = pt.getTimes((2024, 1, 1), (43, -80), -5)
    for key in ('imsak', 'fajr', 'sunrise', 'dhuhr', 'asr', 'sunset', 'maghrib', 'isha', 'midnight'):
        assert key in times


def test_get_times_known_values_waterloo():
    # Regression test using a fixed date/location so the calculation logic
    # doesn't silently change.
    pt = PrayTimes('ISNA')
    times = pt.getTimes((2011, 2, 9), (43, -80), -5)
    assert times['sunrise'] == '07:26'


def test_set_method_changes_calc_method():
    pt = PrayTimes('MWL')
    assert pt.getMethod() == 'MWL'
    pt.setMethod('ISNA')
    assert pt.getMethod() == 'ISNA'


def test_invalid_method_falls_back_to_mwl():
    pt = PrayTimes('NotAMethod')
    assert pt.getMethod() == 'MWL'


def test_get_times_accepts_date_object():
    pt = PrayTimes('ISNA')
    times = pt.getTimes(date(2024, 6, 1), (43, -80), -5)
    assert times['dhuhr'] != pt.invalidTime
