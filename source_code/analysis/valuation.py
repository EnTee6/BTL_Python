"""
valuation.py - Mô hình định giá cầu thủ
Phần III.2

Đề xuất phương pháp: Random Forest Regression
- Features: các chỉ số thống kê từ FBRef (goals, assists, xG, minutes, age, etc.)
- Target: ETV (Estimated Transfer Value) từ footballtransfers.com

Quy trình:
1. Chuẩn bị dữ liệu (xử lý N/a, chuẩn hóa)
2. Chọn features quan trọng
3. Train model (Random Forest + Linear Regression để so sánh)
4. Đánh giá (R², MAE, RMSE)
5. Feature importance analysis
6. Dự đoán giá trị cho cầu thủ không có ETV
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, RANDOM_STATE
from database.db_manager import DatabaseManager


def load_data():
    """Tải dữ liệu và merge stats với transfer values."""
    with DatabaseManager() as db:
        players = db.get_all_players()

    df = pd.DataFrame(players)
    print(f"📋 Tải {len(df)} cầu thủ")
    return df


def prepare_features(df):
    """
    Chuẩn bị features cho model.
    Chỉ giữ cầu thủ có ETV hợp lệ.
    """
    # Lọc cầu thủ có ETV
    df_valid = df[df["etv_numeric"].notna() & (df["etv_numeric"] > 0)].copy()
    print(f"📊 Cầu thủ có ETV hợp lệ: {len(df_valid)}")

    if len(df_valid) < 10:
        print("⚠️ Không đủ dữ liệu để train model (cần ít nhất 10 cầu thủ)")
        return None, None, None

    # Xác định cột numeric
    exclude = {"id", "player_name", "club", "position", "nationality",
               "transfer_value", "etv_currency", "etv_numeric", "source_url", "birth_year", "age"}

    feature_cols = []
    for col in df_valid.columns:
        if col in exclude:
            continue
        temp = df_valid[col].replace(["N/a", "", "--"], np.nan)
        temp = temp.apply(lambda x: str(x).replace(",", "") if pd.notna(x) else x)
        converted = pd.to_numeric(temp, errors="coerce")
        if converted.notna().mean() > 0.3:
            feature_cols.append(col)
            df_valid[col] = converted

    print(f"📊 Số features: {len(feature_cols)}")

    # Target
    y = df_valid["etv_numeric"].astype(float)

    # Features matrix
    X = df_valid[feature_cols].copy()
    for col in feature_cols:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    # Điền NaN bằng median
    X = X.fillna(X.median())

    # Bỏ cột có variance = 0
    X = X.loc[:, X.std() > 0]
    feature_cols = list(X.columns)

    return X, y, feature_cols


def train_and_evaluate(X, y, feature_cols):
    """
    Train model và đánh giá.
    
    Models: Random Forest, Gradient Boosting, Linear Regression
    """
    print("\n" + "=" * 70)
    print("🤖 TRAINING MÔ HÌNH ĐỊNH GIÁ CẦU THỦ")
    print("=" * 70)

    # Chia dữ liệu
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    # Chuẩn hóa
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Các model
    models = {
        "Random Forest": RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=RANDOM_STATE
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=100, max_depth=5, random_state=RANDOM_STATE
        ),
        "Linear Regression": LinearRegression(),
    }

    results = {}
    best_model = None
    best_r2 = -999

    for name, model in models.items():
        print(f"\n📈 Training {name}...")

        # Dùng scaled cho Linear, unscaled cho tree-based
        if "Linear" in name:
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

        # Đánh giá
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        results[name] = {"R2": r2, "MAE": mae, "RMSE": rmse}

        print(f"  R² Score: {r2:.4f}")
        print(f"  MAE: €{mae:,.0f}")
        print(f"  RMSE: €{rmse:,.0f}")

        if r2 > best_r2:
            best_r2 = r2
            best_model = (name, model)

    # Feature Importance (từ Random Forest)
    rf_model = models["Random Forest"]
    importances = rf_model.feature_importances_
    feature_importance = pd.DataFrame({
        "feature": feature_cols,
        "importance": importances,
    }).sort_values("importance", ascending=False)

    print(f"\n🏅 Best model: {best_model[0]} (R²={best_r2:.4f})")

    return results, feature_importance, best_model


def plot_results(results, feature_importance):
    """Vẽ biểu đồ kết quả."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. So sánh models
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("So sánh các mô hình định giá cầu thủ", fontsize=14, fontweight="bold")

    metrics = ["R2", "MAE", "RMSE"]
    for i, metric in enumerate(metrics):
        values = [results[m][metric] for m in results]
        bars = axes[i].bar(results.keys(), values, color=["#2196F3", "#4CAF50", "#FF9800"])
        axes[i].set_title(metric)
        axes[i].set_ylabel(metric)
        for bar, val in zip(bars, values):
            axes[i].text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f"{val:.2f}" if metric == "R2" else f"€{val:,.0f}",
                         ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "model_comparison.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # 2. Feature Importance (top 20)
    top_n = min(20, len(feature_importance))
    top_features = feature_importance.head(top_n)

    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(range(top_n), top_features["importance"].values, color="#2196F3")
    ax.set_yticks(range(top_n))
    ax.set_yticklabels(top_features["feature"].values, fontsize=9)
    ax.set_xlabel("Importance")
    ax.set_title(f"Top {top_n} Feature Importance (Random Forest)", fontweight="bold")
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "feature_importance.png"), dpi=150, bbox_inches="tight")
    plt.close()

    print(f"\n📊 Đã lưu biểu đồ vào {OUTPUT_DIR}")


def main():
    """Chạy mô hình định giá."""
    # Tải dữ liệu
    df = load_data()

    # Chuẩn bị features
    result = prepare_features(df)
    if result[0] is None:
        return

    X, y, feature_cols = result

    # Train & evaluate
    results, feature_importance, best_model = train_and_evaluate(X, y, feature_cols)

    # Vẽ biểu đồ
    plot_results(results, feature_importance)

    # Lưu feature importance
    fi_path = os.path.join(OUTPUT_DIR, "feature_importance.csv")
    feature_importance.to_csv(fi_path, index=False, encoding="utf-8-sig")
    print(f"📁 Feature importance: {fi_path}")

    # Phương pháp đề xuất
    print("\n" + "=" * 70)
    print("📝 PHƯƠNG PHÁP ĐỊNH GIÁ CẦU THỦ ĐỀ XUẤT")
    print("=" * 70)
    print("""
    Phương pháp: Random Forest Regression

    Lý do chọn:
    1. Random Forest xử lý tốt dữ liệu phi tuyến tính (quan hệ giữa 
       chỉ số và giá trị không phải lúc nào cũng tuyến tính)
    2. Tự động xử lý feature selection qua importance scores
    3. Robust với outliers (cầu thủ ngôi sao có giá trị rất cao)
    4. Không cần chuẩn hóa dữ liệu (tree-based)
    
    Features quan trọng nhất (theo kết quả):
    """)

    for i, row in feature_importance.head(10).iterrows():
        print(f"    {i+1}. {row['feature']}: {row['importance']:.4f}")

    print("""
    Yếu tố ảnh hưởng đến giá trị cầu thủ:
    - Tuổi (cầu thủ trẻ thường có giá cao hơn)
    - Phong độ (goals, assists, xG)
    - Thời gian thi đấu (phút, số trận)
    - Vị trí (tiền đạo thường đắt hơn hậu vệ)
    - Khả năng sáng tạo (key passes, SCA, GCA)
    """)


if __name__ == "__main__":
    main()
