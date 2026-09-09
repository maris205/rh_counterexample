"""Export the supplied PDFs as page-indexed Markdown without guessing LaTeX.

Requires Poppler's pdftotext and pdfinfo on PATH; only Python's stdlib is used.
--check regenerates in memory and checks all published bytes without rewriting.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / 'papers'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def export(item):
    pdf = PAPERS / 'pdf' / (item['id'] + '.pdf')
    if digest(pdf.read_bytes()) != item['pdf_sha256']:
        raise ValueError('Source PDF changed: ' + item['id'])
    info = subprocess.run(['pdfinfo', str(pdf)], check=True, capture_output=True).stdout.decode('utf-8', errors='replace')
    count = int(re.search(r'^Pages:\s+(\d+)', info, re.MULTILINE)[1])
    if count != item['pages']:
        raise ValueError('PDF page count differs from catalog')
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / 'layout.txt'
        subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', str(pdf), str(output)], check=True, capture_output=True)
        raw = output.read_bytes()
    text = raw.decode('utf-8-sig').replace('\r\n', '\n')
    pages = text.split('\f')
    if pages and not pages[-1].strip():
        pages.pop()
    if len(pages) != count or any(not page.strip() for page in pages):
        raise ValueError('Missing or empty text page; inspect source PDF')
    lines = [f"# {item['title']}", '', '[论文目录](../README.md)', '',
             f"- 原始文件：`{item['source_filename']}`。",
             f"- [原始 PDF](../pdf/{item['id']}.pdf)，共 {count} 个物理页。",
             f"- PDF SHA-256：`{item['pdf_sha256']}`。", '',
             '> 本文为 PDF 的按页文本提取版，供搜索、引用定位和程序读取。',
             '> 正文使用等宽文本块保留提取顺序与空格；未将公式人工重排成 LaTeX。',
             '> 上下标、特殊符号、双栏顺序及图形可能无法由文本准确表达，请以所附 PDF 为准。',
             '> 原稿表述按原文保留；归档不表示其中的数学结论已经通过验证。', '',
             '## 页码导航', '',
             ' · '.join(f'[{n}](#pdf-page-{n})' for n in range(1, count + 1)), '']
    for number, page in enumerate(pages, 1):
        body = '\n'.join(line.rstrip() for line in page.strip('\n').split('\n'))
        fence = '`' * max(3, 1 + max((len(s) for s in re.findall(r'`+', body)), default=0))
        lines.extend([f'## PDF page {number}', '',
                      f"[核对 PDF 原页](../pdf/{item['id']}.pdf#page={number})", '',
                      fence + 'text', body, fence, ''])
    markdown = '\n'.join(lines).encode('utf-8')
    metadata = {'id': item['id'], 'pdf': f"pdf/{item['id']}.pdf", 'pdf_sha256': item['pdf_sha256'],
                'markdown': f"markdown/{item['id']}.md", 'markdown_sha256': digest(markdown),
                'pdf_pages': count, 'markdown_pages': len(pages), 'empty_text_pages': 0,
                'replacement_characters': text.count('\ufffd'), 'layout_text_sha256': digest(raw),
                'page_text_sha256': [digest(p.encode('utf-8')) for p in pages]}
    return markdown, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for tool in ('pdftotext', 'pdfinfo'):
        if shutil.which(tool) is None:
            parser.error('Install Poppler and add ' + tool + ' to PATH')
    catalog = json.loads((PAPERS / 'catalog.json').read_text(encoding='utf-8'))
    generated, records = [], []
    for item in catalog:
        content, record = export(item)
        generated.append((PAPERS / record['markdown'], content))
        records.append(record)
    version = subprocess.run(['pdftotext', '-v'], capture_output=True, check=True)
    tool_version = (version.stdout + version.stderr).decode('utf-8', errors='replace').splitlines()[0]
    manifest = {'schema': 1, 'tool': tool_version, 'converter_sha256': digest(Path(__file__).read_bytes()),
                'format': 'Page-indexed pdftotext -layout output in Markdown text fences',
                'pdf_content_unchanged': True, 'mathematical_validation_claimed': False,
                'total_papers': len(records), 'total_pages': sum(r['pdf_pages'] for r in records),
                'papers': records}
    generated.append((PAPERS / 'EXTRACTION_MANIFEST.json',
                      (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')))
    for path, content in generated:
        if args.check:
            if not path.exists() or path.read_bytes() != content:
                raise ValueError('Published output differs: ' + str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    print(('VERIFIED' if args.check else 'EXPORTED'), len(records), 'papers;', manifest['total_pages'], 'pages')


if __name__ == '__main__':
    main()
