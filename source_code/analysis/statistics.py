"""
statistics.py - Phân tích thống kê cầu thủ theo đội
Phần III.1

Chức năng:
1. Tính trung vị, trung bình, độ lệch chuẩn của mỗi chỉ số cho mỗi đội
2. Tìm đội có chỉ số cao nhất ở mỗi chỉ số
3. Đánh giá đội có phong độ tốt nhất

Kết quả: 
- output/team_statistics.csv
- output/best_teams_per_stat.csv
"""

import os
import sys

import numpy as np
import pandas as pd

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR
from database.db_manager import DatabaseManager


def load_data():
    """Tải dữ liệu cầu thủ từ database và chuyển thành DataFrame."""
    with DatabaseManager() as db:
        players = db.get_all_players()

    if not players:
        print("❌ Không có dữ liệu trong database!")
        return None

    df = pd.DataFrame(players)
    print(f"📋 Đã tải {len(df)} cầu thủ từ database")
    return df


def get_numeric_columns(df):
    """Tìm các cột có thể chuyển thành số."""
    numeric_cols = []
    exclude_cols = {"id", "player_name", "club", "position", "nationality",
                    "transfer_value", "source_url", "etv_currency", "birth_year", "age"}

    for col in df.columns:
        if col in exclude_cols:
            continue
        # Thử chuyển thành số
        temp = df[col].replace(["N/a", "", "--", "N/A"], np.nan)
        temp = temp.apply(lambda x: str(x).replace(",", "") if pd.notna(x) else x)
        try:
            converted = pd.to_numeric(temp, errors="coerce")
            # Chỉ giữ cột có ít nhất 20% giá trị hợp lệ
            if converted.notna().mean() > 0.2:
                numeric_cols.append(col)
        except Exception:
            continue

    return numeric_cols


def prepare_numeric_df(df, numeric_cols):
    """Chuyển các cột thành kiểu số."""
    df_numeric = df[["player_name", "club"] + numeric_cols].copy()

    for col in numeric_cols:
        df_numeric[col] = df_numeric[col].replace(["N/a", "", "--", "N/A"], np.nan)
        df_numeric[col] = df_numeric[col].apply(
            lambda x: str(x).replace(",", "") if pd.notna(x) else x
        )
        df_numeric[col] = pd.to_numeric(df_numeric[col], errors="coerce")

    return df_numeric


def calculate_team_statistics(df_numeric, numeric_cols):
    """
    Tính trung vị, trung bình, độ lệch chuẩn của mỗi chỉ số cho mỗi đội.
    
    Returns: DataFrame với multi-level columns (stat, metric)
    """
    results = []

    teams = df_numeric["club"].unique()
    print(f"\n📊 Tính thống kê cho {len(teams)} đội...")

    for team in sorted(teams):
        team_data = df_numeric[df_numeric["club"] == team]
        team_stats = {"club": team, "num_players": len(team_data)}

        for col in numeric_cols:
            values = team_data[col].dropna()
            if len(values) > 0:
                team_stats[f"{col}_mean"] = round(values.mean(), 2)
                team_stats[f"{col}_median"] = round(values.median(), 2)
                team_stats[f"{col}_std"] = round(values.std(), 2)
            else:
                team_stats[f"{col}_mean"] = "N/a"
                team_stats[f"{col}_median"] = "N/a"
                team_stats[f"{col}_std"] = "N/a"

        results.append(team_stats)

    return pd.DataFrame(results)


def find_best_teams(stats_df, numeric_cols):
    """
    Tìm đội có điểm số cao nhất ở mỗi chỉ số (dựa trên mean).
    
    Returns: DataFrame với mỗi hàng là 1 chỉ số và đội tốt nhất
    """
    best_teams = []

    for col in numeric_cols:
        mean_col = f"{col}_mean"
        if mean_col in stats_df.columns:
            # Chuyển sang số
            temp = pd.to_numeric(stats_df[mean_col], errors="coerce")
            if temp.notna().any():
                best_idx = temp.idxmax()
                best_teams.append({
                    "statistic": col,
                    "best_team": stats_df.loc[best_idx, "club"],
                    "best_value": stats_df.loc[best_idx, mean_col],
                })

    return pd.DataFrame(best_teams)


def evaluate_best_team(best_teams_df, stats_df):
    """
    Đánh giá đội có phong độ tốt nhất dựa trên số lần dẫn đầu các chỉ số.
    """
    print("\n" + "=" * 70)
    print("🏆 ĐÁNH GIÁ ĐỘI BÓNG CÓ PHONG ĐỘ TỐT NHẤT")
    print("=" * 70)

    if best_teams_df.empty:
        print("Không thể đánh giá vì thiếu dữ liệu")
        return None

    # Đếm số lần mỗi đội dẫn đầu
    team_wins = best_teams_df["best_team"].value_counts()

    print("\n📊 Số chỉ số dẫn đầu theo đội:")
    for team, count in team_wins.items():
        print(f"  {team}: {count} chỉ số")

    # Đội dẫn đầu nhiều nhất
    best_team = team_wins.index[0]
    print(f"\n🏅 Đội có phong độ tốt nhất: {best_team}")
    print(f"   Dẫn đầu {team_wins.iloc[0]} chỉ số")

    # Nhóm các chỉ số quan trọng
    attack_stats = ["goals", "assists", "goals_assists", "xg", "npxg", "xa"]

    for stats, category, label in [
        (attack_stats, "Tấn công & Hiệu suất", "⚽"),
    ]:
        relevant = best_teams_df[best_teams_df["statistic"].isin(stats)]
        if not relevant.empty:
            print(f"\n{label} {category}:")
            for _, row in relevant.iterrows():
                print(f"  {row['statistic']}: {row['best_team']} ({row['best_value']})")

    return best_team


def main():
    """Chạy phân tích thống kê."""
    # Tải dữ liệu
    df = load_data()
    if df is None:
        return

    # Tìm cột số
    numeric_cols = get_numeric_columns(df)
    print(f"📊 Tìm thấy {len(numeric_cols)} chỉ số dạng số")

    # Chuẩn bị DataFrame số
    df_numeric = prepare_numeric_df(df, numeric_cols)

    # Tính thống kê theo đội
    stats_df = calculate_team_statistics(df_numeric, numeric_cols)

    # Lưu file CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    stats_path = os.path.join(OUTPUT_DIR, "team_statistics.csv")
    stats_df.to_csv(stats_path, index=False, encoding="utf-8-sig")
    print(f"\n📁 Đã lưu thống kê: {stats_path}")

    # Tìm đội tốt nhất mỗi chỉ số
    best_teams_df = find_best_teams(stats_df, numeric_cols)
    best_path = os.path.join(OUTPUT_DIR, "best_teams_per_stat.csv")
    best_teams_df.to_csv(best_path, index=False, encoding="utf-8-sig")
    print(f"📁 Đã lưu đội tốt nhất: {best_path}")

    # Đánh giá tổng hợp
    best_team = evaluate_best_team(best_teams_df, stats_df)

    return stats_df, best_teams_df


if __name__ == "__main__":
    main()
