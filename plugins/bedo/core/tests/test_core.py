# -*- coding: utf-8 -*-
"""The core's invariants, each tested against the way it actually broke.

Every row here is invented; the shapes are the base's.

    python3 plugins/bedo/core/tests/test_core.py
"""
import datetime as dt, json, os, sys, tempfile, unittest
from unittest import mock

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_reader as R  # noqa: E402
import bedo_entry as E  # noqa: E402
import bedo_split as S  # noqa: E402
import bedo_export as X  # noqa: E402

F = R.FACTS
INT, MOT, DONE, DROP = '⬜ intention', '▶️ in motion', '✅ done', '✖️ dropped'
LOG = '● log'
ACTION = F['practice']['action']
FIELDS = {k: k for k in ('key', 'status', 'datetime', 'practice', 'title')}


def rec(rid, created, **c):
    return {'id': rid, 'createdTime': created, 'cellValuesByFieldId': c}


def dump(*recs, total=None):
    return {'records': list(recs), 'metadata': {'totalRecordCount': len(recs) if total is None else total}}


def dies(fn, *a, **k):
    try:
        fn(*a, **k)
    except SystemExit as e:
        return str(e)
    raise AssertionError('expected the run to stop')


class Facts(unittest.TestCase):
    def test_strings_hold_their_shape(self):
        self.assertEqual(len(F['status']['logs'] + F['status']['actions']), 8)
        pot = F['status']['actions'][0]
        self.assertEqual([hex(ord(c)) for c in pot[:2]], ['0x25ab', '0xfe0f'])
        self.assertEqual(pot[2:], 'potential')                       # the one glyph with no space
        self.assertTrue(all(e == e.lower() for e in F['emotion']))
        self.assertEqual(len(F['wellness']['be'] + F['wellness']['do']), 8)
        self.assertIn('💨 air', F['wellness']['do'])
        self.assertEqual(F['divider'], '—' * 3)

    def test_week_number_is_derived(self):
        self.assertEqual(E.week_number(dt.date(2026, 5, 3)), 19)
        self.assertEqual(E.week_number(dt.date(2026, 10, 4)), 41)
        self.assertEqual(E.week_number(dt.date(2026, 10, 3)), 40)


class Reader(unittest.TestCase):
    def test_I11_a_short_read_stops(self):
        d = dump(rec('r1', '2026-10-01T10:00:00.000Z'), total=2)
        self.assertIn('I11', dies(R.complete, d))
        self.assertIn('I11', dies(R.complete, {'records': []}))      # no count is no proof
        self.assertEqual(len(R.complete(dump(rec('r1', 'x')))), 1)

    def test_I11_a_wrapped_chat_dump_reads(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, 'w.json')
            with open(p, 'w') as fh:
                json.dump([{'text': json.dumps(dump(rec('r1', 'x')))}], fh)
            self.assertEqual(R.complete(p)[0]['id'], 'r1')

    def test_I15_live_copy_wins(self):
        live = dump(rec('r1', '2026-10-01T10:00:00.000Z', key='261001_1000', status=DONE))
        arch = dump(rec('r1', '2026-10-01T10:00:00.000Z', key='261001_1000', status=INT))
        recs, reads = R.merge_live_first([live, arch])
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]['cellValuesByFieldId']['status'], DONE)
        # the check V52 names: the live base alone and all bases agree
        alone, _ = R.merge_live_first([live])
        self.assertEqual(len(alone), len(recs))

    def test_I5_a_log_in_the_same_minute_is_not_the_head(self):
        # the W39 split: an open action, then a capture logged in the same minute
        rows = [
            {'id': 'a', 'key': '260905_0742', 'status': INT, 'created': '2026-09-05T12:42:00Z'},
            {'id': 'b', 'key': '260905_0742', 'status': LOG, 'created': '2026-09-05T12:43:00Z'},
        ]
        chains, heads = R.resolve(rows, lambda r: r['key'], lambda r: r['status'],
                                  lambda r: r['created'], lambda r: r['id'])
        self.assertEqual(heads['260905_0742']['id'], 'a')
        self.assertIn('b', heads)                                    # the log is its own row
        self.assertEqual(len(chains['260905_0742']), 1)

    def test_I5_latest_action_row_wins(self):
        rows = [{'id': 'a', 'key': 'k', 'status': INT, 'created': '1'},
                {'id': 'b', 'key': 'k', 'status': DONE, 'created': '2'}]
        _, heads = R.resolve(rows, lambda r: r['key'], lambda r: r['status'],
                             lambda r: r['created'], lambda r: r['id'])
        self.assertEqual(heads['k']['id'], 'b')

    def test_stream_rows_in_one_call(self):
        live = dump(rec('r2', '2', key='k', status=DONE, practice=ACTION),
                    rec('r1', '1', key='k', status=INT, practice=ACTION))
        rows, chains, latest, reads = R.stream_rows([live], FIELDS)
        self.assertEqual(latest['k']['id'], 'r2')
        self.assertEqual(reads[0][1], 2)


