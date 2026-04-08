import os
import sys
import re
import time
import random
import json
import pickle
from collections import defaultdict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_HEADERS, MIN_MINUTES_PLAYED, BASE_DIR
from database.db_manager import DatabaseManager

COOKIES_PATH = os.path.join(BASE_DIR, "output", "fbref_cookies.pkl")

# Mapping data-stat từ FBRef thành tên cột của user
COLUMN_MAPPING = {
    'player': 'player_name',
    'team': 'club',          # Ở bảng tổng, trang web gọi là 'team' or 'squad'
    'squad': 'club',
    'position': 'position',
    'age': 'age',
    'birth_year': 'birth_year',
    'games': 'matches_played',
    'minutes': 'minutes_played',
    'goals': 'goals',
    'assists': 'assists',
    'goals_assists': 'goals_assists',
    'goals_pens': 'goals_no_penalty',
    'pens_made': 'penalties',
    'pens_att': 'penalties_attempted',
    'xg': 'xg',
    'npxg': 'npxg',
    'xg_assist': 'xa',
    'npxg_xg_assist': 'npxg_xa',
    'shots_on_target': 'shots_on_target'
}

EXPECTED_COLUMNS = list(set(COLUMN_MAPPING.values()))
EXPECTED_COLUMNS.insert(0, 'id') # Để tạo bảng theo thứ tự
if 'id' in EXPECTED_COLUMNS:
    EXPECTED_COLUMNS.remove('id')
    
# Cố định thứ tự cột cho DB
FINAL_COLUMNS = [
    'player_name', 'club', 'position', 'age', 'birth_year',
    'matches_played', 'minutes_played', 'goals', 'assists', 'goals_assists',
    'goals_no_penalty', 'penalties', 'penalties_attempted',
    'npxg', 'npxg_xa', 'xg', 'xa', 'shots_on_target'
]

