"""
transfer_scraper.py - Thu thập giá chuyển nhượng cầu thủ từ footballtransfers.com
Mùa 2024-2025

Phương pháp:
1. Với mỗi cầu thủ từ database, tạo URL slug từ tên
2. Truy cập trang profile trên footballtransfers.com
3. Lấy ETV (Estimated Transfer Value) 
4. Nếu không tìm thấy → N/a
5. Lưu vào bảng transfer_values trong SQLite

Xử lý anti-bot:
- Random delay 2-4s giữa các request
- User-Agent header hợp lệ
- Retry khi gặp lỗi mạng
"""

import os
import sys
import re
import time
import random
import unicodedata

import requests
from bs4 import BeautifulSoup

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    FT_BASE_URL, FT_PLAYER_URL,
    FT_REQUEST_DELAY_MIN, FT_REQUEST_DELAY_MAX,
    REQUEST_HEADERS, MAX_RETRIES
)
from database.db_manager import DatabaseManager


def normalize_name(name):
    """
    Chuẩn hóa tên cầu thủ: bỏ dấu, chuyển thường, thay space bằng dấu gạch.
    Ví dụ: 'Mohamed Salah' -> 'mohamed-salah'
           'Trent Alexander-Arnold' -> 'trent-alexander-arnold'
    """
    # Bỏ dấu tiếng nước ngoài (é -> e, ü -> u, etc.)
    normalized = unicodedata.normalize("NFKD", name)
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))

    # Chuyển thường, bỏ ký tự đặc biệt
    normalized = normalized.lower().strip()
    normalized = re.sub(r"[^a-z0-9\s-]", "", normalized)
    normalized = re.sub(r"[\s]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized)
    normalized = normalized.strip("-")

    return normalized


def parse_etv(etv_text):
    """
    Parse giá trị ETV từ text sang số.
    Ví dụ: '€48.2M' -> 48200000.0
           '€500K' -> 500000.0
           '€1.5B' -> 1500000000.0
    """
    if not etv_text or etv_text == "N/a":
        return None

    # Bỏ ký tự tiền tệ
    text = etv_text.replace("€", "").replace("$", "").replace("£", "").strip()

    try:
        if text.upper().endswith("B"):
            return float(text[:-1]) * 1_000_000_000
        elif text.upper().endswith("M"):
            return float(text[:-1]) * 1_000_000
        elif text.upper().endswith("K"):
            return float(text[:-1]) * 1_000
        else:
            return float(text.replace(",", ""))
    except (ValueError, TypeError):
        return None


class TransferScraper:
    """Thu thập giá chuyển nhượng từ footballtransfers.com"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(REQUEST_HEADERS)
        self.results = []

    def _random_delay(self):
        """Chờ ngẫu nhiên."""
        delay = random.uniform(FT_REQUEST_DELAY_MIN, FT_REQUEST_DELAY_MAX)
        print(f"  ⏳ Chờ {delay:.1f}s...")
        time.sleep(delay)

    def _get_page(self, url, retry_count=0):
        """Lấy nội dung trang web."""
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 404:
                return None  # Cầu thủ không tồn tại
            elif resp.status_code == 429:
                # Rate limited
                wait = 30 * (retry_count + 1)
                print(f"  ⚠️ Rate limited. Chờ {wait}s...")
                time.sleep(wait)
                if retry_count < MAX_RETRIES:
                    return self._get_page(url, retry_count + 1)
            else:
                print(f"  ❌ HTTP {resp.status_code}: {url}")
                if retry_count < MAX_RETRIES:
                    time.sleep(10)
                    return self._get_page(url, retry_count + 1)
        except requests.RequestException as e:
            print(f"  ❌ Lỗi request: {e}")
            if retry_count < MAX_RETRIES:
                time.sleep(10)
                return self._get_page(url, retry_count + 1)
        return None

    def _search_player(self, player_name):
        """
        Tìm kiếm cầu thủ trên footballtransfers.com.
        Trả về URL profile nếu tìm thấy, None nếu không.
        """
        # Phương pháp 1: Tạo URL trực tiếp từ slug
        slug = normalize_name(player_name)
        direct_url = f"{FT_PLAYER_URL}/{slug}"
        html = self._get_page(direct_url)
        if html:
            return direct_url, html

        # Phương pháp 2: Thử các biến thể slug
        # Đôi khi tên đầy đủ vs tên viết tắt khác nhau
        name_parts = player_name.split()
        if len(name_parts) >= 2:
            # Thử chỉ dùng tên + họ (bỏ tên đệm)
            short_name = f"{name_parts[0]}-{name_parts[-1]}"
            alt_url = f"{FT_PLAYER_URL}/{normalize_name(short_name)}"
            self._random_delay()
            html = self._get_page(alt_url)
            if html:
                return alt_url, html

        # Phương pháp 3: Dùng Google Search (fallback)
        # Có thể cân nhắc thêm sau

        return None, None

    def scrape_player_etv(self, player_name, team):
        """
        Thu thập ETV của 1 cầu thủ.
        
        Returns: dict với keys: player_name, team, transfer_value, etv_numeric, source_url
        """
        print(f"  🔍 Tìm {player_name} ({team})...", end=" ")

        url, html = self._search_player(player_name)

        if not html:
            print("❌ Không tìm thấy")
            return {
                "player_name": player_name,
                "team": team,
                "transfer_value": "N/a",
                "etv_numeric": None,
                "source_url": "N/a",
            }

        # Parse ETV từ HTML
        soup = BeautifulSoup(html, "lxml")
        
        etv_text = "N/a"
        etv_numeric = None
        
        # Tìm ETV trong raw HTML
        matches = re.findall(r'€\s*[0-9.]+\s*[MKBmkb]', html)
        if matches:
            etv_text = matches[0]
            etv_numeric = parse_etv(etv_text)

        if etv_numeric:
            print(f"✅ {etv_text}")
        else:
            print(f"⚠️ Không thể parse ETV từ nội dung trang")
            etv_text = "N/a"

        return {
            "player_name": player_name,
            "team": team,
            "transfer_value": etv_text,
            "etv_numeric": etv_numeric,
            "source_url": url or "N/a",
        }

    def scrape_all_from_database(self):
        """
        Thu thập ETV cho tất cả cầu thủ trong database song song bằng TheadPool.
        """
        import concurrent.futures
        from sys import stdout

        print("=" * 70)
        print("💰 BẮT ĐẦU THU THẬP GIÁ CHUYỂN NHƯỢNG (SIÊU TỐC ĐỘ)")
        print("=" * 70)

        with DatabaseManager() as db:
            players = db.get_player_names_and_teams()
            print(f"📋 Tổng cầu thủ cần tìm: {len(players)}")

            db.create_transfer_values_table()

            # Hàm tải từng cầu thủ
            def _task(player_args):
                name, club = player_args
                return self.scrape_player_etv(name, club)

            # Chạy song song tốc độ cao với 15 luồng
            completed = 0
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                futures = {executor.submit(_task, p): p for p in players}
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    self.results.append(result)
                    completed += 1
                    
                    stdout.write(f"\r  [Tiến độ] {completed}/{len(players)} cầu thủ... ")
                    stdout.flush()

                    # Lưu ngay vào database
                    db.insert_transfer_value(
                        player_name=result["player_name"],
                        club=result["team"], 
                        transfer_value=result["transfer_value"],
                        etv_numeric=result["etv_numeric"],
                        source_url=result["source_url"],
                    )

        # Thống kê kết quả
        found = sum(1 for r in self.results if r["etv_numeric"] is not None)
        not_found = len(self.results) - found
        print(f"\n\n{'='*70}")
        print(f"✅ HOÀN TẤT SIÊU NHANH!")
        print(f"   Tìm thấy ETV: {found}/{len(self.results)}")
        print(f"   Không tìm thấy: {not_found}/{len(self.results)}")
        print(f"{'='*70}")


def main():
    """Chạy transfer scraper."""
    scraper = TransferScraper()
    scraper.scrape_all_from_database()


if __name__ == "__main__":
    main()
