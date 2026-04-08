"""
db_manager.py - Quản lý cơ sở dữ liệu SQLite cho dự án phân tích cầu thủ EPL
"""
import sqlite3
import os
import sys

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


class DatabaseManager:
    """Quản lý kết nối và thao tác với SQLite database."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = None

    def connect(self):
        """Mở kết nối đến database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Đóng kết nối database."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ================================================================
    # Phần I.1 - Bảng player_stats
    # ================================================================

    def create_player_stats_table(self, columns):
        self.conn.execute("DROP TABLE IF EXISTS player_stats")

        col_defs = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
        col_defs.append("player_name TEXT NOT NULL")
        col_defs.append("club TEXT NOT NULL")

        for col in columns:
            if col not in ("player_name", "club", "id"):
                col_defs.append(f'"{col}" TEXT')

        create_sql = f"CREATE TABLE player_stats ({', '.join(col_defs)})"
        self.conn.execute(create_sql)
        self.conn.commit()
        print(f"[DB] Tạo bảng player_stats với {len(col_defs)} cột")

    def insert_player_stats(self, data_rows, columns):
        if not data_rows:
            return

        try:
            self.conn.execute("SELECT 1 FROM player_stats LIMIT 1")
        except sqlite3.OperationalError:
            self.create_player_stats_table(columns)

        col_names = ["player_name", "club"] + [c for c in columns if c not in ("player_name", "club", "id")]
        placeholders = ", ".join(["?"] * len(col_names))
        quoted_cols = ", ".join([f'"{c}"' for c in col_names])
        insert_sql = f"INSERT INTO player_stats ({quoted_cols}) VALUES ({placeholders})"

        count = 0
        for row in data_rows:
            values = []
            for col in col_names:
                val = row.get(col, "N/a")
                if val is None or val == "" or val == "--":
                    val = "N/a"
                values.append(str(val))
            self.conn.execute(insert_sql, values)
            count += 1

        self.conn.commit()
        print(f"[DB] Đã chèn {count} cầu thủ vào player_stats")

    def create_transfer_values_table(self):
        self.conn.execute("DROP TABLE IF EXISTS transfer_values")
        self.conn.execute("""
            CREATE TABLE transfer_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                club TEXT NOT NULL,
                transfer_value TEXT DEFAULT 'N/a',
                etv_currency TEXT DEFAULT 'EUR',
                etv_numeric REAL,
                source_url TEXT
            )
        """)
        self.conn.commit()

    def insert_transfer_value(self, player_name, club, transfer_value, etv_numeric=None, source_url=None):
        self.conn.execute(
            """INSERT INTO transfer_values 
               (player_name, club, transfer_value, etv_currency, etv_numeric, source_url) 
               VALUES (?, ?, ?, 'EUR', ?, ?)""",
            (player_name, club, transfer_value, etv_numeric, source_url)
        )
        self.conn.commit()

    def insert_transfer_values_batch(self, data_rows):
        for row in data_rows:
            self.insert_transfer_value(
                player_name=row.get("player_name", ""),
                club=row.get("club", ""),
                transfer_value=row.get("transfer_value", "N/a"),
                etv_numeric=row.get("etv_numeric"),
                source_url=row.get("source_url"),
            )

    def get_player_by_name(self, name):
        cursor = self.conn.execute(
            """SELECT ps.*, tv.transfer_value, tv.etv_numeric
               FROM player_stats ps
               LEFT JOIN transfer_values tv ON ps.player_name = tv.player_name AND ps.club = tv.club
               WHERE ps.player_name LIKE ?""",
            (f"%{name}%",)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_players_by_club(self, club):
        cursor = self.conn.execute(
            """SELECT ps.*, tv.transfer_value, tv.etv_numeric
               FROM player_stats ps
               LEFT JOIN transfer_values tv ON ps.player_name = tv.player_name AND ps.club = tv.club
               WHERE ps.club LIKE ?""",
            (f"%{club}%",)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_players(self):
        cursor = self.conn.execute(
            """SELECT ps.*, tv.transfer_value, tv.etv_numeric
               FROM player_stats ps
               LEFT JOIN transfer_values tv ON ps.player_name = tv.player_name AND ps.club = tv.club"""
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_teams(self):
        cursor = self.conn.execute("SELECT DISTINCT club FROM player_stats ORDER BY club")
        return [row["club"] for row in cursor.fetchall()]

    def get_player_names_and_teams(self):
        cursor = self.conn.execute("SELECT player_name, club FROM player_stats")
        return [(row["player_name"], row["club"]) for row in cursor.fetchall()]

    def get_column_names(self, table="player_stats"):
        cursor = self.conn.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cursor.fetchall()]
    
    def _execute_query(self, sql):
        self.conn.execute(sql)
        self.conn.commit()


if __name__ == "__main__":
    # Test basic functionality
    with DatabaseManager() as db:
        print(f"Database path: {db.db_path}")
        print("Kết nối database thành công!")