class FBRefScraper:
    def __init__(self):
        self.driver = None
        self.players_data = defaultdict(dict)

    def _init_driver(self):
        from dotenv import load_dotenv
        load_dotenv()
        is_headless = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'
        
        options = Options()
        options.add_argument("--window-size=1920,1080")
        if is_headless:
            options.add_argument("--headless=new")
        options.add_argument(f"user-agent={REQUEST_HEADERS['User-Agent']}")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        
        try:
            from selenium_stealth import stealth
            stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
        except ImportError:
            print("  [WARNING] Chưa cài selenium-stealth, Cloudflare có thể chặn click CAPTCHA.")

        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
            """
        })
        self.driver.set_page_load_timeout(60)

    def _load_cookies(self):
        if os.path.exists(COOKIES_PATH):
            try:
                with open(COOKIES_PATH, "rb") as f:
                    cookies = pickle.load(f)
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except: pass
            except: pass

    def _save_cookies(self):
        os.makedirs(os.path.dirname(COOKIES_PATH), exist_ok=True)
        try:
            with open(COOKIES_PATH, "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
        except: pass

    def get_page(self, url):
        """Fetch page using settings from .env (requests or selenium)"""
        from dotenv import load_dotenv
        import os
        import requests
        
        load_dotenv()
        use_selenium = os.getenv('USE_SELENIUM', 'false').lower() == 'true'
        max_retries = int(os.getenv('MAX_RETRIES', 3))
        backoff = int(os.getenv('RETRY_BACKOFF_FACTOR', 2))
        
        user_agents = os.getenv('USER_AGENT_POOL', '').split(',')
        if not user_agents or not user_agents[0]:
            user_agents = [REQUEST_HEADERS['User-Agent']]
            
        print(f"  [GET] {url} (Selenium: {use_selenium})")
        
        for attempt in range(max_retries):
            # CẤU HÌNH NON-SELENIUM (PURE REQUESTS)
            if not use_selenium:
                ua = random.choice(user_agents)
                print(f"  [Attempt {attempt+1}/{max_retries}] Fetching via requests with UA: {ua[:30]}...")
                headers = {'User-Agent': ua.strip()}
                try:
                    r = requests.get(url, headers=headers, timeout=15)
                    if r.status_code == 200 and "stats_standard" in r.text or "table" in r.text.lower():
                        return r.text
                    print(f"  [WARN] Request returned {r.status_code}. Retry...")
                except Exception as e:
                    print(f"  [ERROR] Request failed: {e}")
            
            # CẤU HÌNH SELENIUM
            else:
                if not self.driver:
                    self._init_driver()
                
                print(f"  [Attempt {attempt+1}/{max_retries}] Fetching via Selenium...")
                self.driver.get(url)
                self._load_cookies()
                self.driver.get(url)
                
                # Chờ người dùng giải CAPTCHA thủ công
                start_wait = time.time()
                success = False
                while time.time() - start_wait < 90:
                    html = self.driver.page_source
                    if "Verify you are human" in html or "challenge-platform" in html or "Just a moment" in html:
                        elapsed = int(time.time() - start_wait)
                        print(f"\r  [!] Cloudflare chặn. Vui lòng tự CLICK vào ô vuông trên Chrome... ({elapsed}s)", end="", flush=True)
                        time.sleep(3)
                    elif "stats_standard" in html or "stats_shooting" in html or "table" in html.lower():
                        print(f"\n  [OK] Đã truy cập thành công ({int(time.time()-start_wait)}s)")
                        self._save_cookies()
                        return html
                    else:
                        time.sleep(2)
                
                if not success:
                    print("\n  [WARN] Selenium failed to load data properly or Captcha timeout. Retry...")

            time.sleep(backoff * (attempt + 1) + random.uniform(2, 5))
            
        print("  [FATAL] Bỏ cuộc. Không thể lấy dữ liệu vì bị chặn hoàn toàn.")
        return ""

    def extract_table(self, html, table_id):
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table", {"id": table_id})
        if not table:
            print(f"  [WARN] Khong tim thay bang {table_id}")
            return
            
        tbody = table.find("tbody")
        rows = tbody.find_all("tr")
        count = 0
        
        for row in rows:
            classes = row.get("class", [])
            if any(c in classes for c in ["thead", "spacer", "partial_table"]):
                continue
                
            player_cell = row.find(["th", "td"], {"data-stat": "player"})
            if not player_cell: continue
            
            player_name = player_cell.get_text(strip=True)
            if not player_name or player_name == "Player": continue

            # Extract fields
            for cell in row.find_all(["th", "td"]):
                stat_name = cell.get("data-stat", "")
                val = cell.get_text(strip=True)
                
                # Ánh xạ cột
                if stat_name in COLUMN_MAPPING:
                    target_col = COLUMN_MAPPING[stat_name]
                    # Format
                    if val == "": val = "N/a"
                    if target_col == 'minutes_played' and val != "N/a":
                        val = val.replace(",", "")
                    self.players_data[player_name][target_col] = val
                    
            # Tên cầu thủ làm key
            self.players_data[player_name]['player_name'] = player_name
            count += 1
            
        print(f"  [OK] Rut trich {count} cau thu tu bang {table_id}")

    def scrape_all(self):
        print("=" * 70)
        print(" THU THAP DU LIEU TONG THE NGOAI HANG ANH 24/25")
        print("=" * 70)
        
        # Bỏ qua cào nếu đã có sẵn dữ liệu trong DB (giúp user ko bao giờ gặp CAPTCHA nếu chạy lại chương trình)
        with DatabaseManager() as db:
            try:
                if len(db.get_player_names_and_teams()) > 200:
                    print("✅ THÔNG BÁO: PHÁT HIỆN DỮ LIỆU ĐÃ CÓ SẴN TRONG CƠ SỞ DỮ LIỆU!")
                    print("✅ Bỏ qua bước cào dữ liệu FBRef để tiết kiệm thời gian và tránh CAPTCHA.")
                    return
            except Exception:
                pass
        print("=" * 70)
        
        # 1. Standard Stats
        html_std = self.get_page("https://fbref.com/en/comps/9/stats/Premier-League-Stats")
        if html_std:
            self.extract_table(html_std, "stats_standard")
        
        # 2. Shooting Stats
        time.sleep(random.uniform(5, 8))
        html_sho = self.get_page("https://fbref.com/en/comps/9/shooting/Premier-League-Stats")
        if html_sho:
            self.extract_table(html_sho, "stats_shooting")

        # Loc cau thu > 90 phut
        final_list = []
        for name, data in self.players_data.items():
            mins = data.get('minutes_played', '0')
            if mins != 'N/a' and str(mins).isdigit() and int(mins) > MIN_MINUTES_PLAYED:
                # Dien N/a cho cot thieu
                for col in FINAL_COLUMNS:
                    if col not in data:
                        data[col] = "N/a"
                final_list.append(data)
                
        print(f"\n  [KET QUA] Tong cong {len(final_list)} cau thu (sau khi loc >90 phut)")
        
        # Luu DB
        if final_list:
            with DatabaseManager() as db:
                # Xóa bảng cũ để làm cấu trúc mớii
                db._execute_query("DROP TABLE IF EXISTS player_stats")
                db.create_player_stats_table(FINAL_COLUMNS)
                db.insert_player_stats(final_list, FINAL_COLUMNS)
                print(f"  [DB] Da ghi {len(final_list)} cau thu vao SQLite!")
                
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    scraper = FBRefScraper()
    scraper.scrape_all()