def good_row(**over):
    row = {'datetime': '2026-10-05T14:00:00.000Z', 'status': INT, 'practice': ACTION,
           'key': '261005_0900', 'wellness': '💨 air', 'device': '💻 laptop', 'details': 'my words\n' + F['divider'] + '\n[be•do] a note'}
    row.update(over)
    return row


class Entry(unittest.TestCase):
    def test_a_good_row_passes(self):
        self.assertEqual(E.problems(good_row()), [])
        self.assertEqual(E.problems(good_row(details='[be•do] only be•do')), [])

    def test_only_action_rows_carry_a_key(self):
        p = E.problems(good_row(practice='📲 capture', status=LOG))
        self.assertTrue(any(m.startswith('key: only') for m in p))
        p = E.problems(good_row(key=''))
        self.assertTrue(any('needs its key' in m for m in p))
        p = E.problems(good_row(key='26105_900'))
        self.assertTrue(any('YYMMDD_HHMM' in m for m in p))
        self.assertEqual(E.problems(good_row(key='261005_0900b')), [])

    def test_I4_full_choices_only(self):
        self.assertTrue(E.problems(good_row(status='⬜')))
        self.assertTrue(E.problems(good_row(wellness='💨 Air')))
        self.assertTrue(E.problems(good_row(emotion=['🟡'])))
        self.assertTrue(E.problems(good_row(attention='🌕')))

    def test_one_divider_of_em_dashes(self):
        self.assertTrue(any('three em dashes' in m for m in
                            E.problems(good_row(details='mine\n---\n[be•do] x'))))
        two = 'mine\n' + F['divider'] + '\nmore\n' + F['divider'] + '\n[be•do] x'
        self.assertTrue(any('one divider' in m for m in E.problems(good_row(details=two))))
        self.assertTrue(any('need the divider' in m for m in
                            E.problems(good_row(details='mine\n[be•do] x'))))

    def test_spans(self):
        self.assertTrue(any('never both' in m for m in
                            E.problems(good_row(end='2026-10-05T15:00:00.000Z', time_spent=600))))
        self.assertTrue(any('before the start' in m for m in
                            E.problems(good_row(end='2026-10-05T13:00:00.000Z'))))
        self.assertTrue(any('I12' in m for m in E.problems(good_row(datetime='2026-10-05T09:00:00'))))

    def test_gratitude_is_bulleted_and_a_milestone_names_its_drive(self):
        g = dict(practice='🙏 gratitude', status='◉ done', key='')
        self.assertTrue(any(m.startswith('gratitude') for m in E.problems(good_row(details='the sun and the dog', **g))))
        bullets = '\n'.join(['• the sun', '• the dog', F['divider'], '[be•do] x'])
        self.assertEqual(E.problems(good_row(details=bullets, **g)), [])
        m = dict(practice='🪨 milestone', status=LOG, key='')
        self.assertTrue(any(x.startswith('milestone') for x in E.problems(good_row(**m))))
        self.assertEqual(E.problems(good_row(rhythm='a drive', **m)), [])

    def test_a_new_day_needs_its_own_chat(self):
        wed = dt.date(2026, 10, 7)
        woke = good_row(practice=F['flows']['wake'], status='◉ done', key='',
                        datetime='2026-10-08T12:17:00.000Z')         # Thu 7:17 local
        self.assertTrue(any(m.startswith('new day') for m in E.problems(woke, utc_offset_hours=-5, chat_day=wed)))
        late = good_row(datetime='2026-10-08T04:30:00.000Z')            # Wed 11:30 pm local
        self.assertEqual(E.problems(late, utc_offset_hours=-5, chat_day=wed), [])
        after_midnight = good_row(datetime='2026-10-08T06:30:00.000Z')  # Thu 1:30 am, dusk running late
        self.assertEqual(E.problems(after_midnight, utc_offset_hours=-5, chat_day=wed), [])
        noon = good_row(datetime='2026-10-08T17:30:00.000Z')            # Thu 12:30 pm
        self.assertTrue(any(m.startswith('new day') for m in E.problems(noon, utc_offset_hours=-5, chat_day=wed)))
        self.assertEqual(E.problems(woke, utc_offset_hours=-5), [])      # no chat day given: no check

    def test_a_row_goes_in_its_own_weeks_base(self):
        # Sunday 4 Oct, 10 PM local, is W41 — not the base that happens to be open
        late_sunday = good_row(datetime='2026-10-05T03:00:00.000Z', key='261004_2200')
        self.assertEqual(E.base_for(late_sunday['datetime'], -5), 'w41 be•do')
        p = E.problems(late_sunday, base_name='w40 be•do', utc_offset_hours=-5)
        self.assertTrue(any(m.startswith('base:') for m in p))
        self.assertEqual(E.problems(late_sunday, base_name='w41 be•do', utc_offset_hours=-5), [])


