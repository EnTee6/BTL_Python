"""
lookup.py - CLI tra cứu dữ liệu cầu thủ qua Flask API
Phần II.2

Cú pháp:
    python lookup.py --name "Mohamed Salah"
    python lookup.py --club "Liverpool"

Kết quả:
    - In ra màn hình dưới dạng bảng
    - Xuất file CSV (tên file theo tên cầu thủ hoặc CLB)
"""

import argparse
import csv
import os
import sys

import requests
from tabulate import tabulate

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FLASK_HOST, FLASK_PORT, OUTPUT_DIR


API_BASE_URL = f"http://{FLASK_HOST}:{FLASK_PORT}/api"


def query_api(endpoint, params):
    """
    Gọi Flask API và trả về dữ liệu.
    
    Args:
        endpoint: str - tên endpoint (ví dụ: 'players', 'clubs')
        params: dict - query parameters
    
    Returns: list of dict hoặc None nếu lỗi
    """
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if resp.status_code == 200:
            return data.get("data", [])
        elif resp.status_code == 404:
            print(f"⚠️ {data.get('message', 'Không tìm thấy kết quả')}")
            return []
        else:
            print(f"❌ Lỗi API: {data.get('error', 'Unknown error')}")
            return None

    except requests.ConnectionError:
        print("❌ Không thể kết nối đến API server!")
        print(f"   Hãy đảm bảo Flask server đang chạy: python api/app.py")
        return None
    except requests.RequestException as e:
        print(f"❌ Lỗi request: {e}")
        return None


def display_table(data, title=""):
    """
    Hiển thị dữ liệu dưới dạng bảng.
    
    Args:
        data: list of dict
        title: str - tiêu đề bảng
    """
    if not data:
        print("Không có dữ liệu để hiển thị.")
        return

    print(f"\n{'='*80}")
    if title:
        print(f"📊 {title}")
        print(f"{'='*80}")

    # Chọn các cột quan trọng để hiển thị (không hiển thị hết ~100 cột)
    priority_cols = [
        "player_name", "team", "position", "age",
        "standard_matches_played", "standard_starts", "standard_minutes",
        "standard_goals", "standard_assists",
        "standard_xg", "standard_xg_assist",
        "transfer_value", "etv_numeric"
    ]

    # Lọc cột có trong dữ liệu
    available_cols = []
    for col in priority_cols:
        if col in data[0]:
            available_cols.append(col)

    # Nếu không có cột ưu tiên nào, hiển thị 15 cột đầu
    if not available_cols:
        available_cols = list(data[0].keys())[:15]

    # Tạo bảng
    table_data = []
    for row in data:
        table_data.append([row.get(col, "N/a") for col in available_cols])

    # Rút gọn tên cột cho hiển thị
    display_headers = [col.replace("standard_", "").replace("_", " ").title() for col in available_cols]

    print(tabulate(table_data, headers=display_headers, tablefmt="grid", maxcolwidths=20))
    print(f"\nTổng: {len(data)} cầu thủ")
    print(f"(Hiển thị {len(available_cols)} cột chính. File CSV chứa tất cả cột.)")


def save_to_csv(data, filename):
    """
    Lưu dữ liệu ra file CSV.
    
    Args:
        data: list of dict
        filename: str - tên file (không cần đuôi .csv)
    """
    if not data:
        print("Không có dữ liệu để lưu.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Chuẩn hóa tên file
    safe_filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
    filepath = os.path.join(OUTPUT_DIR, f"{safe_filename}.csv")

    # Lấy tất cả cột
    all_keys = set()
    for row in data:
        all_keys.update(row.keys())

    # Sắp xếp cột (ưu tiên cột quan trọng trước)
    priority = ["player_name", "team", "position", "age"]
    sorted_keys = priority + sorted(k for k in all_keys if k not in priority)

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=sorted_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)

    print(f"\n📁 Đã lưu file CSV: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Tra cứu dữ liệu cầu thủ EPL 2024-2025",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python lookup.py --name "Mohamed Salah"
  python lookup.py --club "Liverpool"
  python lookup.py --name "Salah" --club "Liverpool"
        """
    )
    parser.add_argument("--name", type=str, default=None,
                        help="Tên cầu thủ cần tra cứu")
    parser.add_argument("--club", type=str, default=None,
                        help="Tên câu lạc bộ cần tra cứu")
    args = parser.parse_args()

    if not args.name and not args.club:
        parser.error("Phải cung cấp ít nhất 1 tham số: --name hoặc --club")

    # Tra cứu theo tên cầu thủ
    if args.name:
        print(f"🔍 Tra cứu cầu thủ: {args.name}")
        data = query_api("players", {"name": args.name})
        if data:
            display_table(data, f"Kết quả tra cứu: {args.name}")
            save_to_csv(data, args.name)

    # Tra cứu theo câu lạc bộ
    if args.club:
        print(f"🔍 Tra cứu câu lạc bộ: {args.club}")
        data = query_api("clubs", {"club": args.club})
        if data:
            display_table(data, f"Kết quả tra cứu: {args.club}")
            save_to_csv(data, args.club)


if __name__ == "__main__":
    main()
