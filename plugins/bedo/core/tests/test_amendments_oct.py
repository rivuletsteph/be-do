# -*- coding: utf-8 -*-
"""The October amendments that were rules on paper, now checks: the entry
check's bucket, open-action device, being and doing, appointment, weather and
in-the-moment rules. Every row and name is invented; the shapes are the base's.

    python3 plugins/bedo/core/tests/test_amendments_oct.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_entry as E  # noqa: E402
import bedo_fill as FL  # noqa: E402
from bedo_reader import FACTS as F  # noqa: E402

LOG, DONE, INT, POT, SKIP = '● log', '◉ done', '⬜ intention', '▫️potential', '⨂ skipped'
DAY = dt.date(2026, 10, 26)
LOCAL = {'system_rhythm': 'the system', 'stories_rhythm': 'Stories'}
NOW = dt.datetime(2026, 10, 26, 15, tzinfo=dt.timezone.utc)


def z(h, m=0, day=DAY):
    return (dt.datetime.combine(day, dt.time(h, m)) + dt.timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M:00.000Z')


def row(**kw):
    r = {'datetime': z(9), 'status': LOG, 'practice': '📝 log', 'title': 'a note', 'device': '📱 phone',
         'wellness': '🧠 mind'}
    r.update(kw)
    return r


def ctx(**kw):
    return FL.Context(local=LOCAL, **kw)


def probs(r, c=None):
    return E.problems(r, fill=c or ctx(), now=NOW)


class Bucket(unittest.TestCase):
    """20 Oct 2026: every row sits in a flow, or under a rhythm or a drive."""

    def test_a_story_goes_under_the_stories_rhythm(self):
        out = probs(row(practice='🎥 movie', title='Jaws, with popcorn', wellness='🩷 heart', person='a friend'))
        self.assertTrue(any('rhythm: empty — deduced Stories' in p for p in out), out)

    def test_a_window_chat_and_its_captures_sit_under_the_system_drive(self):
        for r in (row(practice='⚡ action', title='▶️1026 🌕 Mon my day', status='✅ done', key='261026_0700'),
                  row(practice='📲 capture', title='capture')):
            self.assertTrue(any('deduced the system' in p for p in probs(r)), r)

    def test_a_flow_practice_carries_no_rhythm(self):
        self.assertFalse([p for p in probs(row(practice='☕ coffee', status=DONE)) if 'rhythm' in p])
        c = ctx(flows={'🫖 evening tea'})
        self.assertFalse([p for p in probs(row(practice='🫖 evening tea', status=DONE), c) if 'rhythm' in p])
        self.assertFalse([p for p in probs(row(practice='🌙 evening meditation', status=DONE), c)
                          if 'rhythm' in p])                               # one of an either-or pair is a flow step

    def test_nothing_deduces_it_so_it_is_asked_in_passing(self):
        r = row(practice='🧺 laundry', title='folded towels')
        self.assertFalse([p for p in probs(r) if 'rhythm' in p])          # never a refusal
        self.assertTrue(any('which rhythm or drive' in n for n in E.notes(r, ctx())))

    def test_her_usual_answers_first(self):
        c = ctx(history=[row(practice='🧺 laundry', rhythm='Home')] * 2)
        self.assertTrue(any('deduced Home' in p for p in probs(row(practice='🧺 laundry'), c)))

    def test_a_plan_or_a_tagged_row_needs_nothing(self):
        self.assertFalse([p for p in probs(row(practice='🧺 laundry', status=INT, device=None)) if 'rhythm' in p])
        self.assertFalse([p for p in probs(row(practice='🎥 movie', rhythm='Stories', wellness='🩷 heart'))
                          if 'rhythm' in p])


class OpenDevice(unittest.TestCase):
    """8 Oct 2026: every open action gets a device when it's written."""

    def act(self, title, **kw):
        return dict(row(practice='⚡ action', status=INT, title=title, key='261026_0900', device=None), **kw)

    def test_the_device_it_will_be_done_on_is_deduced(self):
        self.assertTrue(any('deduced 💻 laptop' in p for p in probs(self.act('draft the report on the laptop'))))
        self.assertTrue(any('deduced 📱 phone' in p for p in probs(self.act('call the vet about Rosa'))))
        self.assertTrue(any('deduced 📱 phone' in p for p in probs(self.act('pick the paint', quickie=True))))

    def test_else_asked_in_passing(self):
        r = self.act('sort the garage shelves')
        self.assertFalse([p for p in probs(r) if p.startswith('device')])
        self.assertTrue(any('laptop or phone' in n for n in E.notes(r, ctx())))

    def test_a_plan_that_is_not_an_action_still_carries_none(self):
        r = row(practice='🔅 morning sun', status=INT, device=None)
        self.assertFalse([p for p in probs(r) if p.startswith('device')])
        self.assertFalse([n for n in E.notes(r, ctx()) if 'laptop or phone' in n])