def split_fixture():
    """w41 is a clone of w40; w39 is an archive. Sunday 4 Oct opens W41."""
    C = '2026-10-04T15:00:00.000Z'                                       # the clone
    w40 = [
        rec('o1', '2026-09-28T13:00:00.000Z', key='260928_0800', status=INT, practice=ACTION,
            datetime='2026-09-28T13:00:00.000Z', title='open intention'),
        # a capture in the same minute, written later — it must not close the chain
        rec('l1', '2026-09-28T13:00:30.000Z', key='260928_0800', status=LOG, practice='📲 capture',
            datetime='2026-09-28T13:00:00.000Z'),
        rec('d1', '2026-09-29T13:00:00.000Z', key='260929_0800', status=INT, practice=ACTION,
            datetime='2026-09-29T13:00:00.000Z'),
        rec('d2', '2026-09-29T18:00:00.000Z', key='260929_0800', status=DONE, practice=ACTION,
            datetime='2026-09-29T13:00:00.000Z'),
        rec('g1', '2026-10-01T13:00:00.000Z', status=LOG, practice='📝 log', datetime='2026-10-01T13:00:00.000Z'),
        # last night's sleep, written this morning, dated Saturday: a date rule would keep it wrongly
        rec('s1', '2026-10-04T12:00:00.000Z', status=LOG, practice='😴 sleep', datetime='2026-10-04T03:30:00.000Z'),
        # written Sunday morning in the new week
        rec('n1', '2026-10-04T13:00:00.000Z', status=LOG, practice='📝 log', datetime='2026-10-04T13:00:00.000Z'),
    ]
    w39 = [
        # an open head that lives only in the archive — the kind the W39 split dropped
        rec('x1', '2026-09-05T12:42:00.000Z', key='260905_0742', status=INT, practice=ACTION,
            datetime='2026-09-05T12:42:00.000Z'),
        rec('m1', '2026-09-06T12:00:00.000Z', key='260906_0700', status=INT, practice='📼 video',
            datetime='2026-09-06T12:00:00.000Z'),
    ]
    return dump(*w40), dump(*w40), dump(*w39), C


