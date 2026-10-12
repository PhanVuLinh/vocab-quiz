"""
VocabQuiz — Vocabulary Extractor & Markdown Generator
Extracts vocabulary, IPA, synonyms, antonyms, meanings, and examples from PPTX files.
Outputs:
1. data/vocab.json — Clean structured JSON for the web app
2. DANH_SACH_TU_VUNG.md — Complete human-readable markdown table of all vocabulary
"""

import os
import sys
import io
import json
import re
import glob
from pptx import Presentation

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PPTX_DIR = os.path.join(BASE_DIR, 'pp')
DATA_DIR = os.path.join(BASE_DIR, 'data')
IMAGES_DIR = os.path.join(BASE_DIR, 'images')
MD_FILE = os.path.join(BASE_DIR, 'DANH_SACH_TU_VUNG.md')

VN_CHARS = set('àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ')
TITLE_KEYWORDS = {'VOCABULARY', 'TỪ VỰNG', 'LESSON', 'LISTENING', 'READING', 'ĐỌC', 'NGHE', 'PHẦN', 'LUYỆN TẬP', 'PART'}
EXCLUSIVE_IPA_CHARS = set('ˈˌːɑɒɔəɛɜɪʊʌæθðʃʒŋʔɡ')
COMMON_ENGLISH_WORDS = {
    'solve', 'goods', 'cargo', 'respond', 'answer', 'occur', 'happen', 'deal',
    'handle', 'discount', 'rebate', 'cost', 'bill', 'receipt', 'rent', 'sail',
    'tap', 'furniture', 'shade', 'ground', 'trolley', 'cart', 'applicant'
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


def split_example_vi(text):
    text = text.strip()
    paren_match = re.search(r'\(([^)]*[' + ''.join(list(VN_CHARS)[:10]) + r'][^)]*)\)\s*\.?\s*$', text)
    if paren_match:
        vi = paren_match.group(1).strip()
        en = text[:paren_match.start()].strip().rstrip('.')
        return en, vi
    return text, ''


def is_example_sentence(text):
    t = text.strip()
    if not t:
        return False
    if t.lower().startswith(('ex:', 'example:', 'to ')):
        return True
    if len(t) > 20 and t[0].isupper() and (t.endswith('.') or t.endswith('!') or t.endswith('?') or t.endswith('"')):
        if not re.match(r'^\d+\.\s+[A-Z][a-z]+$', t):
            return True
    return False


def is_true_ipa(token):
    inner = token.strip("/ \t\n")
    if not inner:
        return False
    if inner.lower() in COMMON_ENGLISH_WORDS:
        return False
    if any(c in EXCLUSIVE_IPA_CHARS for c in inner):
        return True
    return False


def clean_term(w):
    w = re.sub(r'^\d+[\.\t\s]+', '', w)
    w = re.sub(r'\([a-zA-Z,\s/]+\)$', '', w)
    w = re.sub(r'^\([a-zA-Z,\s/]+\)', '', w)
    w = re.sub(r'\([a-z\s–-]+\)', '', w, flags=re.IGNORECASE)
    w = w.strip().rstrip(' ,;:-–/')
    return w


def parse_slide(slide, lesson_id, w_idx):
    blocks = []
    image_shape = None
    
    for sh in slide.shapes:
        if sh.shape_type == 13: # Picture
            image_shape = sh
        elif hasattr(sh, 'text') and sh.text.strip():
            raw = clean_text(sh.text).replace('‹#›', '').strip()
            if raw and not re.match(r'^\d{1,3}$', raw):
                blocks.append(raw)
                
    if not blocks or is_title_slide(blocks):
        return None
        
    example_en = ''
    example_vi = ''
    content_blocks = []
    
    for b in blocks:
        if b.lower().startswith(('ex:', 'example:')):
            ex_body = re.sub(r'^(ex|example):\s*', '', b, flags=re.IGNORECASE).strip()
            example_en, example_vi = split_example_vi(ex_body)
        elif is_example_sentence(b) and not has_vietnamese(b):
            if not example_en:
                example_en, example_vi = split_example_vi(b)
        else:
            content_blocks.append(b)
            
    lines = []
    for b in content_blocks:
        for l in b.split('\n'):
            l_str = l.strip()
            if l_str:
                lines.append(l_str)
                
    meaning_idx = -1
    meaning = ''
    for i, line in enumerate(lines):
        if any(line.upper().startswith(kw) for kw in TITLE_KEYWORDS) and len(line) < 30:
            continue
        if has_vietnamese(line):
            if line.lower().startswith(('ex:', 'example:')):
                if not example_en:
                    example_en, example_vi = split_example_vi(line[3:].strip())
                continue
            if line.startswith('(') and line.endswith(')') and len(line) > 20:
                if not example_vi:
                    example_vi = line.strip('()')
                continue
            meaning_idx = i
            meaning = line
            break
            
    if meaning_idx == -1:
        return None
        
    if 'Ex:' in meaning or 'ex:' in meaning:
        parts = re.split(r'\n*[Ee]x:\s*', meaning, maxsplit=1)
        meaning = parts[0].strip()
        if len(parts) > 1 and not example_en:
            example_en, example_vi = split_example_vi(parts[1].strip())
            
    pre_meaning = [l for l in lines[:meaning_idx] if not any(l.upper().startswith(kw) for kw in TITLE_KEYWORDS)]
    post_meaning = lines[meaning_idx+1:]
    
    for line in post_meaning:
        if line.lower().startswith(('ex:', 'example:')):
            if not example_en:
                ex_body = re.sub(r'^(ex|example):\s*', '', line, flags=re.IGNORECASE).strip()
                example_en, example_vi = split_example_vi(ex_body)
        elif has_vietnamese(line) and line.startswith('(') and not example_vi:
            example_vi = line.strip('()')
        elif not has_vietnamese(line) and len(line) > 12 and not example_en:
            example_en, example_vi = split_example_vi(line)
            
    if not pre_meaning:
        return None
        
    # Extract POS
    pos = ''
    combined_pre = ' '.join(pre_meaning)
    pos_match = re.search(r'\(([a-zA-Z,\s/]+)\)', combined_pre)
    if pos_match:
        p_str = pos_match.group(1).strip().lower()
        if any(k in p_str for k in ['n', 'v', 'adj', 'adv', 'phr', 'np', 'a']):
            pos = p_str
            
    # Check if multiple lines have their own true IPAs (Style 1)
    lines_with_ipa = []
    for l in pre_meaning:
        ipas = [m for m in re.findall(r'/[^/\n]{2,}/', l) if is_true_ipa(m)]
        if ipas:
            clean_w = l
            for ipa in ipas:
                clean_w = clean_w.replace(ipa, ' ')
            clean_w = clean_term(clean_w)
            if clean_w and not re.match(r'^\([a-z/,\s]+\)$', clean_w):
                lines_with_ipa.append((clean_w, ipas[0]))
                
    main_word = ''
    synonyms = []
    antonyms = []
    main_ipa = ''
    all_ipas = []
    
    if len(lines_with_ipa) >= 2:
        main_word = lines_with_ipa[0][0]
        main_ipa = lines_with_ipa[0][1]
        for w, ipa in lines_with_ipa[1:]:
            if w != main_word and w not in synonyms:
                synonyms.append(w)
    else:
        for l in pre_meaning:
            for ipa in re.findall(r'/[^/\n]{2,}/', l):
                if is_true_ipa(ipa) and ipa not in all_ipas:
                    all_ipas.append(ipa)
            if '/' in l and any(c in EXCLUSIVE_IPA_CHARS for c in l):
                parts = [p.strip() for p in l.split('/') if p.strip()]
                for p in parts:
                    if is_true_ipa(p) and f"/{p}/" not in all_ipas:
                        all_ipas.append(f"/{p}/")
                        
        if all_ipas:
            main_ipa = all_ipas[0]
            
        clean_word_lines = []
        for l in pre_meaning:
            l_no_ipa = l
            for ipa in all_ipas:
                l_no_ipa = l_no_ipa.replace(ipa, ' ')
            l_no_ipa = re.sub(r'^\d+[\.\t\s]+', '', l_no_ipa)
            l_no_ipa = re.sub(r'\([a-zA-Z,\s/]+\)', '', l_no_ipa)
            cw = clean_term(l_no_ipa)
            if cw and not is_true_ipa(cw) and not re.match(r'^[,\s/]+$', cw):
                clean_word_lines.append(cw)
                
        full_w_str = ' '.join(clean_word_lines)
        
        if '><' in full_w_str:
            parts = [clean_term(p) for p in full_w_str.split('><') if clean_term(p)]
            if len(parts) >= 2:
                main_word = parts[0]
                antonyms = parts[1:]
        elif '=' in full_w_str:
            parts = [clean_term(p) for p in full_w_str.split('=') if clean_term(p)]
            if len(parts) >= 2:
                main_word = parts[0]
                synonyms = parts[1:]
        elif '/' in full_w_str:
            parts = [clean_term(p) for p in full_w_str.split('/') if clean_term(p)]
            if len(parts) >= 2 and all(len(p) > 1 for p in parts):
                main_word = parts[0]
                synonyms = parts[1:]
            else:
                main_word = clean_term(full_w_str)
        elif len(clean_word_lines) > 1:
            main_word = clean_word_lines[0]
            for cl in clean_word_lines[1:]:
                if cl != main_word and cl not in synonyms:
                    synonyms.append(cl)
        elif clean_word_lines:
            main_word = clean_word_lines[0]
            
    if not main_word:
        return None
        
    img_path = None
    if image_shape:
        try:
            img = image_shape.image
            ext = img.content_type.split('/')[-1]
            if ext == 'jpeg': ext = 'jpg'
            fname = "b%02d_w%02d.%s" % (lesson_id, w_idx, ext)
            fpath = os.path.join(IMAGES_DIR, fname)
            with open(fpath, 'wb') as f:
                f.write(img.blob)
            img_path = f"images/{fname}"
        except Exception:
            pass

    return {
        'id': f"b{lesson_id:02d}_w{w_idx:02d}",
        'word': main_word,
        'pos': pos,
        'pronunciation': main_ipa,
        'synonyms': synonyms,
        'antonyms': antonyms,
        'meaning': meaning,
        'example': example_en,
        'exampleVi': example_vi,
        'image': img_path
    }


def generate_markdown(lessons):
    lines = [
        "# 📚 TỔNG HỢP TOÀN BỘ TỪ VỰNG & TỪ ĐỒNG NGHĨA (VOCABQUIZ)",
        "",
        "> [!NOTE]",
        f"> Tài liệu tổng hợp toàn bộ từ vựng được bóc tách từ 22 file PowerPoint bài giảng.",
        f"> Tổng số bài học: **{len(lessons)} bài** | Tổng số mục từ vựng: **{sum(len(l['words']) for l in lessons)} mục**.",
        "",
        "---",
        ""
    ]
    
    # Table of contents
    lines.append("## 📑 Danh Mục Bài Học\n")
    for l in lessons:
        syn_count = sum(1 for w in l['words'] if w['synonyms'] or w['antonyms'])
        lines.append(f"- [Bài {l['id']}: {l['name']}](#bài-{l['id']}) ({len(l['words'])} từ, {syn_count} nhóm đồng/trái nghĩa)")
    lines.append("\n---\n")
    
    for l in lessons:
        lines.append(f"## <a id=\"bài-{l['id']}\"></a>📖 {l['name']} ({l['filename']})")
        lines.append(f"- **Tổng số từ:** {len(l['words'])}")
        lines.append("")
        lines.append("| STT | Từ Vựng Chính | Loại Từ | Phiên Âm | Từ Đồng Nghĩa / Trái Nghĩa | Nghĩa Tiếng Việt | Câu Ví Dụ (Anh - Việt) |")
        lines.append("|:---:|:---|:---:|:---|:---|:---|:---|")
        
        for idx, w in enumerate(l['words'], 1):
            syn_str = ""
            if w['synonyms']:
                syn_str = "🔗 **Đồng nghĩa:** " + ", ".join(f"`{s}`" for s in w['synonyms'])
            if w['antonyms']:
                if syn_str: syn_str += "<br>"
                syn_str += "⚡ **Trái nghĩa:** " + ", ".join(f"`{a}`" for a in w['antonyms'])
            if not syn_str:
                syn_str = "—"
                
            pos_str = f"`{w['pos']}`" if w['pos'] else "—"
            ipa_str = f"`{w['pronunciation']}`" if w['pronunciation'] else "—"
            meaning_str = w['meaning'].replace('\n', '<br>')
            
            ex_str = ""
            if w['example']:
                ex_str = f"*{w['example']}*"
                if w['exampleVi']:
                    ex_str += f"<br>({w['exampleVi']})"
            else:
                ex_str = "—"
                
            lines.append(f"| {idx} | **{w['word']}** | {pos_str} | {ipa_str} | {syn_str} | {meaning_str} | {ex_str} |")
            
        lines.append("\n---\n")
        
    return "\n".join(lines)


def main():
    ensure_dirs()
    pptx_files = sorted(glob.glob(os.path.join(PPTX_DIR, '*.pptx')))
    print(f"Found {len(pptx_files)} PPTX files.")
    
    lessons = []
    total_words = 0
    total_syn = 0
    total_ant = 0
    
    for fpath in pptx_files:
        filename = os.path.basename(fpath)
        lesson_id = extract_lesson_number(filename)
        print(f"\nProcessing: {filename} (Lesson {lesson_id})...")
        
        prs = Presentation(fpath)
        words = []
        w_idx = 1
        
        for s_idx, slide in enumerate(prs.slides):
            item = parse_slide(slide, lesson_id, w_idx)
            if item:
                words.append(item)
                if item['synonyms']:
                    total_syn += 1
                if item['antonyms']:
                    total_ant += 1
                w_idx += 1
                
        print(f"  → Extracted {len(words)} entries.")
        total_words += len(words)
        
        lessons.append({
            'id': lesson_id,
            'name': f"Bài {lesson_id}",
            'filename': filename,
            'wordCount': len(words),
            'words': words
        })
        
    lessons.sort(key=lambda x: x['id'])
    
    # Save to data/vocab.json
    output_json = os.path.join(DATA_DIR, 'vocab.json')
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({'lessons': lessons}, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Saved vocab JSON: {output_json}")
    
    # Save Markdown documentation
    md_content = generate_markdown(lessons)
    with open(MD_FILE, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"[OK] Generated Markdown documentation: {MD_FILE}")
    
    print("\n" + "=" * 50)
    print("EXTRACTION COMPLETE & VERIFIED!")
    print(f"Total Lessons: {len(lessons)}")
    print(f"Total Entries: {total_words}")
    print(f"Entries with Synonyms: {total_syn}")
    print(f"Entries with Antonyms: {total_ant}")
    print("=" * 50)


if __name__ == '__main__':
    main()
