from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import os
import csv
from werkzeug.utils import secure_filename

# --------------------
# APP CONFIG
# --------------------
app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ML_CSV_PATH = os.path.join(BASE_DIR, "..", "ml", "ranked_vendors.csv")

# --------------------
# DATABASE CONNECTION
# --------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="stuti123",
        database="hidden_local"
    )

# --------------------
# HOME
# --------------------
@app.route("/")
def home():
    return "Hidden Local Backend (MySQL) Running 🚀"

# --------------------
# ADD VENDOR (WITH IMAGE)
# --------------------
@app.route("/add-vendor", methods=["POST"])
def add_vendor():
    data = request.form
    image = request.files.get("image")

    filename = None
    if image:
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO vendors
        (name, category, area, description, rating, latitude, longitude, status, image_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data["name"],
        data["category"],
        data["area"],
        data["description"],
        data["rating"],
        data["latitude"],
        data["longitude"],
        "pending",
        filename
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Vendor added successfully"})

# --------------------
# SERVE UPLOADED IMAGES
# --------------------
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    if not filename or filename == "null":
        return "", 204
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# --------------------
# GET APPROVED VENDORS
# --------------------
@app.route("/vendors", methods=["GET"])
def get_vendors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM vendors WHERE status='approved'")
    vendors = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(vendors)

# --------------------
# ADMIN: PENDING VENDORS
# --------------------
@app.route("/admin/pending", methods=["GET"])
def get_pending_vendors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM vendors WHERE status='pending'")
    vendors = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(vendors)

# --------------------
# ADMIN: APPROVE / REJECT
# --------------------
@app.route("/admin/approve/<int:vendor_id>", methods=["POST"])
def approve_vendor(vendor_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE vendors SET status='approved' WHERE id=%s",
        (vendor_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Vendor approved"})

@app.route("/admin/reject/<int:vendor_id>", methods=["POST"])
def reject_vendor(vendor_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE vendors SET status='rejected' WHERE id=%s",
        (vendor_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Vendor rejected"})

# --------------------
# LIKE / UPVOTE VENDOR
# --------------------
@app.route("/vendor/like/<int:vendor_id>", methods=["POST"])
def like_vendor(vendor_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE vendors SET likes = likes + 1 WHERE id=%s",
        (vendor_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Vendor liked"})

# --------------------
# ML: TOP HIDDEN GEMS
# --------------------
@app.route("/ml/top-gems", methods=["GET"])
def top_hidden_gems():
    gems = []

    if not os.path.exists(ML_CSV_PATH):
        return jsonify([])

    with open(ML_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gems.append({
                "id": int(row.get("id", 0)),
                "name": row["name"],
                "category": row["category"],
                "area": row["area"],
                "rating": float(row["rating"]),
                "score": round(float(row["final_score"]), 2),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "image_path": row.get("image_path"),
                "likes": int(row.get("likes", 0))
            })

    return jsonify(gems[:5])

# --------------------
# RUN APP
# --------------------
if __name__ == "__main__":
    app.run(debug=True)
