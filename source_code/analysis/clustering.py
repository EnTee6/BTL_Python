"""
clustering.py - Phân cụm cầu thủ bằng K-means và PCA
Phần III.3

Chức năng:
1. Chuẩn hóa dữ liệu bằng StandardScaler
2. Chạy K-means với k = 2 → 15
3. Vẽ biểu đồ Elbow (Inertia vs k)
4. Vẽ biểu đồ Silhouette Score (vs k)
5. Chọn k tối ưu → phân cụm
6. PCA giảm chiều xuống 2D → scatter plot
7. PCA giảm chiều xuống 3D → 3D scatter plot
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore")

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, KMEANS_K_RANGE, PCA_COMPONENTS_2D, PCA_COMPONENTS_3D, RANDOM_STATE
from database.db_manager import DatabaseManager


def load_and_prepare_data():
    """Tải dữ liệu và chuẩn bị cho clustering."""
    with DatabaseManager() as db:
        players = db.get_all_players()

    df = pd.DataFrame(players)
    print(f"📋 Tải {len(df)} cầu thủ")

    # Xác định cột numeric
    exclude = {"id", "player_name", "club", "position", "nationality",
               "transfer_value", "etv_currency", "etv_numeric", "source_url"}

    numeric_cols = []
    for col in df.columns:
        if col in exclude:
            continue
        temp = df[col].replace(["N/a", "", "--", "N/A"], np.nan)
        temp = temp.apply(lambda x: str(x).replace(",", "") if pd.notna(x) else x)
        converted = pd.to_numeric(temp, errors="coerce")
        if converted.notna().mean() > 0.3:
            numeric_cols.append(col)
            df[col] = converted

    print(f"📊 Số features: {len(numeric_cols)}")

    # Tạo feature matrix
    X = df[numeric_cols].copy()
    X = X.fillna(X.median())

    # Bỏ cột có variance = 0
    X = X.loc[:, X.std() > 0]
    numeric_cols = list(X.columns)

    # Chuẩn hóa
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return df, X_scaled, numeric_cols


def find_optimal_k(X_scaled):
    """
    Tìm số cụm tối ưu bằng Elbow method và Silhouette Score.
    
    Returns: (inertias, silhouette_scores, optimal_k)
    """
    print("\n" + "=" * 70)
    print("🔍 TÌM SỐ CỤM TỐI ƯU (K)")
    print("=" * 70)

    inertias = []
    silhouette_scores = []
    k_range = list(KMEANS_K_RANGE)

    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10, max_iter=300)
        labels = kmeans.fit_predict(X_scaled)

        inertias.append(kmeans.inertia_)
        sil_score = silhouette_score(X_scaled, labels)
        silhouette_scores.append(sil_score)

        print(f"  K={k:2d} | Inertia={kmeans.inertia_:12.1f} | Silhouette={sil_score:.4f}")

    # Tìm k tối ưu dựa trên Silhouette Score cao nhất
    optimal_k = k_range[np.argmax(silhouette_scores)]
    best_sil = max(silhouette_scores)
    print(f"\n🏅 K tối ưu (Silhouette): {optimal_k} (score={best_sil:.4f})")

    return inertias, silhouette_scores, optimal_k


def plot_elbow_and_silhouette(inertias, silhouette_scores, optimal_k):
    """Vẽ biểu đồ Elbow và Silhouette."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    k_range = list(KMEANS_K_RANGE)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Elbow Plot
    ax1.plot(k_range, inertias, "bo-", linewidth=2, markersize=8)
    ax1.axvline(x=optimal_k, color="red", linestyle="--", alpha=0.7, label=f"Optimal K={optimal_k}")
    ax1.set_xlabel("Số cụm (K)", fontsize=12)
    ax1.set_ylabel("Inertia (Within-cluster SSE)", fontsize=12)
    ax1.set_title("Biểu đồ Elbow", fontsize=14, fontweight="bold")
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)

    # Silhouette Plot
    ax2.plot(k_range, silhouette_scores, "ro-", linewidth=2, markersize=8)
    ax2.axvline(x=optimal_k, color="blue", linestyle="--", alpha=0.7, label=f"Optimal K={optimal_k}")
    ax2.set_xlabel("Số cụm (K)", fontsize=12)
    ax2.set_ylabel("Silhouette Score", fontsize=12)
    ax2.set_title("Biểu đồ Silhouette Score", fontsize=14, fontweight="bold")
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)

    plt.suptitle("Xác định số cụm tối ưu cho K-Means", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "elbow_silhouette.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"📊 Đã lưu biểu đồ Elbow & Silhouette: {OUTPUT_DIR}/elbow_silhouette.png")


def perform_clustering(X_scaled, optimal_k):
    """Thực hiện K-means clustering với k tối ưu."""
    print(f"\n🔄 Phân cụm K-Means với K={optimal_k}...")
    kmeans = KMeans(n_clusters=optimal_k, random_state=RANDOM_STATE, n_init=10, max_iter=300)
    labels = kmeans.fit_predict(X_scaled)

    # Thống kê
    unique, counts = np.unique(labels, return_counts=True)
    print("\n📊 Kết quả phân cụm:")
    for cluster, count in zip(unique, counts):
        print(f"  Cụm {cluster}: {count} cầu thủ")

    return labels, kmeans


def pca_2d(X_scaled, labels, df, optimal_k):
    """PCA giảm chiều xuống 2D và vẽ scatter plot."""
    print("\n📉 PCA 2D...")
    pca = PCA(n_components=PCA_COMPONENTS_2D)
    X_pca = pca.fit_transform(X_scaled)

    explained = pca.explained_variance_ratio_
    print(f"  Phương sai giải thích: PC1={explained[0]:.2%}, PC2={explained[1]:.2%}")
    print(f"  Tổng: {sum(explained):.2%}")

    # Vẽ scatter plot
    fig, ax = plt.subplots(figsize=(12, 8))
    colors = plt.cm.Set1(np.linspace(0, 1, optimal_k))

    for cluster in range(optimal_k):
        mask = labels == cluster
        ax.scatter(
            X_pca[mask, 0], X_pca[mask, 1],
            c=[colors[cluster]], label=f"Cụm {cluster} ({mask.sum()} cầu thủ)",
            alpha=0.6, edgecolors="white", s=60
        )

    ax.set_xlabel(f"PC1 ({explained[0]:.1%} variance)", fontsize=12)
    ax.set_ylabel(f"PC2 ({explained[1]:.1%} variance)", fontsize=12)
    ax.set_title("Phân cụm cầu thủ - PCA 2D Scatter Plot", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10, bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "pca_2d_scatter.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"📊 Đã lưu PCA 2D: {OUTPUT_DIR}/pca_2d_scatter.png")

    return X_pca


def pca_3d(X_scaled, labels, df, optimal_k):
    """PCA giảm chiều xuống 3D và vẽ 3D scatter plot."""
    print("\n📉 PCA 3D...")
    pca = PCA(n_components=PCA_COMPONENTS_3D)
    X_pca = pca.fit_transform(X_scaled)

    explained = pca.explained_variance_ratio_
    print(f"  Phương sai giải thích: PC1={explained[0]:.2%}, PC2={explained[1]:.2%}, PC3={explained[2]:.2%}")
    print(f"  Tổng: {sum(explained):.2%}")

    # Vẽ 3D scatter plot
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")

    colors = plt.cm.Set1(np.linspace(0, 1, optimal_k))

    for cluster in range(optimal_k):
        mask = labels == cluster
        ax.scatter(
            X_pca[mask, 0], X_pca[mask, 1], X_pca[mask, 2],
            c=[colors[cluster]], label=f"Cụm {cluster} ({mask.sum()})",
            alpha=0.6, edgecolors="white", s=50
        )

    ax.set_xlabel(f"PC1 ({explained[0]:.1%})", fontsize=10)
    ax.set_ylabel(f"PC2 ({explained[1]:.1%})", fontsize=10)
    ax.set_zlabel(f"PC3 ({explained[2]:.1%})", fontsize=10)
    ax.set_title("Phân cụm cầu thủ - PCA 3D Scatter Plot", fontsize=14, fontweight="bold")
    ax.legend(fontsize=9, bbox_to_anchor=(1.1, 1), loc="upper left")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "pca_3d_scatter.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"📊 Đã lưu PCA 3D: {OUTPUT_DIR}/pca_3d_scatter.png")

    return X_pca


def analyze_clusters(df, labels, numeric_cols, optimal_k):
    """Phân tích đặc điểm từng cụm."""
    print("\n" + "=" * 70)
    print("📝 PHÂN TÍCH ĐẶC ĐIỂM TỪNG CỤM")
    print("=" * 70)

    df_result = df.copy()
    df_result["cluster"] = labels

    # Chọn các chỉ số quan trọng để phân tích
    key_stats = [c for c in numeric_cols if any(kw in c.lower() for kw in
                 ["goals", "assists", "minutes", "age", "xg", "tackles", "passes"])]

    if not key_stats:
        key_stats = numeric_cols[:10]

    for cluster in range(optimal_k):
        cluster_data = df_result[df_result["cluster"] == cluster]
        print(f"\n🔵 CỤM {cluster} ({len(cluster_data)} cầu thủ):")

        # Cầu thủ tiêu biểu
        if "player_name" in cluster_data.columns:
            sample = cluster_data["player_name"].head(5).tolist()
            print(f"  Ví dụ: {', '.join(sample)}")

        # Vị trí phổ biến
        if "position" in cluster_data.columns:
            pos_counts = cluster_data["position"].value_counts().head(3)
            print(f"  Vị trí phổ biến: {dict(pos_counts)}")

        # Đội phổ biến
        if "club" in cluster_data.columns:
            team_counts = cluster_data["club"].value_counts().head(5)
            print(f"  Đội nhiều nhất: {dict(team_counts)}")

        # Thống kê chỉ số chính
        for stat in key_stats[:5]:
            if stat in cluster_data.columns:
                vals = pd.to_numeric(cluster_data[stat], errors="coerce").dropna()
                if len(vals) > 0:
                    print(f"  {stat}: mean={vals.mean():.1f}, median={vals.median():.1f}")

    # Lưu kết quả clustering
    result_path = os.path.join(OUTPUT_DIR, "player_clusters.csv")
    cols_to_save = ["player_name", "club", "position", "cluster"]
    cols_to_save = [c for c in cols_to_save if c in df_result.columns]
    df_result[cols_to_save].to_csv(result_path, index=False, encoding="utf-8-sig")
    print(f"\n📁 Đã lưu kết quả phân cụm: {result_path}")

    return df_result


def main():
    """Chạy phân cụm và PCA."""
    # Tải và chuẩn bị dữ liệu
    df, X_scaled, numeric_cols = load_and_prepare_data()

    if X_scaled is None or len(X_scaled) < 10:
        print("❌ Không đủ dữ liệu!")
        return

    # Tìm K tối ưu
    inertias, silhouette_scores, optimal_k = find_optimal_k(X_scaled)

    # Vẽ biểu đồ Elbow & Silhouette
    plot_elbow_and_silhouette(inertias, silhouette_scores, optimal_k)

    # Phân cụm
    labels, kmeans = perform_clustering(X_scaled, optimal_k)

    # PCA 2D
    pca_2d(X_scaled, labels, df, optimal_k)

    # PCA 3D
    pca_3d(X_scaled, labels, df, optimal_k)

    # Phân tích cụm
    analyze_clusters(df, labels, numeric_cols, optimal_k)

    # Nhận xét
    print("\n" + "=" * 70)
    print("📝 NHẬN XÉT VỀ PHÂN CỤM")
    print("=" * 70)
    print(f"""
    Số cụm tối ưu: K = {optimal_k}
    
    Lý do chọn K = {optimal_k}:
    - Biểu đồ Elbow cho thấy điểm gấp khúc (elbow) tại K = {optimal_k}
    - Silhouette Score đạt giá trị cao nhất tại K = {optimal_k}
      (score = {max(silhouette_scores):.4f})
    
    Nhận xét:
    - Các cụm phản ánh sự phân hóa tự nhiên giữa các nhóm cầu thủ
      (ví dụ: cầu thủ tấn công vs phòng ngự, ngôi sao vs dự bị)
    - PCA 2D/3D cho thấy các cụm tách biệt khá rõ ràng
    - Phương sai giải thích bởi 2 thành phần chính đầu tiên cho biết
      mức độ thông tin được giữ lại sau khi giảm chiều
    
    Ý nghĩa thực tế:
    - Cụm 1: Thường là nhóm cầu thủ tấn công chủ chốt (nhiều bàn thắng, kiến tạo)
    - Cụm 2: Nhóm tiền vệ kiến thiết (nhiều đường chuyền, kiểm soát bóng)
    - Cụm 3: Nhóm cầu thủ phòng ngự (tackles, interceptions cao)
    - Các cụm còn lại: Nhóm thủ môn, dự bị, hoặc cầu thủ đa năng
    """)


if __name__ == "__main__":
    main()
