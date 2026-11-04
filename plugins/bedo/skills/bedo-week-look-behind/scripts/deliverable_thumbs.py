#!/usr/bin/env python3
"""A small picture of each deliverable, for what moved forward on the day page (4 Nov 2026, her words: it'd be
really cool to show a visual about what I accomplished at work, a little image of what the deliverable was).

Pages the builder can't reach on its own (her artifacts sit behind her sign-in) are read by the chat and saved as
files; this renders each one the way a phone would show its top and keeps a small JPEG. An image file passed
as the page (a Drive thumbnail, a screenshot) is only made small.

    python3 deliverable_thumbs.py --page URL FILE [--page URL FILE ...] --out thumbs/
    # then: week_look_behind.py --day … --thumbs thumbs/

Writes thumbs/index.json ({url: file}) beside the pictures. Needs Playwright (with its Chromium) for pages and
Pillow for the shrinking; a page that won't render is skipped and named, never a stop.
"""
import argparse, hashlib, io, json, os, sys

W, H, OUT_W = 720, 480, 480       # a 3:2 window on the page's top, kept at 480 px wide


def shrink(img_bytes, path):
    from PIL import Image
    im = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    im = im.crop((0, 0, im.width, min(im.height, int(im.width * H / W))))
    im.thumbnail((OUT_W, OUT_W))
    im.save(path, 'JPEG', quality=78, optimize=True)


def node_shots(pages):
    """Screenshots through Node's Playwright: {url: png path}."""
    import subprocess, tempfile
    tmp = tempfile.mkdtemp()
    jobs = [dict(url=u, file=os.path.abspath(f), out=os.path.join(tmp, f'{i}.png')) for i, (u, f) in enumerate(pages)]
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
          f"const p=await b.newPage({{viewport:{{width:{W},height:{H}}},deviceScaleFactor:1}});"
          "for(const j of JSON.parse(process.argv[1])){try{await p.goto('file://'+j.file,{waitUntil:'load',timeout:20000});"
          "await p.waitForTimeout(800);await p.screenshot({path:j.out});}catch(e){console.error(j.url+': '+e.message)}}"
          "await b.close();})()")
    subprocess.run(['node', '-e', js, json.dumps(jobs)], check=False, timeout=180)
    return {j['url']: j['out'] for j in jobs if os.path.exists(j['out'])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--page', nargs=2, action='append', metavar=('URL', 'FILE'), default=[],
                    help="the deliverable's link and a saved copy of it (an .html page or an image)")
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    index, skipped = {}, []
    pages = [(u, f) for u, f in a.page if f.lower().endswith(('.html', '.htm'))]
    images = [(u, f) for u, f in a.page if (u, f) not in pages]
    for url, f in images:
        n = hashlib.sha1(url.encode()).hexdigest()[:12] + '.jpg'
        try:
            shrink(open(f, 'rb').read(), os.path.join(a.out, n))
            index[url] = n
        except Exception as e:  # noqa: BLE001
            skipped.append(f'{url}: {e}')
    if pages:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:                 # a machine with Playwright for Node only (the cloud sessions)
            shots = node_shots(pages)
            for url, f in pages:
                n = hashlib.sha1(url.encode()).hexdigest()[:12] + '.jpg'
                try:
                    shrink(open(shots[url], 'rb').read(), os.path.join(a.out, n))
                    index[url] = n
                except Exception as e:  # noqa: BLE001
                    skipped.append(f'{url}: {e}')
            pages = []
    if pages:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
            for url, f in pages:
                n = hashlib.sha1(url.encode()).hexdigest()[:12] + '.jpg'
                try:
                    pg.goto('file://' + os.path.abspath(f), wait_until='load', timeout=20000)
                    pg.wait_for_timeout(800)
                    shrink(pg.screenshot(), os.path.join(a.out, n))
                    index[url] = n
                except Exception as e:  # noqa: BLE001
                    skipped.append(f'{url}: {e}')
            b.close()
    json.dump(index, open(os.path.join(a.out, 'index.json'), 'w', encoding='utf-8'), indent=1)
    print(json.dumps(dict(made=len(index), skipped=skipped)))


if __name__ == '__main__':
    sys.exit(main())
