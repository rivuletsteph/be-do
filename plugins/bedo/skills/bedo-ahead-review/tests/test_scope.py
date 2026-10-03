"""Which chains the monthly ahead-review cards: intentions and in-motion rows,
not potentials — unless a potential asks to come back this month."""
import json, pathlib, subprocess, sys, tempfile, unittest

BUILD = pathlib.Path(__file__).resolve().parent.parent / 'scripts' / 'build_ahead_review.py'
F = {k: 'f_' + k for k in ('title', 'key', 'details', 'target', 'status', 'practice',
                           'rhythm', 'waiting_on', 'queue')}


def row(key, status, created='2026-09-01T12:00:00.000Z', **kw):
    c = {F['key']: key, F['title']: 'row ' + key, F['status']: {'name': status},
         F['practice']: kw.get('practice', '⚡ action'), F['details']: kw.get('details', '')}
    if kw.get('queue'): c[F['queue']] = True
    if kw.get('waiting_on'): c[F['waiting_on']] = kw['waiting_on']
    return {'id': 'r' + key, 'createdTime': created, 'cellValuesByFieldId': c}


def build(rows, today, fields=F):
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / 'stream.json').write_text(json.dumps({'records': rows, 'metadata': {'totalRecordCount': len(rows)}}), encoding='utf-8')
        (d / 'recs.json').write_text('{}', encoding='utf-8')
        (d / 'local.json').write_text(json.dumps({'fields': {'stream': fields}}), encoding='utf-8')
        p = subprocess.run([sys.executable, str(BUILD), '--stream', str(d / 'stream.json'), '--recs', str(d / 'recs.json'),
                            '--today', today, '--out', str(d / 'out.html'), '--local', str(d / 'local.json')],
                           capture_output=True, text=True, encoding='utf-8')
        if p.returncode:
            return p
        html = (d / 'out.html').read_text(encoding='utf-8')
        items = json.loads(html.split('const ITEMS = ', 1)[1].split(';\nconst G=', 1)[0])
        return sorted(i['k'] for i in items)


class Scope(unittest.TestCase):
    rows = [
        row('260801_0900', '⬜ intention'),
        row('260801_0901', '▶️ in motion'),
        row('260801_0902', '▫️potential'),
        row('260801_0903', '▫️potential', details='Let it rest. Ask me again at the beginning of November.'),
        row('260801_0904', '⬜ intention', queue=True),
        row('260801_0905', '⬜ intention', waiting_on='a reply'),
        row('260801_0906', '⬜ intention', practice='📗 book'),
        row('260801_0907', '✅ done'),
        row('261001_0900', '⬜ intention'),          # younger than 14 days
    ]

    def test_october(self):
        self.assertEqual(build(self.rows, '2026-10-02'), ['260801_0900', '260801_0901'])

    def test_ask_again_comes_back_in_its_month(self):
        self.assertEqual(build(self.rows, '2026-11-02'), ['260801_0900', '260801_0901', '260801_0903', '261001_0900'])

    def test_latest_row_per_key_decides(self):
        rows = [row('260801_0900', '⬜ intention'), row('260801_0900', '✅ done', created='2026-09-20T12:00:00.000Z')]
        self.assertEqual(build(rows, '2026-10-02'), [])

    def test_a_blank_field_id_stops_the_build(self):
        p = build(self.rows, '2026-10-02', fields={**F, 'queue': ''})
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('queue', p.stderr)


if __name__ == '__main__':
    unittest.main()
