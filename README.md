# 📚 VocabQuiz — Học Từ Vựng Tiếng Anh Thông Minh

Ứng dụng web học từ vựng tiếng Anh tương tác từ các slide bài giảng PowerPoint (PPTX), hỗ trợ Flashcard, Quiz trắc nghiệm, Điền từ, Nối từ và Nghe chọn, tối ưu hóa cho việc tự học cá nhân và deploy miễn phí lên GitHub Pages.

![VocabQuiz Demo](https://raw.githubusercontent.com/placeholder-demo.png)

---

## ✨ Tính Năng Nổi Bật

- **📖 Flashcard Thông Minh**: Thẻ lật 3D mượt mà, hiển thị từ vựng, phiên âm IPA, hình ảnh minh hoạ, nghĩa tiếng Việt và câu ví dụ thực tế.
- **🔊 Phát Âm Tự Động (TTS)**: Tích hợp Web Speech API chuẩn giọng Anh/Mỹ không cần API key.
- **🎯 4 Chế Độ Quiz Tương Tác**:
  - **Anh → Việt**: Đọc từ tiếng Anh, chọn nghĩa tiếng Việt (4 đáp án).
  - **Việt → Anh**: Đọc nghĩa tiếng Việt, chọn từ tiếng Anh tương ứng.
  - **🎧 Nghe & Chọn**: Luyện phản xạ nghe phát âm rồi chọn nghĩa đúng.
  - **⌨️ Điền Từ (Typing)**: Tự gõ từ tiếng Anh theo nghĩa với gợi ý thông minh (thuật toán Levenshtein distance).
  - **🔗 Nối Từ (Matching)**: Ghép cặp từ vựng và nghĩa tiếng Việt với đồng hồ bấm giờ tính điểm.
- **⭐ Lưu Từ Đánh Dấu**: Đánh dấu các từ vựng khó để ôn tập riêng biệt bất cứ lúc nào.
- **📊 Theo Dõi Tiến Độ**: Lưu lịch sử học, tỷ lệ chính xác (%) và chuỗi ngày học liên tục (Streak 🔥) trực tiếp trên `localStorage` (không cần server backend hay đăng ký tài khoản).
- **🌙 Giao Diện Hiện Đại**: Thiết kế chuẩn Dark Mode & Light Mode sang trọng, Glassmorphism, Responsive tối ưu cho cả máy tính và điện thoại.

---

## 📁 Cấu Trúc Dự Án

```text
tu_vung/
├── css/
│   └── style.css            # Toàn bộ CSS (Variables, Theme, Animations, Responsive)
├── data/
│   └── vocab.json           # Dữ liệu từ vựng trích xuất từ 22 bài PPTX (519 từ)
├── images/                  # Hình ảnh minh họa trích xuất từ slide bài giảng
├── js/
│   └── app.js               # Logic ứng dụng (Router, Flashcard, Quiz, Typing, Matching, Audio)
├── pp/                      # Thư mục chứa file PPTX gốc (được bỏ qua trong .gitignore)
├── scripts/
│   └── extract_vocab.py     # Script Python tự động bóc tách từ vựng & hình ảnh từ PPTX
├── .gitignore
├── index.html               # Trang chính ứng dụng
└── README.md
```

---

## 🚀 Hướng Dẫn Chạy Cục Bộ (Local)

Dự án là Single Page Application tĩnh thuần (HTML/CSS/JS thuần), không cần cài đặt node_modules hay build tool phức tạp:

1. **Dùng Python HTTP Server**:
   ```bash
   # Mở terminal tại thư mục dự án tu_vung:
   python -m http.server 8080
   ```
   Mở trình duyệt truy cập: `http://localhost:8080`

2. **Hoặc dùng Live Server trong VS Code**:
   - Cài extension **Live Server** trong VS Code
   - Chuột phải vào `index.html` → Chọn **Open with Live Server**

---

## 🌐 Hướng Dẫn Deploy Lên GitHub Pages (Miễn Phí)

Website được thiết kế hoàn toàn tĩnh và sử dụng hash routing (`#/lesson/1`, `#/flashcard`), rất thích hợp để host miễn phí trên GitHub Pages:

### Bước 1: Khởi tạo Git và Commit
```bash
git init
git add .
git commit -m "feat: initial commit VocabQuiz app"
```

### Bước 2: Tạo Repository trên GitHub
1. Truy cập [GitHub](https://github.com/new) và tạo một repository mới (ví dụ: `vocab-quiz` hoặc `tu-vung`).
2. Chọn chế độ **Public** hoặc **Private** tuỳ nhu cầu.

### Bước 3: Đẩy code lên GitHub
```bash
git branch -M main
git remote add origin https://github.com/<username>/<repo-name>.git
git push -u origin main
```

### Bước 4: Bật GitHub Pages
1. Vào repository trên GitHub → Chọn tab **Settings**.
2. Chọn mục **Pages** ở thanh menu bên trái.
3. Tại phần **Build and deployment > Branch**:
   - Chọn nhánh **`main`**
   - Thư mục: chọn **`/ (root)`**
   - Bấm **Save**.
4. Chờ 1–2 phút, trang web của bạn sẽ hoạt động tại địa chỉ:
   `https://<username>.github.io/<repo-name>/`

---

## 🔄 Cách Thêm Bài Học Mới Từ File PPTX

Khi có thêm file PowerPoint từ vựng mới:
1. Sao chép file `.pptx` mới vào thư mục `pp/`.
2. Chạy lệnh trích xuất:
   ```bash
   python scripts/extract_vocab.py
   ```
3. Script sẽ tự động nhận diện định dạng slide, trích xuất từ vựng, hình ảnh và cập nhật lại `data/vocab.json`.
4. Commit và push lên GitHub để cập nhật trang web trực tiếp!

---

## 🛠️ Công Nghệ Sử Dụng

- **Frontend**: HTML5, Vanilla CSS3 (Custom Properties, Flexbox, Grid, 3D Transforms), Vanilla JavaScript (ES6+).
- **Dữ liệu**: JSON, Python (`python-pptx`, `Pillow`) bóc tách dữ liệu tự động.
- **Audio**: Web Speech Synthesis API (`window.speechSynthesis`).
- **Lưu trữ**: Browser LocalStorage.
