# Mắt Xích Vốn — Hệ thống nhật ký dòng chảy vốn toàn cầu, tự động 100%

Đây là một hệ thống **thật, độc lập**, tự động chạy mỗi ngày mà không cần bạn mở máy tính hay mở Claude.
Nó dùng **GitHub Actions** (miễn phí) làm "đồng hồ báo thức" — mỗi sáng tự động đi lấy dữ liệu từ nhiều nguồn,
dựng thành một trang web, và xuất bản lên **GitHub Pages** (cũng miễn phí, có địa chỉ web thật).

## Cách hoạt động (không cần hiểu code)

```
6h00 sáng mỗi ngày → GitHub tự "đánh thức" hệ thống
   → Lấy số liệu Fed/lãi suất (FRED)
   → Lấy chỉ số chứng khoán toàn cầu (Finnhub)
   → Lấy giá crypto (CoinGecko)
   → Lấy VN-Index (vnstock)
   → Lấy tin tức (RSS)
   → Dựng thành 1 trang web
   → Tự động cập nhật lên địa chỉ web của bạn
```

Bạn chỉ cần mở link mỗi sáng — dữ liệu đã sẵn sàng.

## Triển khai — 6 bước (khoảng 20-30 phút, làm 1 lần duy nhất)

### Bước 1 — Tạo tài khoản GitHub (nếu chưa có)
Vào https://github.com/signup — miễn phí.

### Bước 2 — Tạo repository mới
- Bấm "New repository"
- Đặt tên (vd: `mat-xich-von`)
- Chọn **Public** (để dùng GitHub Pages miễn phí) hoặc Private (cần gói trả phí cho Pages)
- Bấm "Create repository"

### Bước 3 — Tải toàn bộ thư mục này lên repository
Cách dễ nhất: kéo-thả toàn bộ các file/thư mục trong gói này vào giao diện web GitHub
("Add file" → "Upload files"), giữ nguyên cấu trúc thư mục.

### Bước 4 — Đăng ký API key miễn phí (3 nơi, mỗi nơi ~2 phút)
| Nguồn | Đăng ký tại | Ghi chú |
|---|---|---|
| FRED | https://fred.stlouisfed.org/docs/api/api_key.html | Miễn phí, không giới hạn |
| Finnhub | https://finnhub.io/register | Miễn phí, 60 request/phút |
| CoinGecko | https://www.coingecko.com/en/api | Miễn phí, gói Demo |

### Bước 5 — Lưu API key vào GitHub Secrets (bảo mật, không lộ ra ngoài)
Trong repository → **Settings → Secrets and variables → Actions → New repository secret**
Thêm lần lượt 3 secret:
- `FRED_API_KEY`
- `FINNHUB_API_KEY`
- `COINGECKO_API_KEY`

### Bước 6 — Bật GitHub Pages
Repository → **Settings → Pages** → chọn nhánh `main`, thư mục `/docs` → Save.
Sau vài phút, GitHub cho bạn 1 link dạng `https://<tên-bạn>.github.io/mat-xich-von/`

### Chạy thử ngay (không cần đợi 6h sáng)
Vào tab **Actions** trong repository → chọn workflow "Cập nhật Nhật ký Vốn hằng ngày" → **Run workflow**.
Sau ~1-2 phút, kiểm tra thư mục `docs/index.html` đã được cập nhật, và link Pages đã sống.

## Cấu trúc thư mục

```
mat-xich-von/
├── .github/workflows/daily-update.yml   ← "đồng hồ báo thức" tự động
├── scripts/
│   ├── fetch_fred.py        ← vĩ mô Mỹ (Fed, CPI, lợi suất)
│   ├── fetch_finnhub.py     ← chỉ số toàn cầu (CK, FX, hàng hóa qua ETF proxy)
│   ├── fetch_crypto.py      ← BTC, ETH, SOL
│   ├── fetch_vnstock.py     ← VN-Index
│   ├── fetch_news_rss.py    ← tin tức
│   └── build_site.py        ← dựng trang HTML từ dữ liệu
├── data/                     ← dữ liệu thô mỗi ngày (JSON, tự lưu lịch sử qua git)
├── docs/                     ← trang web tĩnh (GitHub Pages đọc từ đây)
└── requirements.txt
```

## Việc cần làm tiếp (Giai đoạn 2 trở đi — chưa có trong gói này)
- Ma trận liên kết & Risk Regime Score (cần dữ liệu chạy vài tuần để hiệu chỉnh)
- Lớp phân tích Claude sinh "macro_analysis.md" mỗi sáng (cần gọi Anthropic API riêng, có phí theo dung lượng)
- Module dầu, đồng, JPY, CNY, BĐS VN, VIX (mở rộng thêm scripts tương tự các file hiện có)
- Dashboard đầy đủ giao diện đẹp như bản artifact đã duyệt (hiện tại `build_site.py` đang ở bản tối giản — có thể nâng cấp giao diện sau khi dữ liệu chạy ổn định)

## Vì sao không dùng Claude Cowork làm lõi hệ thống này?
Cowork chạy trong phiên làm việc có giới hạn thời lượng, phù hợp cho việc **phân tích sâu theo yêu cầu** —
không phù hợp để là "hạ tầng nền" chạy bền bỉ mỗi ngày không cần giám sát. GitHub Actions mới là đúng công cụ
cho phần "xương sống tự động". Cowork nên được dùng như **lớp phân tích cấp cao phía trên** hệ thống này khi
cần: bạn đưa dữ liệu JSON mới nhất vào Cowork/Claude, yêu cầu viết phân tích dòng chảy sâu, rồi dán ngược vào
trang web (thủ công lúc đầu, tự động hoá sau qua Anthropic API nếu cần).