class Split(unittest.TestCase):
    def test_I16_delete_set_by_id(self):
        w41, w40, w39, clone = split_fixture()
        p = S.plan(w41, w40, [w39], FIELDS, dt.date(2026, 10, 4), -5, clone)
        self.assertIn('o1', p['carry_ids'])                            # the W39 loss, not repeated
        self.assertNotIn('o1', p['delete_ids'])
        self.assertEqual(sorted(p['delete_ids']), ['d1', 'd2', 'g1', 'l1', 's1'])
        self.assertEqual(p['keep_new_week'], 1)
        self.assertEqual(p['carry_elsewhere'], ['m1', 'x1'])

    def test_I16_asserts(self):
        w41, w40, w39, clone = split_fixture()
        self.assertIn('created after the clone',
                      dies(S.plan, w41, w40, [w39], FIELDS, dt.date(2026, 10, 4), -5,
                           '2026-10-02T00:00:00.000Z'))
        short = dump(*w40['records'][:-1])
        self.assertIn('diff is not clean', dies(S.plan, w41, short, [], FIELDS, dt.date(2026, 10, 4), -5, clone))

    def test_carry_verify_stops_on_a_real_gap(self):
        w41, w40, w39, _ = split_fixture()
        self.assertIn('260905_0742', dies(S.verify_carry, w41, [w41, w40, w39], FIELDS))

    def test_carry_verify_passes_once_recarried_and_names_media(self):
        w41, w40, w39, _ = split_fixture()
        again = rec('x2', '2026-10-04T16:00:00.000Z', key='260905_0742', status=INT,
                    practice=ACTION, datetime='2026-09-05T12:42:00.000Z')
        w41b = dump(*(w41['records'] + [again]))
        gaps = S.verify_carry(w41b, [w41b, w40, w39], FIELDS)
        self.assertEqual([g['chain'] for g in gaps], ['260906_0700'])
        self.assertTrue(gaps[0]['media'])

    def test_carry_verify_sees_a_closed_row_as_no_carry(self):
        w41, w40, w39, _ = split_fixture()
        # the new base holds only an older CLOSED row for a chain the archive reopened
        reopened = rec('y2', '2026-09-10T00:00:00.000Z', key='260909_0700', status=MOT, practice=ACTION,
                       datetime='2026-09-09T12:00:00.000Z')
        closed = rec('y1', '2026-09-09T12:00:00.000Z', key='260909_0700', status=DONE, practice=ACTION,
                     datetime='2026-09-09T12:00:00.000Z')
        w41b = dump(*(w41['records'] + [closed]))
        arch = dump(*(w39['records'] + [reopened]))
        gaps = S.carry_gaps(w41b, [w41b, arch], FIELDS)
        self.assertIn('260909_0700', [g['chain'] for g in gaps])


class Export(unittest.TestCase):
    def test_her_words_only(self):
        d = F['divider']
        self.assertEqual(X.hers(f'mine\n{d}\n[be•do] theirs'), 'mine')
        self.assertEqual(X.hers('mine\n---\n[be•do] theirs'), 'mine')    # the 190 W40 rows
        self.assertEqual(X.hers('[be•do] theirs only'), '')                # the 80 W40 rows
        self.assertEqual(X.hers('[be•do] theirs\n> screen text'), '> screen text')
        self.assertEqual(X.hers(f'mine\n{d}\n[be•do] x\n> screen'), 'mine\n\n> screen')
        self.assertEqual(X.hers('mine\n[be•do] no divider'), 'mine')

    def test_clock_reads_the_same_everywhere(self):
        self.assertEqual(X.clock(dt.datetime(2026, 10, 4, 7, 5)), '7:05 AM')
        self.assertEqual(X.clock(dt.datetime(2026, 10, 4, 0, 30)), '12:30 AM')
        self.assertEqual(X.clock(dt.datetime(2026, 10, 4, 12, 0)), '12:00 PM')
        self.assertEqual(X.clock(dt.datetime(2026, 10, 4, 21, 45)), '9:45 PM')

    def test_docx_without_pandoc(self):
        import importlib.util
        if importlib.util.find_spec('docx') is None:
            self.skipTest('python-docx not installed here')
        with tempfile.TemporaryDirectory() as t:
            md, out = os.path.join(t, 'w.md'), os.path.join(t, 'w.docx')
            open(md, 'w', encoding='utf-8').write('# W\n\n## Sunday\n\n**7:05 AM · ● log x**\n\n> screen\n')
            with mock.patch('shutil.which', return_value=None):
                self.assertEqual(X.write_docx(md, out), 'python-docx')
            self.assertGreater(os.path.getsize(out), 1000)


if __name__ == '__main__':
    unittest.main()
