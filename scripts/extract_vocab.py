"""
Extract vocabulary data from PPTX files → vocab.json + images/
Enhanced unified parser: extracts ALL words/synonyms without omitting any.
"""

import os
import sys
import io
import json
import re
import glob
from pptx import Presentation

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PPTX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pp')
OUTPUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(OUTPUT_DIR, 'data')
IMAGES_DIR = os.path.join(OUTPUT_DIR, 'images')

VN_CHARS = set('àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ')
TITLE_KEYWORDS = {'VOCABULARY', 'TỪ VỰNG', 'LESSON', 'LISTENING', 'READING', 'ĐỌC', 'NGHE', 'PHẦN', 'LUYỆN TẬP', 'PART'}

COMMON_EN_WORDS = {
    'goods', 'happen', 'occur', 'rebate', 'promotional', 'cargo', 'contest',
    'opportunity', 'applicant', 'finish', 'abstract', 'malfunctioning',
    'figures', 'numbers', 'whole', 'entire', 'confirm', 'verify',
    'generate', 'create', 'substitute', 'replace', 'shipping', 'delivery',
    'mandatory', 'obligated', 'investigate', 'polite', 'courteous', 'predict',
    'forecast', 'foresee', 'anticipate', 'obey', 'document', 'target', 'goal',
    'purpose', 'objective', 'release', 'publish', 'launch', 'unveil', 'reveal',
    'disclose', 'decline', 'decrease', 'reach', 'contact', 'invoice', 'bill',
    'receipt', 'expense', 'cost', 'expenditure', 'submit', 'complete'
}


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)


def extract_lesson_number(filename):
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else 0


def has_vietnamese(text):
    return bool(set(text) & VN_CHARS)


def clean_text(t):
    return t.replace('\x0b', '\n').strip()


def is_title_slide(texts):
    if not texts:
        return True
    combined = ' '.join(texts).upper().strip()
    for kw in TITLE_KEYWORDS:
        combined = combined.replace(kw, '').strip()
    cleaned = re.sub(r'[\d\s,&\-–]+', '', combined)
    cleaned = re.sub(r'PART\s*\d*', '', cleaned, flags=re.IGNORECASE)
    return len(cleaned) < 3


def split_example(text):
    text = text.strip()
    paren_match = re.search(r'\(([^)]*[' + ''.join(list(VN_CHARS)[:10]) + r'][^)]*)\)\s*\.?\s*$', text)
    if paren_match:
        vi = paren_match.group(1).strip()
        en = text[:paren_match.start()].strip().rstrip('.')
        return en, vi
    return text, ''


def is_pure_ipa(token):
    token = token.strip()
    if not (token.startswith('/') and token.endswith('/') and len(token) >= 2):
        return False
    inner = token.strip('/ \t\n')
    if not inner:
        return False
    if inner.lower() in COMMON_EN_WORDS:
        return False
    words = [w for w in re.split(r'\s+', inner.lower()) if w]
    if all(w in COMMON_EN_WORDS for w in words):
        return False
    return True


def extract_true_ipas(text):
    candidates = re.findall(r'/[^/\n]{2,}/', text)
    result = []
    for c in candidates:
        if is_pure_ipa(c):
            result.append(c.strip())
    return result


def clean_word(w):
    w = re.sub(r'^\d+[\.\t\s]+', '', w)
    w = re.sub(r'\([a-zA-Z,\s]+\)', '', w)
    w = w.strip().rstrip(' ,;:-–/')
    return w


