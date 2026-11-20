"""Local text extraction. Originals, numeric strings and cached formulas stay intact."""
import csv
from dataclasses import dataclass, field
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile

SUPPORTED = {'.xlsx', '.csv', '.tsv', '.txt', '.md', '.docx', '.pptx', '.pdf'}
SS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
WORD = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
DRAW = 'http://schemas.openxmlformats.org/drawingml/2006/main'


class IngestError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


@dataclass
class Chunk:
    locator: str
    text: str
    details: dict = field(default_factory=dict)


@dataclass
class Extraction:
    chunks: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def relationship_targets(archive, part):
    directory, basename = posixpath.split(part)
    rels = posixpath.join(directory, '_rels', basename + '.rels')
    result = {}
    for item in ET.fromstring(archive.read(rels)):
        if item.get('TargetMode') == 'External':
            continue
        target = item.attrib['Target']
        result[item.attrib['Id']] = (
            target.lstrip('/') if target.startswith('/')
            else posixpath.normpath(posixpath.join(directory, target))
        )
    return result


def xlsx_string(element):
    if element is None:
        return ''
    return ''.join(child.text or '' if child.tag == f'{{{SS}}}t'
                   else ''.join(t.text or '' for t in child.findall(f'{{{SS}}}t'))
                   for child in element if child.tag in (f'{{{SS}}}t', f'{{{SS}}}r'))


def extract_xlsx(path):
    result = Extraction(warnings=[
        'Saved numeric strings and cached formula values only; no recalculation or date/number formatting.',
        'Images, charts and embedded objects remain in the original workbook and are not indexed.',
    ])
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        targets = relationship_targets(archive, 'xl/workbook.xml')
        props = workbook.find(f'{{{SS}}}workbookPr')
        date_system = '1904' if props is not None and props.get('date1904') in ('1', 'true') else '1900'
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            with archive.open('xl/sharedStrings.xml') as stream:
                for _, element in ET.iterparse(stream, events=('end',)):
                    if element.tag == f'{{{SS}}}si':
                        strings.append(xlsx_string(element))
                        element.clear()
        sheets = workbook.find(f'{{{SS}}}sheets')
        for sheet in sheets:
            part = targets[sheet.attrib[f'{{{REL}}}id']]
            with archive.open(part) as stream:
                for _, row in ET.iterparse(stream, events=('end',)):
                    if row.tag != f'{{{SS}}}row':
                        continue
                    cells, text = [], []
                    for cell in row.findall(f'{{{SS}}}c'):
                        address = cell.attrib['r']
                        typ = cell.get('t', 'n')
                        value_node = cell.find(f'{{{SS}}}v')
                        raw = value_node.text if value_node is not None else None
                        formula_node = cell.find(f'{{{SS}}}f')
                        formula = '=' + formula_node.text if formula_node is not None and formula_node.text else None
                        if typ == 's' and raw is not None:
                            value = strings[int(raw)]
                        elif typ == 'inlineStr':
                            value = xlsx_string(cell.find(f'{{{SS}}}is'))
                        else:
                            value = raw
                        if value in (None, '') and formula_node is None:
                            continue
                        details = {'address': address, 'cell_type': typ, 'raw_value': raw,
                                   'value': value, 'formula': formula, 'style_index': cell.get('s')}
                        if formula_node is not None:
                            details['formula_attributes'] = dict(formula_node.attrib)
                        cells.append(details)
                        rendered = value if value is not None else 'cached value unavailable'
                        if formula_node is not None:
                            rendered += ' [formula: ' + (formula or 'shared/array formula metadata') + ']'
                        text.append(address + ': ' + rendered)
                    if cells:
                        name = sheet.attrib['name'].replace("'", "''")
                        locator = f"'{name}'!{cells[0]['address']}:{cells[-1]['address']}"
                        result.chunks.append(Chunk(locator, ' | '.join(text), {
                            'sheet': sheet.attrib['name'], 'visibility': sheet.get('state', 'visible'),
                            'date_system': date_system, 'cells': cells,
                        }))
                    row.clear()
    return result


def extract_text(path):
    chunks = []
    for number, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        if line.strip():
            chunks.append(Chunk(f'lines {number}-{number}', line))
    return Extraction(chunks)


