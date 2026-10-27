# -*- coding: utf-8 -*-
"""The October amendments that were rules on paper, now checks: the entry
check's bucket, open-action device, being and doing, appointment, weather and
in-the-moment rules. Every row and name is invented; the shapes are the base's.

    python3 plugins/bedo/core/tests/test_amendments_oct.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_calendar as CA  # noqa: E402
import bedo_dayqa as Q  # noqa: E402
import bedo_dusk_audit as D  # noqa: E402
import bedo_entry as E  # noqa: E402
import bedo_fill as FL  # noqa: E402
import bedo_forecast as FC  # noqa: E402
import bedo_inbox as IB  # noqa: E402
import bedo_preflight as P  # noqa: E402
import bedo_split as S  # noqa: E402
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
        out = probs(row(practice='🎥 movie', title='a shark film, with popcorn', wellness='🩷 heart', person='a pal'))
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
        r = row(practice='💆 massage', title='massage, Thursday 2 pm', status=INT, device=None,
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
    """23 and 27 Oct 2026: synergy or competition is read from what she says about
    it; asked in the moment only when her words don't say, never a day late."""

    def pair(self, words=''):
        video = row(practice='📼 video', title='a talk', datetime=z(16), end=z(16, 30), key='261026_1600')
        hips = row(practice='🧎‍♀️ hip exercises', title='hips', datetime=z(16, 5), end=z(16, 15), details=words)
        return video, hips

    def test_her_words_decide_it(self):
        video, hips = self.pair('the talk made the time fly')
        n = [x for x in E.notes(hips, ctx(day_rows=[video, hips])) if 'two things' in x]
        self.assertEqual(len(n), 1)
        self.assertIn('her words say synergizing', n[0])
        self.assertIn('overlap — synergizing with 261026_1600', n[0])
        self.assertNotIn('?', n[0])                                         # never asked when her words say
        video, hips = self.pair("couldn't focus on either")
        self.assertIn('her words say competing', E.notes(hips, ctx(day_rows=[video, hips]))[-1])
        self.assertEqual(E.synergy_from('loved doing it, though so distracted')[0], 'both')

    def test_asked_right_then_only_when_her_words_dont_say(self):
        video, hips = self.pair()
        n = [x for x in E.notes(hips, ctx(day_rows=[video, hips])) if 'two things' in x]
        self.assertTrue(n and 'ask in this reply, once' in n[0] and 'never ask it later' in n[0], n)

    def test_already_noted_or_alone_says_nothing(self):
        video, hips = self.pair('hips\noverlap — synergizing with 261026_1600')
        self.assertFalse([x for x in E.notes(hips, ctx(day_rows=[video, hips])) if 'two things' in x])
        _, alone = self.pair()
        self.assertFalse([x for x in E.notes(alone, ctx(day_rows=[alone])) if 'two things' in x])

    def test_the_qa_never_asks_a_day_late(self):
        video, hips = self.pair()
        out = Q.synergy([dict(video, id='v'), dict(hips, id='h')], -5)
        self.assertEqual([i['kind'] for i in out], ['count'])


class FamilyIsHeart(unittest.TestCase):
    """19 Oct 2026, rule 3: a stretch with family that nothing else names is heart."""

    def test_the_stretch_takes_heart_and_the_people(self):
        loc = {'people': {'self': '♋ Me', 'kid': '♑ Kid'}}
        rows = [row(practice='😶 wake', datetime=z(7), status=DONE, id='w'),
                row(practice='☕ coffee', datetime=z(7, 5), end=z(7, 20), status=DONE, id='c'),
                row(practice='✨ glimmer', title='he laughed at the ducks', datetime=z(9, 30), person='♑ Kid',
                    wellness=None, id='g'),
                row(practice='🍽️ lunch', datetime=z(11), end=z(11, 30), status=DONE, id='l')]
        fills = [i for i in Q.gaps(rows, -5, (), FL.Context(local=loc)) if i['kind'] == 'fill']
        self.assertEqual(len(fills), 1, fills)
        self.assertEqual((fills[0]['new']['wellness'], fills[0]['new']['person']), ('🩷 heart', '♑ Kid'))