def parse_slide_thorough(slide, lesson_id, word_idx):
    text_blocks = []
    image_shapes = []
    
    for shape in slide.shapes:
        if shape.shape_type == 13: # Picture
            image_shapes.append(shape)
        elif hasattr(shape, 'text'):
            raw = clean_text(shape.text)
            cleaned = raw.replace('‹#›', '').strip()
            if cleaned and not re.match(r'^\d{1,3}$', cleaned):
                text_blocks.append(cleaned)
                
    if not text_blocks or is_title_slide(text_blocks):
        return None
        
    all_lines = []
    for b in text_blocks:
        for l in b.split('\n'):
            l_str = l.strip()
            if l_str:
                all_lines.append(l_str)
                
    if not all_lines:
        return None
        
    # Find boundary for Vietnamese meaning
    meaning_idx = -1
    for i, line in enumerate(all_lines):
        if any(line.upper().startswith(kw) for kw in TITLE_KEYWORDS) and len(line) < 30:
            continue
        if has_vietnamese(line):
            if line.lower().startswith(('ex:', 'example:')):
                continue
            if line.startswith('(') and line.endswith(')') and len(line) > 25:
                continue
            meaning_idx = i
            break
            
    if meaning_idx == -1:
        return None
        
    pre_meaning = [l for l in all_lines[:meaning_idx] if not any(l.upper().startswith(kw) for kw in TITLE_KEYWORDS)]
    post_meaning = all_lines[meaning_idx:]
    
    if not pre_meaning:
        return None
        
    # Meaning & Example
    meaning = post_meaning[0]
    example_en = ''
    example_vi = ''
    
    if 'Ex:' in meaning or 'ex:' in meaning:
        parts = re.split(r'\n*[Ee]x:\s*', meaning, maxsplit=1)
        meaning = parts[0].strip()
        if len(parts) > 1:
            example_en, example_vi = split_example(parts[1].strip())
            
    for l in post_meaning[1:]:
        if l.lower().startswith(('ex:', 'example:')):
            ex_content = re.sub(r'^(ex|example):\s*', '', l, flags=re.IGNORECASE).strip()
            example_en, example_vi = split_example(ex_content)
            break
        elif has_vietnamese(l) and l.startswith('(') and not example_vi:
            example_vi = l.strip('()')
        elif not has_vietnamese(l) and len(l) > 10 and not example_en:
            example_en, example_vi = split_example(l)
            
    # Part of speech
    pos = ''
    full_pre_text = ' '.join(pre_meaning)
    pos_matches = re.findall(r'\(([a-zA-Z,\s]+)\)', full_pre_text)
    for p in pos_matches:
        p_clean = p.strip().lower()
        if p_clean in ['n', 'v', 'a', 'adj', 'adv', 'np', 'phr', 'phrasal verb', 'v,n', 'n,v']:
            pos = p_clean
            break

    word_details = []
    cleaned_lines = []
    for l in pre_meaning:
        l_no_num = re.sub(r'^\d+[\.\t\s]+', '', l).strip()
        if l_no_num and not re.match(r'^\([a-zA-Z,\s]+\)$', l_no_num):
            cleaned_lines.append(l_no_num)
            
    lines_with_ipa = []
    for l in cleaned_lines:
        ipas = extract_true_ipas(l)
        if ipas:
            w_text = l
            for ipa in ipas:
                w_text = w_text.replace(ipa, ' ')
            w_text = clean_word(w_text)
            if w_text:
                lines_with_ipa.append((w_text, ipas))
                
    if len(lines_with_ipa) >= 2:
        for w_text, ipas in lines_with_ipa:
            if '=' in w_text:
                for sub_w in w_text.split('='):
                    sw = clean_word(sub_w)
                    if sw:
                        word_details.append({'word': sw, 'ipa': ' '.join(ipas)})
            elif '/' in w_text and not ('http' in w_text):
                for sub_w in w_text.split('/'):
                    sw = clean_word(sub_w)
                    if sw:
                        word_details.append({'word': sw, 'ipa': ' '.join(ipas)})
            else:
                sw = clean_word(w_text)
                if sw:
                    word_details.append({'word': sw, 'ipa': ' '.join(ipas)})
    else:
        all_ipas = []
        for l in pre_meaning:
            all_ipas.extend(extract_true_ipas(l))
            
        text_for_words = full_pre_text
        for ipa in all_ipas:
            text_for_words = text_for_words.replace(ipa, ' ')
            
        text_for_words = re.sub(r'^\s*\d+[\.\t\s]+', '', text_for_words)
        text_for_words = re.sub(r'\([a-zA-Z,\s]+\)', '', text_for_words)
        colloc_match = re.search(r'\([a-zA-Z\s,]+\)', text_for_words)
        if colloc_match:
            text_for_words = text_for_words[:colloc_match.start()] + text_for_words[colloc_match.end():]
            
        text_for_words = text_for_words.strip()
        
        if '=' in text_for_words:
            parts = [clean_word(p) for p in text_for_words.split('=') if clean_word(p)]
            for idx, p in enumerate(parts):
                ipa = all_ipas[idx] if idx < len(all_ipas) else (all_ipas[0] if all_ipas else '')
                word_details.append({'word': p, 'ipa': ipa})
        elif '><' in text_for_words:
            parts = [clean_word(p) for p in text_for_words.split('><') if clean_word(p)]
            for idx, p in enumerate(parts):
                ipa = all_ipas[idx] if idx < len(all_ipas) else (all_ipas[0] if all_ipas else '')
                word_details.append({'word': p, 'ipa': ipa})
        elif '/' in text_for_words:
            parts = [clean_word(p) for p in text_for_words.split('/') if clean_word(p)]
            if len(parts) >= 2 and all(len(p) > 1 for p in parts):
                for idx, p in enumerate(parts):
                    ipa = all_ipas[idx] if idx < len(all_ipas) else (all_ipas[0] if all_ipas else '')
                    word_details.append({'word': p, 'ipa': ipa})
            else:
                w = clean_word(text_for_words)
                if w:
                    word_details.append({'word': w, 'ipa': ' '.join(all_ipas)})
        else:
            w = clean_word(text_for_words)
            if w:
                word_details.append({'word': w, 'ipa': ' '.join(all_ipas)})

    if not word_details:
        return None
        
    all_words = [wd['word'] for wd in word_details]
    
    if '><' in full_pre_text:
        display_word = ' >< '.join(all_words)
    elif len(all_words) > 1:
        display_word = ' = '.join(all_words)
    else:
        display_word = all_words[0]
        
    all_ipas_clean = []
    for wd in word_details:
        if wd['ipa'] and wd['ipa'] not in all_ipas_clean:
            all_ipas_clean.append(wd['ipa'])
    display_ipa = ' • '.join(all_ipas_clean) if all_ipas_clean else ''
    
    image_path = None
    if image_shapes:
        try:
            img = image_shapes[0].image
            ext = img.content_type.split('/')[-1]
            if ext == 'jpeg': ext = 'jpg'
            fname = "b%02d_w%02d.%s" % (lesson_id, word_idx, ext)
            fpath = os.path.join(IMAGES_DIR, fname)
            with open(fpath, 'wb') as f:
                f.write(img.blob)
            image_path = "images/%s" % fname
        except Exception:
            pass

    return {
        'id': f"b{lesson_id:02d}_w{word_idx:02d}",
        'word': display_word,
        'allWords': all_words,
        'wordDetails': word_details,
        'pronunciation': display_ipa,
        'partOfSpeech': pos,
        'meaning': meaning,
        'example': example_en,
        'exampleVi': example_vi,
        'image': image_path
    }