def extract_csv(path):
    chunks = []
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = csv.reader(stream, delimiter='\t' if path.suffix.lower() == '.tsv' else ',', strict=True)
        header = next(rows, [])
        if any(header):
            chunks.append(Chunk('row 1', ' | '.join(header), {'values': header, 'is_header': True}))
        for number, values in enumerate(rows, 2):
            if any(values):
                text = ' | '.join(f'{header[i] if i < len(header) else "column " + str(i + 1)}: {value}'
                                  for i, value in enumerate(values))
                chunks.append(Chunk(f'row {number}', text, {'headers': header, 'values': values}))
    return Extraction(chunks)


def word_text(element):
    parts = []
    for item in element.iter():
        if item.tag == f'{{{WORD}}}p' and item is not element and parts:
            parts.append('\n')
        elif item.tag == f'{{{WORD}}}t':
            parts.append(item.text or '')
        elif item.tag == f'{{{WORD}}}tab':
            parts.append('\t')
        elif item.tag in (f'{{{WORD}}}br', f'{{{WORD}}}cr'):
            parts.append('\n')
    return ''.join(parts)


def extract_docx(path):
    result = Extraction(warnings=['Body paragraphs and tables only; headers, footnotes, images and embedded objects are not indexed.'])
    with zipfile.ZipFile(path) as archive:
        body = ET.fromstring(archive.read('word/document.xml')).find(f'{{{WORD}}}body')
        paragraph, table = 0, 0
        for element in body:
            if element.tag == f'{{{WORD}}}p':
                paragraph += 1
                text = word_text(element)
                if text.strip():
                    result.chunks.append(Chunk(f'paragraph {paragraph}', text))
            elif element.tag == f'{{{WORD}}}tbl':
                table += 1
                for number, row in enumerate(element.findall(f'{{{WORD}}}tr'), 1):
                    values = [word_text(cell) for cell in row.findall(f'{{{WORD}}}tc')]
                    text = ' | '.join(values)
                    if text.strip():
                        result.chunks.append(Chunk(f'table {table}, row {number}', text, {'values': values}))
    return result


def extract_pptx(path):
    result = Extraction(warnings=['Slide text and table text only; images, charts, embedded objects and speaker notes are not indexed.'])
    ns = 'http://schemas.openxmlformats.org/presentationml/2006/main'
    with zipfile.ZipFile(path) as archive:
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        targets = relationship_targets(archive, 'ppt/presentation.xml')
        for slide_number, slide in enumerate(presentation.find(f'{{{ns}}}sldIdLst'), 1):
            root = ET.fromstring(archive.read(targets[slide.attrib[f'{{{REL}}}id']]))
            for paragraph_number, paragraph in enumerate(root.iter(f'{{{DRAW}}}p'), 1):
                text = ''.join((t.text or '') if t.tag == f'{{{DRAW}}}t' else '\n'
                               for t in paragraph.iter() if t.tag in (f'{{{DRAW}}}t', f'{{{DRAW}}}br'))
                if text.strip():
                    result.chunks.append(Chunk(f'slide {slide_number}, paragraph {paragraph_number}', text))
    return result


def extract_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise IngestError('missing_dependency', 'PDF extraction requires pypdf; use the bundled Python runtime.') from exc
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise IngestError('encrypted_file', 'Password-protected PDFs are not supported.')
    result = Extraction()
    for number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ''
        if text.strip():
            result.chunks.append(Chunk(f'page {number}', text.strip()))
        else:
            result.warnings.append(f'Page {number}: no extractable text; OCR is not enabled.')
    return result


def extract(path):
    path = Path(path)
    if not path.is_file():
        raise IngestError('missing_file', 'The input is not an existing file.')
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise IngestError('unsupported_format', 'Unsupported format; use XLSX, CSV, TSV, TXT, MD, DOCX, PPTX or PDF.')
    readers = {'.xlsx': extract_xlsx, '.csv': extract_csv, '.tsv': extract_csv,
               '.txt': extract_text, '.md': extract_text, '.docx': extract_docx,
               '.pptx': extract_pptx, '.pdf': extract_pdf}
    try:
        result = readers[suffix](path)
    except IngestError:
        raise
    except UnicodeError as exc:
        raise IngestError('invalid_encoding', 'Text inputs must use UTF-8 encoding.') from exc
    except (OSError, ValueError, KeyError, IndexError, TypeError, ET.ParseError, zipfile.BadZipFile) as exc:
        raise IngestError('extraction_failed', 'The file could not be parsed; verify its format and integrity.') from exc
    except Exception as exc:
        # Do not put parser messages or source text into ingestion logs.
        raise IngestError('extraction_failed', 'The local extractor could not read this file.') from exc
    if not result.chunks:
        raise IngestError('no_extractable_text', 'No text was extracted; empty or scanned documents need another source or OCR.')
    return result
