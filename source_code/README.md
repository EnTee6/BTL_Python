# Phân Tích Cầu Thủ Ngoại Hạng Anh 2024-2025

## Mô tả
Dự án thu thập, lưu trữ, tra cứu và phân tích dữ liệu cầu thủ bóng đá Ngoại Hạng Anh mùa 2024-2025.

## Cấu trúc thư mục
```
source_code/
├── config.py                    # Cấu hình chung
├── requirements.txt             # Dependencies
├── README.md                    # File này
├── scraper/
│   ├── fbref_scraper.py         # Thu thập dữ liệu từ FBRef.com
│   └── transfer_scraper.py      # Thu thập giá chuyển nhượng
├── database/
│   ├── db_manager.py            # Quản lý SQLite database
│   └── premier_league.db        # Database (tạo tự động)
├── api/
│   ├── app.py                   # Flask REST API
│   └── lookup.py                # CLI tra cứu
├── analysis/
│   ├── statistics.py            # Thống kê theo đội
│   ├── valuation.py             # Mô hình định giá
│   └── clustering.py            # K-means & PCA
└── output/                      # Kết quả (CSV, biểu đồ)
```

## Cài đặt

```bash
pip install -r requirements.txt
```

## Hướng dẫn sử dụng

### Cách nhanh nhất: Tự động hoá bằng script (Khuyên dùng)
Dự án đã được tích hợp sẵn một script tự động chạy từ A-Z. Tại thư mục gốc của Terminal, bạn gõ 2 lệnh sau:
```bash
cd source_code
.\run_all.bat
```
Script sẽ cung cấp menu để bạn chọn chạy lại cào dữ liệu hay chỉ chạy phân tích, tự động trích xuất các biểu đồ và khởi động luôn API server.

---

### Hoặc chạy thủ công từng bước:

### Bước 1: Thu thập dữ liệu từ FBRef (Phần I.1)
```bash
# Scrape tất cả 20 đội (mất ~30-60 phút)
python scraper/fbref_scraper.py

# Hoặc test với 1 đội
python scraper/fbref_scraper.py --team Liverpool

# Bắt buộc dùng Selenium (nếu requests bị chặn)
python scraper/fbref_scraper.py --selenium
```

### Bước 2: Thu thập giá chuyển nhượng (Phần I.2)
```bash
python scraper/transfer_scraper.py
```

### Bước 3: Khởi chạy Flask API (Phần II.1)
```bash
python api/app.py
```
API Endpoints:
- `GET /api/players?name=<tên>` - Tra cứu theo tên cầu thủ
- `GET /api/clubs?club=<CLB>` - Tra cứu theo câu lạc bộ
- `GET /api/teams` - Danh sách các đội

### Bước 4: Tra cứu CLI (Phần II.2)
```bash
# Đảm bảo Flask server đang chạy (bước 3)
python api/lookup.py --name "Mohamed Salah"
python api/lookup.py --club "Liverpool"
```

### Bước 5: Phân tích thống kê (Phần III.1)
```bash
python analysis/statistics.py
```

### Bước 6: Mô hình định giá (Phần III.2)
```bash
python analysis/valuation.py
```

### Bước 7: Phân cụm K-means & PCA (Phần III.3)
```bash
python analysis/clustering.py
```

## Xử lý vấn đề anti-bot

### FBRef.com
- **Cloudflare CAPTCHA**: Dùng `undetected-chromedriver` khi bật Selenium (mặc định). Có thể tắt bằng `USE_UNDETECTED_CHROMEDRIVER=false`
- **Rate Limit**: Delay ngẫu nhiên 5-10s giữa các request
- **Retry**: Tự động retry 3 lần khi gặp lỗi
- **CAPTCHA thủ công**: Nếu cần, giải CAPTCHA trong cửa sổ trình duyệt Selenium

### FootballTransfers.com
- **Rate Limit**: Delay 2-4s giữa các request
- **404**: Tự động thử các biến thể tên cầu thủ

## Kết quả đầu ra
- `database/premier_league.db` - Database SQLite
- `output/team_statistics.csv` - Thống kê theo đội
- `output/best_teams_per_stat.csv` - Đội tốt nhất mỗi chỉ số
- `output/player_clusters.csv` - Kết quả phân cụm
- `output/feature_importance.csv` - Độ quan trọng features
- `output/elbow_silhouette.png` - Biểu đồ Elbow & Silhouette
- `output/pca_2d_scatter.png` - PCA 2D
- `output/pca_3d_scatter.png` - PCA 3D
- `output/model_comparison.png` - So sánh mô hình
- `output/feature_importance.png` - Feature importance chart
