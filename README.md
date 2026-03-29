# RMTK VN — Từ điển Kanji Hán-Việt

Từ điển Kanji Hán-Việt dựa trên phương pháp **Remembering the Kanji** (RTK) của James Heisig, với toàn bộ nội dung được dịch sang tiếng Việt.

## Tính năng

-  **Tìm kiếm thông minh** — Tìm theo từ khóa tiếng Việt, Hán-Việt, số frame, hoặc dán trực tiếp chữ Kanji
-  **3030 Kanji** — 2200 Kanji RTK1 + 830 Kanji RTK3 bổ sung
-  **Hán-Việt** — Âm Hán-Việt cho mỗi chữ Kanji
-  **Stroke Animation** — Xem thứ tự nét viết cho mỗi chữ Kanji
-  **Câu chuyện Koohii** — Câu chuyện ghi nhớ từ cộng đồng, đã dịch sang tiếng Việt
-  **Phím tắt** — Nhấn `/` để tìm kiếm, `↑↓` để chọn, `Enter` để mở
-  **Dark Mode** — Giao diện tối, hiện đại

## Chạy local

```bash
# Clone repo
git clone https://github.com/Narcolepsyy/rmtk_vn.git
cd rmtk_vn

# Cài Jekyll (nếu chưa có)
gem install jekyll

# Chạy
./serve.sh
# Hoặc
jekyll serve --port 4000 --host 127.0.0.1 --livereload
```

Mở trình duyệt tại `http://127.0.0.1:4000`

## Cấu trúc thư mục

```
├── rtk1-v6/          # 2200 Kanji RTK1 (markdown)
├── rtk3-remain/      # 830 Kanji RTK3 (markdown)
├── kanjivg/           # SVG stroke data (KanjiVG)
├── assets/
│   ├── css/           # SCSS styles
│   └── js/            # Search engine + app logic
├── _layouts/          # Jekyll layouts
├── _includes/         # Jekyll includes (post.json)
├── _pipeline/         # Data processing scripts
├── _config.yml        # Jekyll config
└── index.html         # Homepage + search
```

##  Giấy phép

- Nội dung Kanji: [Remembering the Kanji](https://en.wikipedia.org/wiki/Remembering_the_Kanji_and_Remembering_the_Hanzi) by James Heisig
- Stroke data: [KanjiVG](http://kanjivg.tagaini.net/) — Creative Commons Attribution-Share Alike 3.0
- Câu chuyện: [Kanji Koohii](https://kanji.koohii.com/)
- Code: MIT License

##  Credits

- [Học hành](http://hochanh.github.io) — Tác giả gốc
- Bản dịch tiếng Việt bằng GPT-4.1-mini (OpenAI Batch API)
