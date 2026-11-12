# -*- coding: utf-8 -*-
"""The clock across a daylight-saving change (10 Nov 2026, her words: how many
times are we going to have to fix these damn settings on the time). The offset
is worked out from time_zone for each instant, so a date on each side of the
1 Nov 2026 fall-back (and the 14 Mar 2027 spring-forward) reads on its own
clock, and the hand-kept utc_offset_hours is only a fallback. The number in
the settings below is deliberately the WRONG one for half the dates, so any
code still reading it as the truth fails here.

    python3 core/tests/test_clock_change.py
"""
import datetime as dt, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_clock as C  # noqa: E402
import bedo_reader  # noqa: E402
import bedo_entry as E  # noqa: E402
import bedo_split  # noqa: E402
import bedo_forecast  # noqa: E402
import bedo_stretches as ST  # noqa: E402
import bedo_photos as PH  # noqa: E402
import bedo_close  # noqa: E402

UTC = dt.timezone.utc
L = {'time_zone': 'America/Chicago', 'utc_offset_hours': -5}   # the stale summer number, kept on purpose
BEFORE, AFTER = dt.date(2026, 10, 31), dt.date(2026, 11, 2)    # Saturday before, Monday after the change


def u(y, m, d, h, mi=0):
    return dt.datetime(y, m, d, h, mi, tzinfo=UTC)


class Clock(unittest.TestCase):
    def test_each_side_of_the_change_on_its_own_clock(self):
        self.assertEqual(C.offset_hours(L, u(2026, 10, 31, 17)), -5)
        self.assertEqual(C.offset_hours(L, u(2026, 11, 2, 17)), -6)
        self.assertEqual(C.to_local(L, '2026-10-31T17:00:00.000Z'), dt.datetime(2026, 10, 31, 12))
        self.assertEqual(C.to_local(L, '2026-11-02T18:00:00.000Z'), dt.datetime(2026, 11, 2, 12))
        self.assertEqual(C.offset_on(L, BEFORE), -5)
        self.assertEqual(C.offset_on(L, AFTER), -6)

    def test_the_spring_change_too(self):
        self.assertEqual(C.offset_on(L, dt.date(2027, 3, 13)), -6)
        self.assertEqual(C.offset_on(L, dt.date(2027, 3, 15)), -5)

    def test_back_to_utc_on_the_clock_of_the_day(self):
        self.assertEqual(C.to_utc(L, dt.datetime(2026, 10, 31, 12)), u(2026, 10, 31, 17))
        self.assertEqual(C.to_utc(L, dt.datetime(2026, 11, 2, 12)), u(2026, 11, 2, 18))

    def test_the_change_day_is_twenty_five_hours(self):
        a, b = C.day_bounds_utc(L, dt.date(2026, 11, 1))
        self.assertEqual((a, b - a), (u(2026, 11, 1, 5), dt.timedelta(hours=25)))
        a, b = C.day_bounds_utc(L, dt.date(2027, 3, 14))
        self.assertEqual(b - a, dt.timedelta(hours=23))

    def test_a_night_across_the_change_reads_each_end_on_its_own_clock(self):
        off = C.Offset(L)
        bed, wake = u(2026, 11, 1, 4), u(2026, 11, 1, 13)       # 11 PM CDT, 7 AM CST
        self.assertEqual(((bed + off).replace(tzinfo=None), (wake + off).replace(tzinfo=None)),
                         (dt.datetime(2026, 10, 31, 23), dt.datetime(2026, 11, 1, 7)))
        self.assertEqual(dt.datetime(2026, 11, 1, 7) - off, dt.datetime(2026, 11, 1, 13))   # naive in, naive out
        self.assertEqual((dt.datetime(2026, 10, 31, 23, tzinfo=UTC) - off), bed)            # aware in, aware out

    def test_the_number_is_only_the_fallback(self):
        nozone = {'time_zone': 'Nowhere/Atall', 'utc_offset_hours': -6}
        self.assertIsNone(C.zone(nozone))
        self.assertEqual(C.offset_hours(nozone, u(2026, 7, 1, 12)), -6)
        self.assertEqual(C.offset_hours({'utc_offset_hours': -6}, u(2026, 7, 1, 12)), -6)
        self.assertEqual(C.offset_hours(-5, u(2027, 1, 1, 12)), -5)     # a plain number stays a plain number
        self.assertIsNone(C.problem(L))
        self.assertIsNone(C.problem(nozone))
        self.assertIn('time_zone is missing', C.problem({}))

    def test_the_reader_agrees(self):
        self.assertEqual(bedo_reader.offset_hours(L, u(2026, 11, 2, 17)), -6)
        rows = [{'datetime': '2026-11-02T05:30:00.000Z'}]          # 11:30 PM Sunday, CST
        self.assertEqual(bedo_reader.on_day(rows, dt.date(2026, 11, 1), L), rows)

    def test_iso_offset(self):
        self.assertEqual((C.iso_offset(-5), C.iso_offset(-6), C.iso_offset(5.5)), ('-05:00', '-06:00', '+05:30'))


