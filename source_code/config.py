"""
config.py - Cấu hình cho dự án phân tích cầu thủ EPL 2024-2025
"""
import os

# ============================================================
# Đường dẫn
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "premier_league.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ============================================================
# FBRef Configuration
# ============================================================
FBREF_BASE_URL = "https://fbref.com"
FBREF_SEASON = "2024-2025"
FBREF_COMP_ID = "9"  # Premier League
FBREF_COMP_URL = f"{FBREF_BASE_URL}/en/comps/{FBREF_COMP_ID}/{FBREF_SEASON}/{FBREF_SEASON}-Premier-League-Stats"

# Các bảng thống kê cần thu thập từ mỗi trang đội
FBREF_STAT_TABLES = [
    "stats_standard",
    "stats_shooting",
    "stats_passing",
    "stats_passing_types",
    "stats_gca",
    "stats_defense",
    "stats_possession",
    "stats_playing_time",
    "stats_misc",
    "stats_keeper",
    "stats_keeper_adv",
]

# Danh sách đội EPL 2024-2025 (fallback nếu không scrape được từ trang tổng hợp)
# Format: {team_id: (team_name, url_slug)}
EPL_TEAMS_2024_25 = {
    "18bb7c10": ("Arsenal", "Arsenal"),
    "8602292d": ("Aston Villa", "Aston-Villa"),
    "4ba7cbea": ("Bournemouth", "Bournemouth"),
    "cd051869": ("Brentford", "Brentford"),
    "d07537b9": ("Brighton", "Brighton-and-Hove-Albion"),
    "cff3d9bb": ("Chelsea", "Chelsea"),
    "47c64c55": ("Crystal Palace", "Crystal-Palace"),
    "d3fd31cc": ("Everton", "Everton"),
    "fd962109": ("Fulham", "Fulham"),
    "b74092de": ("Ipswich Town", "Ipswich-Town"),
    "a2d435b3": ("Leicester City", "Leicester-City"),
    "822bd0ba": ("Liverpool", "Liverpool"),
    "b8fd03ef": ("Manchester City", "Manchester-City"),
    "19538871": ("Manchester Utd", "Manchester-United"),
    "b2b47a98": ("Newcastle Utd", "Newcastle-United"),
    "e4a775cb": ("Nott'ham Forest", "Nottingham-Forest"),
    "33c895d4": ("Southampton", "Southampton"),
    "361ca564": ("Tottenham", "Tottenham-Hotspur"),
    "7c21e445": ("West Ham", "West-Ham-United"),
    "8cec06e1": ("Wolves", "Wolverhampton-Wanderers"),
}

def get_team_url(team_id, team_slug):
    """Tạo URL trang thống kê của đội từ team_id và slug."""
    return f"{FBREF_BASE_URL}/en/squads/{team_id}/{FBREF_SEASON}/{team_slug}-Stats"

# ============================================================
# Scraping Configuration
# ============================================================

# Delay giữa các request (giây) - ngẫu nhiên trong khoảng min-max
REQUEST_DELAY_MIN = 5
REQUEST_DELAY_MAX = 10

# Headers cho requests
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Số lần retry tối đa khi gặp lỗi
MAX_RETRIES = 3
RETRY_DELAY = 30  # Delay giữa các lần retry (giây)

# Ngưỡng phút thi đấu tối thiểu
MIN_MINUTES_PLAYED = 90

# ============================================================
# Football Transfers Configuration
# ============================================================
FT_BASE_URL = "https://www.footballtransfers.com"
FT_PLAYER_URL = f"{FT_BASE_URL}/us/players"
FT_REQUEST_DELAY_MIN = 2
FT_REQUEST_DELAY_MAX = 4

# ============================================================
# Flask API Configuration
# ============================================================
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
FLASK_DEBUG = True

# ============================================================
# Analysis Configuration
# ============================================================
KMEANS_K_RANGE = range(2, 16)  # K=2 đến K=15 cho Elbow/Silhouette
PCA_COMPONENTS_2D = 2
PCA_COMPONENTS_3D = 3
RANDOM_STATE = 42
