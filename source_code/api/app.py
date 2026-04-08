"""
app.py - Flask REST API tra cứu chỉ số cầu thủ
Phần II.1 - API Endpoints:
  GET /api/players?name=<tên cầu thủ>  -> Trả về chỉ số cầu thủ theo tên
  GET /api/clubs?club=<tên CLB>        -> Trả về chỉ số cầu thủ theo CLB
"""

import os
import sys

from flask import Flask, request, jsonify

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
from database.db_manager import DatabaseManager

app = Flask(__name__)


@app.route("/")
def index():
    """Trang chủ API - hiển thị hướng dẫn sử dụng."""
    return jsonify({
        "message": "EPL 2024-2025 Player Stats API",
        "endpoints": {
            "/api/players?name=<tên cầu thủ>": "Tra cứu chỉ số theo tên cầu thủ",
            "/api/clubs?club=<tên CLB>": "Tra cứu chỉ số theo câu lạc bộ",
            "/api/teams": "Danh sách tất cả các đội",
        },
        "examples": [
            "/api/players?name=Salah",
            "/api/clubs?club=Liverpool",
        ]
    })


@app.route("/api/players", methods=["GET"])
def get_players_by_name():
    """
    Tra cứu cầu thủ theo tên.
    Query params:
        name: tên cầu thủ (tìm gần đúng, không phân biệt hoa thường)
    Returns:
        JSON với danh sách cầu thủ và tất cả chỉ số
    """
    name = request.args.get("name", "").strip()

    if not name:
        return jsonify({
            "error": "Thiếu tham số 'name'. Ví dụ: /api/players?name=Salah"
        }), 400

    with DatabaseManager() as db:
        results = db.get_player_by_name(name)

    if not results:
        return jsonify({
            "message": f"Không tìm thấy cầu thủ '{name}'",
            "count": 0,
            "data": []
        }), 404

    return jsonify({
        "message": f"Tìm thấy {len(results)} kết quả cho '{name}'",
        "count": len(results),
        "data": results
    })


@app.route("/api/clubs", methods=["GET"])
def get_players_by_club():
    """
    Tra cứu cầu thủ theo câu lạc bộ.
    Query params:
        club: tên câu lạc bộ (tìm gần đúng, không phân biệt hoa thường)
    Returns:
        JSON với danh sách cầu thủ và tất cả chỉ số
    """
    club = request.args.get("club", "").strip()

    if not club:
        return jsonify({
            "error": "Thiếu tham số 'club'. Ví dụ: /api/clubs?club=Liverpool"
        }), 400

    with DatabaseManager() as db:
        results = db.get_players_by_club(club)

    if not results:
        return jsonify({
            "message": f"Không tìm thấy câu lạc bộ '{club}'",
            "count": 0,
            "data": []
        }), 404

    return jsonify({
        "message": f"Tìm thấy {len(results)} cầu thủ thuộc '{club}'",
        "count": len(results),
        "data": results
    })


@app.route("/api/teams", methods=["GET"])
def get_teams():
    """Lấy danh sách tất cả các đội."""
    with DatabaseManager() as db:
        teams = db.get_all_teams()

    return jsonify({
        "count": len(teams),
        "teams": teams
    })


if __name__ == "__main__":
    print("🚀 Khởi động Flask API Server...")
    print(f"   URL: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"   Endpoints:")
    print(f"     GET /api/players?name=<tên cầu thủ>")
    print(f"     GET /api/clubs?club=<tên CLB>")
    print(f"     GET /api/teams")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