class BeingDoing(unittest.TestCase):
    """24 Oct 2026: work on a drive takes its element; a show on the couch is being."""

    def test_work_on_a_drive_is_never_mind_by_default(self):
        c = ctx(drives={'GLO2': '💨 air'})
        r = row(practice='⚡ action', status='✅ done', key='261026_1000', rhythm='GLO2', title='progress report')
        self.assertTrue(any('takes its element 💨 air' in p for p in probs(r, c)))
        self.assertFalse([p for p in probs(dict(r, wellness='💨 air'), c) if 'element' in p])

    def test_passive_rest_is_never_a_doing_element(self):
        r = row(practice='📺 show', title='two episodes', wellness='🔥 fire', rhythm='Stories')
        self.assertTrue(any('passive rest is being' in p for p in probs(r)))

    def test_the_fill_gives_a_show_heart_with_people_never_fire(self):
        c = ctx(catalog={'📺 show': '🔥 fire'})
        got, ask = FL.deduce(row(practice='📺 show', wellness=None, person='Pat'), c)
        self.assertEqual(got['wellness'][0], '🩷 heart')
        got, ask = FL.deduce(row(practice='📺 show', wellness=None), c)
        self.assertNotIn('wellness', got)                                  # alone: hers to say
        self.assertIn('wellness', ask)


class Appointment(unittest.TestCase):
    """6 Oct 2026: an appointment she shares goes on her calendar."""

    def test_an_appointment_ahead_needs_its_event(self):
        r = row(practice='💆 massage', title='massage with Jodi, Thursday 2 pm', status=INT, device=None,
                datetime=z(14, day=DAY + dt.timedelta(days=3)))
        self.assertTrue(any('goes on her calendar' in p for p in probs(r)))
        self.assertFalse([p for p in probs(dict(r, calendar_event='https://calendar/x')) if 'calendar' in p])

    def test_a_calendar_event_row_always_carries_its_link(self):
        r = row(practice='🗓️ calendar event', title='school play', status=DONE)
        self.assertTrue(any('goes on her calendar' in p for p in probs(r)))

    def test_a_to_do_to_book_one_and_a_past_one_are_not(self):
        book = row(practice='⚡ action', status=INT, key='261026_1100', title='book a dentist appointment',
                   device='📱 phone')
        self.assertFalse([p for p in probs(book) if 'calendar' in p])
        past = row(practice='📝 log', title='the massage was lovely', datetime=z(9))
        self.assertFalse([p for p in probs(past) if 'calendar' in p])


class Weather(unittest.TestCase):
    """26 Oct 2026: when weather takes away direct sun, a sun practice is 🌥️ weather."""

    def test_a_cloudy_sun_is_never_skipped(self):
        r = row(practice='🔅 morning sun', status=SKIP, details='clouds came in before I got out', device='🚫 none')
        out = probs(r)
        self.assertTrue(any('that is 🌥️ weather' in p for p in out), out)

    def test_until_the_base_carries_the_choice_the_row_is_held(self):
        r = row(practice='🔅 morning sun', status=F['weather_status']['status'], device='🚫 none')
        out = probs(r)
        self.assertEqual(F['weather_status']['in_base'], False)
        self.assertTrue(any('hold this row' in p for p in out), out)
        self.assertFalse([p for p in out if 'eight choices' in p])

    def test_weather_is_only_for_a_sun_practice(self):
        r = row(practice='☕ coffee', status=F['weather_status']['status'])
        self.assertTrue(any('for a sun practice' in p for p in probs(r)))

    def test_a_plain_skip_stays_a_skip(self):
        self.assertFalse([p for p in probs(row(practice='🔅 morning sun', status=SKIP, device='🚫 none'))
                          if 'weather' in p])


class InTheMoment(unittest.TestCase):
    """23 Oct 2026: the synergy-or-competing question is asked as she logs it."""

    def test_two_things_at_once_are_asked_about_now(self):
        video = row(practice='📼 video', title='a talk', datetime=z(16), end=z(16, 30), key='261026_1600')
        hips = row(practice='🧎‍♀️ hip exercises', title='hips', datetime=z(16, 5), end=z(16, 15))
        n = E.notes(hips, ctx(day_rows=[video, hips]))
        self.assertTrue(any('two things at once with “a talk”' in x and 'help each other' in x for x in n), n)
        self.assertTrue(any('overlap — <answer> with 261026_1600' in x for x in n))

    def test_already_answered_or_alone_is_not_asked(self):
        video = row(practice='📼 video', title='a talk', datetime=z(16), end=z(16, 30))
        hips = row(practice='🧎‍♀️ hip exercises', datetime=z(16, 5), end=z(16, 15),
                   details='so much synergy there')
        self.assertFalse([x for x in E.notes(hips, ctx(day_rows=[video, hips])) if 'two things' in x])
        alone = dict(hips, details='')
        self.assertFalse([x for x in E.notes(alone, ctx(day_rows=[alone])) if 'two things' in x])


if __name__ == '__main__':
    unittest.main()