CAL_LOCAL = {'calendar': {'calendars': {'mine': 'me@example.com', 'Kid': 'kid@example.com',
                                        'dropped': 'drop@example.com'},
                          'work_parents': ['Work mission'], 'work_words': ['University']}}


class Calendar(unittest.TestCase):
    """6 Oct 2026: every calendar write names the calendar and is read back.
    9 Oct 2026: every work event is purple."""

    def ev(self, **kw):
        return dict({'summary': 'piano lesson', 'startTime': '2026-10-29T16:00:00',
                     'endTime': '2026-10-29T17:00:00', 'calendarId': 'kid@example.com'}, **kw)

    def test_the_calendar_is_named_never_the_default(self):
        out, _ = CA.problems(self.ev(calendarId=None), CAL_LOCAL)
        self.assertTrue(any('name it' in p and 'never the tool default' in p for p in out))
        out, _ = CA.problems(self.ev(calendarId='stray@example.org'), CAL_LOCAL)
        self.assertTrue(any('not one of hers' in p for p in out))
        self.assertEqual(CA.problems(self.ev(), CAL_LOCAL)[0], [])

    def test_it_is_not_done_until_read_back_there(self):
        out, nxt = CA.problems(self.ev(), CAL_LOCAL)
        self.assertIn('read it back from Kid', nxt)
        found = {'events': [{'id': 'e1', 'summary': 'Piano lesson'}]}
        self.assertEqual(CA.problems(self.ev(), CAL_LOCAL, found, 'kid@example.com'), ([], None))
        out, _ = CA.problems(self.ev(), CAL_LOCAL, {'events': []}, 'kid@example.com')
        self.assertTrue(any('did not come back' in p and 'not done' in p for p in out))
        out, _ = CA.problems(self.ev(), CAL_LOCAL, found, 'me@example.com')
        self.assertTrue(any('not the calendar it was written to' in p for p in out))

    def test_work_is_purple(self):
        parents = {'River data': 'Water work', 'Water work': 'Work mission'}
        work = self.ev(summary='quarterly data review', calendarId='me@example.com', drive='River data')
        out, _ = CA.problems(work, CAL_LOCAL, parents=parents)
        self.assertTrue(any('purple — colorId 3' in p for p in out))         # two levels down still counts
        self.assertEqual(CA.problems(dict(work, colorId='3'), CAL_LOCAL, parents=parents)[0], [])
        out, _ = CA.problems(self.ev(summary='University seminar', calendarId='me@example.com',
                                     recurrenceData=['RRULE:FREQ=WEEKLY']), CAL_LOCAL)
        self.assertTrue(any('on the series' in p for p in out))
        self.assertEqual(CA.problems(self.ev(), CAL_LOCAL)[0], [])            # a piano lesson is not work


INBOX = {'keep_from': {'Pat': ['pat@example.com']},
         'archive_unless': [{'name': 'The Club', 'from': ['example.org'], 'keep_words': ['data center']}]}


def thread(i, sender, subj, snip=''):
    return {'id': i, 'messages': [{'sender': sender, 'subject': subj, 'snippet': snip}]}


class Inbox(unittest.TestCase):
    """22, 25 and 26 Oct 2026: the keeps, the archive rule and the nudge."""

    def test_her_person_is_an_automatic_keep_and_never_archived(self):
        ts = [thread('t1', 'Pat <Pat@example.com>', 'dinner?'), thread('t2', 'shop@example.com', 'sale')]
        res = IB.check({'threads': ts}.get('threads'), INBOX, planned=['t1', 't2'])
        self.assertEqual([k[0] for k in res['keeps']], ['t1'])
        self.assertTrue(res['fixes'] and 'take it out' in res['fixes'][0])
        self.assertEqual(IB.check(ts, INBOX, planned=['t2'])['fixes'], [])

    def test_the_club_is_archived_unless_about_data_centers(self):
        ts = [thread('c1', 'news@example.org', 'Fall drive: give today'),
              thread('c2', 'action@example.org', 'Hearing on the new data center')]
        res = IB.check(ts, INBOX)
        self.assertEqual([a[0] for a in res['archives']], ['c1'])
        self.assertEqual([k[0] for k in res['keeps']], ['c2'])

    def test_she_gets_the_nudge_before_anything_is_archived(self):
        res = IB.check([thread('c1', 'news@example.org', 'Fall drive')], INBOX, planned=['c1', 'x2', 'x3'])
        self.assertIn('give your inbox a quick look before I archive the rest — 3 thread(s)', res['nudge'])
        text = IB.render(res, 1)
        self.assertTrue(text.endswith('archive only on her go'))
        self.assertIsNone(IB.check([], INBOX)['nudge'])                       # nothing to archive, nothing to say


