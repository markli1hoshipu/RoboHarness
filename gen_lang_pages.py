#!/usr/bin/env python3
"""Refresh root metadata and generate language pages from docs/index.html.

Run python3 gen_lang_pages.py after editing the bilingual source. Only the
managed metadata is refreshed in the source; its body remains authoritative.
"""
import json
import pathlib
import re
from html import escape
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / 'docs/index.html'
SITE_ORIGIN = 'https://www.robo-harness.com'
PAPER_TITLE = 'RoboHarness: Memory-Driven Orchestration of Heterogeneous Robot Policies for Long-Horizon Planning'
PAPER_URL = 'https://arxiv.org/abs/2607.18060v3'
PAPER_DATE = '2026-09-29'  # Publication of the cited v3, not the website update.
AUTHORS = ['Jinbang Huang', 'Zhiyuan Li', 'Yuanzhao Hu', 'Ran Qi', 'Yixin Xiao', 'Mark Coates', 'Tongtong Cao', 'Zhanguang Zhang', 'Yingxue Zhang']
TITLES = {'en': 'RoboHarness | Coding Agent Harness for Robot Control', 'zh': 'RoboHarness：面向机器人控制的 Coding Agent Harness'}
DESCRIPTIONS = {
    'en': 'RoboHarness uses a coding agent harness, execution memory, and Memory Bridge to orchestrate heterogeneous robot policies for long-horizon planning and control.',
    'zh': 'RoboHarness 利用 coding agent harness、执行记忆和 Memory Bridge 编排异构机器人策略，实现长时序机器人规划与控制。',
}
IMAGE = '/assets/images/harness_framework.png'


class TagAttributes(HTMLParser):
    def handle_starttag(self, tag, attrs):
        self.attrs = dict(attrs)


def remove_page_metadata(html):
    """Replace inherited page metadata, including legacy unmarked tags."""
    html = re.sub(r'\s*<!-- BEGIN GENERATED METADATA -->.*?<!-- END GENERATED METADATA -->', '', html, flags=re.S)
    html = re.sub(r'\s*<title\b[^>]*>.*?</title>', '', html, flags=re.S | re.I)
    def clean(match):
        tag = match.group()
        parser = TagAttributes()
        parser.feed(tag)
        attrs = parser.attrs
        name = (attrs.get('name') or attrs.get('property') or '').lower()
        rel = (attrs.get('rel') or '').lower().split()
        if name == 'description' or name.startswith(('og:', 'twitter:', 'citation_')):
            return ''
        if 'canonical' in rel or ('alternate' in rel and 'hreflang' in attrs):
            return ''
        return tag
    return re.sub(r'<(?:meta|link)\b[^>]*>', clean, html, flags=re.I)


def metadata(lang):
    canonical = SITE_ORIGIN + ('/zh/' if lang == 'zh' else '/')
    title, description = TITLES[lang], DESCRIPTIONS[lang]
    lines = ['<!-- BEGIN GENERATED METADATA -->', f'<title>{escape(title)}</title>']
    def meta(name, value, attr='name'):
        lines.append(f'<meta {attr}="{name}" content="{escape(value, quote=True)}">')
    meta('description', description)
    lines.append(f'<link rel="canonical" href="{canonical}">')
    for code, path in [('en', '/'), ('zh', '/zh/'), ('x-default', '/')]:
        lines.append(f'<link rel="alternate" hreflang="{code}" href="{SITE_ORIGIN}{path}">')
    for name, value in [('title', title), ('description', description), ('url', canonical), ('image', SITE_ORIGIN + IMAGE), ('type', 'website')]:
        meta('og:' + name, value, 'property')
    for name, value in [('card', 'summary_large_image'), ('title', title), ('description', description), ('image', SITE_ORIGIN + IMAGE)]:
        meta('twitter:' + name, value)
    meta('citation_title', PAPER_TITLE)
    for author in AUTHORS:
        meta('citation_author', author)
    meta('citation_publication_date', PAPER_DATE.replace('-', '/'))
    article_id = PAPER_URL + '#article'
    data = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': canonical + '#webpage', 'url': canonical,
         'name': title, 'description': description, 'inLanguage': lang,
         'mainEntity': {'@id': article_id}},
        {'@type': 'ScholarlyArticle', '@id': article_id, 'name': PAPER_TITLE,
         'headline': PAPER_TITLE, 'author': [{'@type': 'Person', 'name': n} for n in AUTHORS],
         'datePublished': PAPER_DATE, 'version': '3', 'identifier': 'arXiv:2607.18060v3',
         'url': PAPER_URL, 'sameAs': PAPER_URL},
    ]}
    lines.append('<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace('<', '\\u003c') + '</script>')
    lines.append('<!-- END GENERATED METADATA -->')
    return '\n    '.join(lines)


def build(source, lang, subpage=False):
    html = remove_page_metadata(source)
    html = re.sub(r'<html\b[^>]*>', '<html lang="zh" class="zh">' if lang == 'zh' else '<html lang="en">', html, count=1)
    html = html.replace('</head>', '    ' + metadata(lang) + '\n</head>', 1)
    if subpage:
        html = html.replace('"assets/', '"../assets/')
    return html


def main():
    assert (ROOT / 'docs/CNAME').read_text().strip() == SITE_ORIGIN.removeprefix('https://')
    assert (ROOT / 'docs' / IMAGE.lstrip('/')).is_file()
    source = SRC.read_text(encoding='utf-8')
    # Remove blank lines left by legacy metadata before inserting the managed block.
    source = '\n'.join(line.rstrip() for line in remove_page_metadata(source).split('\n'))
    source = re.sub(r'\n[ \t]*\n(?=[ \t]*</head>)', '\n', source)
    SRC.write_text(build(source, 'en'), encoding='utf-8')
    for lang in ('en', 'zh'):
        out = ROOT / 'docs' / lang / 'index.html'
        out.parent.mkdir(exist_ok=True)
        out.write_text(build(source, lang, subpage=True), encoding='utf-8')
        print(f'wrote {out.relative_to(ROOT)}')
    urls = [SITE_ORIGIN + '/', SITE_ORIGIN + '/zh/']
    (ROOT / 'docs/sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{url}</loc></url>\n' for url in urls) + '</urlset>\n', encoding='utf-8')
    robots = ROOT / 'docs/robots.txt'
    content = robots.read_text() if robots.exists() else 'User-agent: *\nAllow: /\n'
    content = re.sub(r'^Sitemap:.*\n?', '', content, flags=re.M | re.I)
    robots.write_text(content.rstrip() + '\n\nSitemap: ' + SITE_ORIGIN + '/sitemap.xml\n', encoding='utf-8')


if __name__ == '__main__':
    main()