def main():
    ensure_dirs()
    pptx_files = sorted(glob.glob(os.path.join(PPTX_DIR, '*.pptx')))
    print(f"Found {len(pptx_files)} PPTX files.")
    
    lessons = []
    total_words = 0
    multi_count = 0
    
    for fpath in pptx_files:
        filename = os.path.basename(fpath)
        lesson_id = extract_lesson_number(filename)
        print(f"\nProcessing: {filename} (Lesson {lesson_id})...")
        
        prs = Presentation(fpath)
        words = []
        word_idx = 1
        
        for slide in prs.slides:
            parsed = parse_slide_thorough(slide, lesson_id, word_idx)
            if parsed:
                words.append(parsed)
                if len(parsed['allWords']) > 1:
                    multi_count += 1
                word_idx += 1
                
        print(f"  → Extracted {len(words)} words.")
        total_words += len(words)
        
        lessons.append({
            'id': lesson_id,
            'name': f"Bài {lesson_id}",
            'filename': filename,
            'wordCount': len(words),
            'words': words
        })
        
    lessons.sort(key=lambda x: x['id'])
    
    output_path = os.path.join(DATA_DIR, 'vocab.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'lessons': lessons}, f, ensure_ascii=False, indent=2)
        
    print(f"\n" + "=" * 50)
    print(f"SUCCESS!")
    print(f"Total Lessons: {len(lessons)}")
    print(f"Total Entries: {total_words}")
    print(f"Total Multi-word (Synonym/Antonym) Entries: {multi_count}")
    print(f"Saved to: {output_path}")
    print("=" * 50)


if __name__ == '__main__':
    main()