class Forecasts(unittest.TestCase):
    """20 Oct 2026: every look behind lists the forecasts due in its window."""

    def f(self, target, **kw):
        return dict({'practice': '💡 insight', 'title': 'forecast: the CO2 map is ready', 'target': target}, **kw)

    def test_due_in_a_window(self):
        a = dt.datetime(2027, 1, 29, 5, tzinfo=dt.timezone.utc)
        rows = [self.f('2027-01-29T23:00:00.000Z'), self.f('2027-02-02T23:00:00.000Z'),
                self.f('2027-01-29T23:00:00.000Z', title='lunch'), {'practice': '🔭 forecast', 'title': 'snow',
                                                                    'target': '2027-01-29T12:00:00.000Z'}]
        self.assertEqual([r['title'] for r in FC.due_in(rows, a, a + dt.timedelta(days=1))],
                         ['snow', 'forecast: the CO2 map is ready'])

    def test_the_split_carries_a_forecast_not_yet_due(self):
        def rec(rid, **c):
            return {'id': rid, 'createdTime': '2026-10-20T12:00:00.000Z', 'cellValuesByFieldId': c}
        fields = {k: k for k in ('key', 'status', 'datetime', 'practice', 'title', 'target')}
        old = [rec('f1', status=LOG, practice='💡 insight', datetime='2026-10-21T00:48:00.000Z',
                   title='forecast: LA CO2 — a map for January', target='2027-01-29T23:00:00.000Z'),
               rec('f2', status=LOG, practice='💡 insight', datetime='2026-10-21T00:48:00.000Z',
                   title='forecast: the fence is up', target='2026-10-23T23:00:00.000Z'),
               rec('g1', status=LOG, practice='📝 log', datetime='2026-10-21T00:48:00.000Z', title='a note')]
        dump = {'records': old, 'metadata': {'totalRecordCount': 3}}
        p = S.plan(dump, dump, [], fields, dt.date(2026, 10, 25), -5, '2026-10-25T00:00:00.000Z')
        self.assertEqual(p['carry_forecasts'], ['f1'])
        self.assertEqual(sorted(p['delete_ids']), ['f2', 'g1'])               # one already due stays behind


class DuskPhotos(unittest.TestCase):
    """20 Oct 2026: photos are imported at the dusk close."""

    def test_no_folder_read_is_said_never_skipped(self):
        res = D.audit([], NOW, -5, day=DAY)
        self.assertTrue(res['findings']['photo_import'])
        self.assertIn('photos — imported at the dusk close', D.render(res, 'dusk'))
        self.assertEqual(D.audit([], NOW, -5, day=DAY, photo_files=[])['findings']['photo_import'], [])


class Schedule(unittest.TestCase):
    """20 Oct 2026: every skill has a set time, and preflight names what is due."""

    def test_what_is_due_by_the_clock(self):
        tue = dt.datetime(2026, 10, 27, 8, 0)
        self.assertIn('look ahead', P.due(tue))
        self.assertNotIn('dusk --photos', P.due(tue))
        self.assertIn('dusk --photos', P.due(tue.replace(hour=20)))
        self.assertIn('weekly close', P.due(dt.datetime(2026, 11, 1, 9)))       # Sunday
        self.assertIn('ahead review', P.due(dt.datetime(2026, 11, 3, 9)))       # by the 5th
        self.assertIsNone(P.due(tue.replace(hour=14)))


if __name__ == '__main__':
    unittest.main()
