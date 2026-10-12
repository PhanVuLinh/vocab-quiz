import json
import os

with open('data/vocab.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

data['totalLessons'] = len(data['lessons'])
data['totalWords'] = sum(len(l['words']) for l in data['lessons'])

# Re-save vocab.json without BOM for clean web loading
with open('data/vocab.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

lines = []
lines.append("# 📚 TỔNG HỢP TOÀN BỘ TỪ VỰNG & TỪ ĐỒNG NGHĨA (VOCABQUIZ)\n")
lines.append("> [!NOTE]")
lines.append("> Tài liệu tổng hợp toàn bộ từ vựng được bóc tách từ 22 file PowerPoint bài giảng.")
lines.append(f"> Tổng số bài học: **{data['totalLessons']} bài** | Tổng số mục từ vựng: **{data['totalWords']} mục**.\n")
lines.append("---\n")
lines.append("## 📑 Danh Mục Bài Học\n")

for lesson in data['lessons']:
    syn_count = sum(1 for w in lesson['words'] if w.get('synonyms') or w.get('antonyms'))
    group_str = f"{syn_count} nhóm đồng/trái nghĩa" if syn_count > 0 else "0 nhóm đồng/trái nghĩa"
    lines.append(f"- [Bài {lesson['id']}: {lesson['name']}](#bài-{lesson['id']}) ({lesson['wordCount']} từ, {group_str})")

lines.append("\n---\n")

for lesson in data['lessons']:
    lines.append(f"## <a id=\"bài-{lesson['id']}\"></a>📖 Bài {lesson['id']} ({lesson['filename']})")
    lines.append(f"- **Tổng số từ:** {lesson['wordCount']}\n")
    lines.append("| STT | Từ Vựng Chính | Loại Từ | Phiên Âm | Từ Đồng Nghĩa / Trái Nghĩa | Nghĩa Tiếng Việt | Câu Ví Dụ (Anh - Việt) |")
    lines.append("|:---:|:---|:---:|:---|:---|:---|:---|")
    
    for idx, w in enumerate(lesson['words'], 1):
        word_col = f"**{w['word']}**"
        pos_col = f"`{w['pos']}`" if w.get('pos') else "—"
        ipa_col = f"`{w['pronunciation']}`" if w.get('pronunciation') else "—"
        
        rel_parts = []
        if w.get('synonyms'):
            syn_str = ", ".join(f"`{s}`" for s in w['synonyms'])
            rel_parts.append(f"🔗 **Đồng nghĩa:** {syn_str}")
        if w.get('antonyms'):
            ant_str = ", ".join(f"`{a}`" for a in w['antonyms'])
            rel_parts.append(f"⚡ **Trái nghĩa:** {ant_str}")
        rel_col = "<br>".join(rel_parts) if rel_parts else "—"
        
        meaning_clean = w.get('meaning', '—').replace('|', '\\|').replace('\n', '<br>')
        
        ex_parts = []
        if w.get('example'):
            ex_parts.append(f"*{w['example']}*")
        if w.get('exampleVi'):
            ex_vi = w['exampleVi']
            if not ex_vi.startswith('('):
                ex_vi = f"({ex_vi})"
            ex_parts.append(ex_vi)
        ex_col = "<br>".join(ex_parts) if ex_parts else "—"
        
        lines.append(f"| {idx} | {word_col} | {pos_col} | {ipa_col} | {rel_col} | {meaning_clean} | {ex_col} |")
        
    lines.append("\n---\n")

md_content = "\n".join(lines)
with open('DANH_SACH_TU_VUNG.md', 'w', encoding='utf-8') as f:
    f.write(md_content)

print("SUCCESS: Generated DANH_SACH_TU_VUNG.md with", len(data['lessons']), "lessons")
