# -*- coding: utf-8 -*-
"""Installed skills in step with the version store (12 Nov 2026).

Her concern that day: installed skills need to stay in step with the repo. One
skill was installed and nowhere in the repo, three still carried their whole
text beside a repo copy that had moved on, and nothing said so.

An installed skill is in one of four states:

  loader          it downloads its procedure from the version store each run:
                  always in step, nothing to do
  older copy      the repo holds this skill, but the installed one carries its
                  own text: the repo wins (25 Oct 2026), and the installed copy
                  is replaced by its loader
  installed only  be•do's, and nowhere in the repo: its procedure can't be
                  tested, checked for privacy or changed by pull request
  not installed   in the repo and not on this machine (said, never a fault)

Only be•do's own skills are looked at: one the repo holds, or one whose text
names the system. Nothing personal lives here, and nothing is changed: installing
or replacing a skill is hers.

    python3 bedo_skills.py --installed ~/.claude/skills --repo skills.json
"""
import json, os, sys

MARK = 'be•do'
STORE = ('codeload.github.com', 'git clone')


def installed(root):
    """Every installed skill under `root`, by name: {name: SKILL.md text}. A
    skill folder is any folder holding a SKILL.md, at any depth; the first
    one found for a name is kept."""
    out = {}
    for d, _, files in sorted(os.walk(root)):
        if 'SKILL.md' in files:
            name = os.path.basename(d)
            if name not in out:
                with open(os.path.join(d, 'SKILL.md'), encoding='utf-8', errors='replace') as f:
                    out[name] = f.read()
    return out


def repo_skills(skills_dir):
    """What the version store holds: {name: {'loader': bool, 'retired': bool}}."""
    out = {}
    for name in sorted(os.listdir(skills_dir)):
        d = os.path.join(skills_dir, name)
        if os.path.isfile(os.path.join(d, 'SKILL.md')):
            out[name] = {'loader': os.path.isfile(os.path.join(d, 'loader', 'SKILL.md'))}
    return out


def is_loader(text):
    return any(s in text for s in STORE)


def states(have, repo, retired=()):
    """Sort every be•do skill into its state. `have` is installed(); `repo` is
    repo_skills() or the list the runner saved at the download."""
    out = {'loader': [], 'older copy': [], 'installed only': [], 'not installed': []}
    for name, text in sorted(have.items()):
        if name in repo:
            out['loader' if is_loader(text) else 'older copy'].append(name)
        elif MARK in text:
            out['installed only'].append(name)
    out['not installed'] = sorted(n for n in repo if n not in have and n not in set(retired))
    return out


def report(st, repo):
    n = sum(len(st[k]) for k in ('loader', 'older copy', 'installed only'))
    lines = [f'skills  {len(st["loader"])} of {n} installed be•do skills load from the version store']
    if st['older copy']:
        lines.append('older copy — the repo holds these, the installed ones carry their own text; the repo wins:')
        for s in st['older copy']:
            how = (f'replace it with plugins/bedo/skills/{s}/loader/SKILL.md' if (repo.get(s) or {}).get('loader')
                   else 'no loader in the repo yet: write one, then replace it')
            lines.append(f'  · {s} — {how}')
    if st['installed only']:
        lines.append('installed only — nowhere in the repo, so never tested, never checked, changed only by upload:')
        lines += [f'  · {s}' for s in st['installed only']]
    if st['not installed']:
        lines.append('in the repo, not installed here: ' + ' · '.join(st['not installed']))
    if not (st['older copy'] or st['installed only']):
        lines.append('all in step')
    return '\n'.join(lines)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='installed skills against the version store')
    ap.add_argument('--installed', action='append', help='a folder of installed skills (repeatable)')
    ap.add_argument('--repo', required=True, help="the repo's plugins/bedo/skills folder, or the skills.json saved at the download")
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    repo = repo_skills(a.repo) if os.path.isdir(a.repo) else json.load(open(a.repo, encoding='utf-8'))
    have = {}
    for root in a.installed or [os.path.expanduser('~/.claude/skills')]:
        if os.path.isdir(root):
            for k, v in installed(root).items():
                have.setdefault(k, v)
    if not have:
        sys.exit('skills: no installed skills found here — pass --installed FOLDER')
    try:
        import bedo_reader
        retired = bedo_reader.load_facts().get('skills_retired') or []
    except Exception:
        retired = []
    st = states(have, repo, retired)
    print(json.dumps(st, ensure_ascii=False, indent=1) if a.json else report(st, repo))
    sys.exit(1 if (st['older copy'] or st['installed only']) else 0)


if __name__ == '__main__':
    main()
