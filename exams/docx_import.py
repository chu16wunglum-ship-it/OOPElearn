import re
import zipfile
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
LETTER_INDEX = {'ก': 0, 'ข': 1, 'ค': 2, 'ง': 3}
UNIT_HEADER_RE = re.compile(r'หน่วยที่\s*(\d+)')
QSTART_RE = re.compile(r'^(\d+)\.\s*(.+)$')
CHOICE_RE = re.compile(r'^\s*([กขคง])\.\s*(.+)$')
ANSWER_HEADER_RE = re.compile(r'เฉลย')


def _paragraph_texts(path):
    with zipfile.ZipFile(path) as z:
        xml_content = z.read('word/document.xml')
    root = ET.fromstring(xml_content)
    return [''.join(n.text or '' for n in para.iter(f'{W}t')).strip() for para in root.iter(f'{W}p')]


def parse_pretest_bank(path):
    """Parse a unit-segmented pretest .docx: plain-text questions grouped under
    'หน่วยที่ N' headers, with a trailing 'เฉลย...' section listing
    (question number, answer letter) pairs as the answer key.

    Returns {unit_number: [{'num', 'text', 'choices': [str x4], 'answer_index'}]}.
    """
    paras = _paragraph_texts(path)

    key_start = next((i for i, p in enumerate(paras) if ANSWER_HEADER_RE.search(p)), len(paras))
    body_paras = paras[:key_start]
    key_paras = [p for p in paras[key_start + 1:] if p]

    answer_key = {}
    it = iter(key_paras)
    for num_str, letter in zip(it, it):
        if num_str.isdigit() and letter in LETTER_INDEX:
            answer_key[int(num_str)] = LETTER_INDEX[letter]

    bank = {}
    current_unit = None
    current_q = None

    def finalize():
        nonlocal current_q
        if current_q and len(current_q['choices']) == 4:
            current_q['answer_index'] = answer_key.get(current_q['num'])
            bank.setdefault(current_unit, []).append(current_q)
        current_q = None

    for p in body_paras:
        if not p:
            continue
        um = UNIT_HEADER_RE.search(p)
        if um:
            finalize()
            current_unit = int(um.group(1))
            continue
        qm = QSTART_RE.match(p)
        if qm:
            finalize()
            current_q = {'num': int(qm.group(1)), 'text': qm.group(2).strip(), 'choices': []}
            continue
        cm = CHOICE_RE.match(p)
        if cm and current_q is not None and len(current_q['choices']) < 4:
            current_q['choices'].append(cm.group(2).strip())
            continue
    finalize()

    return bank