class Core(unittest.TestCase):
    def test_the_weekly_base_by_the_rows_own_clock(self):
        # 11:30 PM Saturday 7 Nov, CST: still the week that opened 1 Nov. The stale -5 put it on Sunday 8 Nov.
        w = E.base_for('2026-11-08T05:30:00.000Z', L)
        self.assertEqual(w, E.base_for('2026-11-07T18:00:00.000Z', L))
        self.assertNotEqual(w, E.base_for('2026-11-08T05:30:00.000Z', -5))

    def test_a_span_on_one_day_after_the_change(self):
        row = dict(datetime='2026-11-03T04:00:00.000Z', end='2026-11-03T05:30:00.000Z', practice='📖 read')
        self.assertEqual(E.span_problems(row, L), [])                 # 10:00–11:30 PM Monday, CST
        self.assertTrue(E.span_problems(row, -5))                     # the stale number crossed midnight

    def test_the_split_and_the_forecast_on_the_days_clock(self):
        s = '2026-11-08T05:30:00.000Z'                                # 11:30 PM Sat 7 Nov, CST
        self.assertEqual(bedo_split.local_date(s, L), dt.date(2026, 11, 7))
        self.assertEqual(bedo_split.local_date('2026-10-31T04:30:00.000Z', L), dt.date(2026, 10, 30))
        fc = dict(practice=bedo_forecast.FC['practices'][0], title='a guess', target=s)
        self.assertTrue(bedo_forecast.is_forecast(fc))
        self.assertFalse(bedo_forecast.ahead(fc, dt.date(2026, 11, 8), L))     # its day is Saturday: no ride
        self.assertTrue(bedo_forecast.ahead(fc, dt.date(2026, 11, 8), -5))     # the stale number put it on Sunday

    def test_stretches_name_each_on_its_own_clock(self):
        spans = [(u(2026, 10, 31, 14), u(2026, 10, 31, 15)), (u(2026, 11, 2, 14), u(2026, 11, 2, 15))]
        self.assertTrue(ST.named(spans, L).startswith('9:00–10:00 · 8:00–9:00'))
        self.assertEqual(ST.on_day(spans, AFTER, L), spans[1:])

    def test_a_photo_takes_the_offset_of_its_instant(self):
        self.assertEqual(PH.taken('PXL_20261031_170000000.jpg', L), dt.datetime(2026, 10, 31, 12))
        self.assertEqual(PH.taken('PXL_20261102_180000000.jpg', L), dt.datetime(2026, 11, 2, 12))

    def test_the_close_reads_the_session_on_the_zone(self):
        entry = dict(datetime='2026-11-02T15:00:00.000Z', time_spent=600,
                     details='[be•do] stretches: 9:00–9:10 = 10m')
        self.assertIsNone(bedo_close.stretches_qa(entry, L))


if __name__ == '__main__':
    unittest.main()
