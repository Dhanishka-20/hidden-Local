from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import mysql.connector
import os
import csv
import re

# ====================
# HELPERS
# ====================

def slugify(name):
    name = name.lower().strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name



def get_vendor_images(vendor_slug):
    # Absolute path to project root
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    folder = os.path.join(
        BASE_PATH,
        "frontend",
        "static",
        "images",
        "vendors",
        vendor_slug
    )

    if not os.path.exists(folder):
        return []

    return [
        f"/static/images/vendors/{vendor_slug}/{img}"
        for img in sorted(os.listdir(folder))
        if img.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ]



# ====================
# APP CONFIG
# ====================

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ML_CSV_PATH = os.path.join(BASE_DIR, "..", "ml", "ranked_vendors.csv")


# ====================
# DATABASE
# ====================

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="150804",
        database="hidden_local"
    )


# ====================
# BASIC PAGES
# ====================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/explore")
def explore():
    return render_template("explore.html")


@app.route("/add-vendor-page")
def add_vendor_page():
    return render_template("add_vendor.html")


# ====================
# VENDOR DETAIL (BY ID)
# ====================

@app.route("/vendor/<int:vendor_id>")
def vendor_detail(vendor_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM vendors WHERE id=%s", (vendor_id,))
    vendor = cursor.fetchone()

    if not vendor:
        cursor.close()
        conn.close()
        return "Vendor not found", 404

    vendor_slug = slugify(vendor["name"])
    vendor["images"] = get_vendor_images(vendor_slug)

    cursor.execute(
        "SELECT * FROM reviews WHERE vendor_id=%s ORDER BY created_at DESC",
        (vendor_id,)
    )
    reviews = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "vendor_detail.html",
        vendor=vendor,
        reviews=reviews
    )


# ====================
# VENDOR DETAIL (BY NAME)
# ====================

@app.route("/vendor/name/<string:vendor_name>")
def vendor_detail_by_name(vendor_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM vendors WHERE name=%s",
        (vendor_name,)
    )
    vendor = cursor.fetchone()

    if not vendor:
        cursor.close()
        conn.close()
        return "Vendor not found", 404

    # ✅ IMPORTANT: use the SAME slug logic everywhere
    vendor_slug = slugify(vendor["name"])

    # ✅ LOAD IMAGES FROM STATIC FOLDER
    vendor["images"] = get_vendor_images(vendor_slug)

    # ✅ LOAD REVIEWS
    cursor.execute(
        "SELECT * FROM reviews WHERE vendor_id=%s ORDER BY created_at DESC",
        (vendor["id"],)
    )
    reviews = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "vendor_detail.html",
        vendor=vendor,
        reviews=reviews
    )


# ====================
# ADD VENDOR
# ====================

@app.route("/add-vendor", methods=["POST"])
def add_vendor():
    data = request.form
    images = request.files.getlist("images")

    vendor_slug = slugify(data["name"])

    vendor_image_dir = os.path.join(
        app.static_folder,
        "images",
        "vendors",
        vendor_slug
    )
    os.makedirs(vendor_image_dir, exist_ok=True)

    for idx, img in enumerate(images, start=1):
        img.save(os.path.join(vendor_image_dir, f"{idx}.jpg"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO vendors
        (name, category, area, description, rating, latitude, longitude, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'approved')
    """, (
        data["name"],
        data["category"],
        data["area"],
        data["description"],
        data["rating"],
        data["latitude"],
        data["longitude"]
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Vendor added"})


# ====================
# SERVE UPLOADS
# ====================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    if not filename or filename == "null":
        return "", 204
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ====================
# GET ALL APPROVED VENDORS (EXPLORE USES THIS)
# ====================

@app.route("/vendors", methods=["GET"])
def get_vendors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM vendors WHERE status='approved'")
    vendors = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(vendors)


# ====================
# LIKE VENDOR
# ====================

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


# ====================
# ML: TOP HIDDEN GEMS (NO LIMIT)
# ====================

@app.route("/ml/top-gems", methods=["GET"])
def top_hidden_gems():
    gems = []

    if not os.path.exists(ML_CSV_PATH):
        return jsonify([])

    with open(ML_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gems.append({
                "name": row["name"],
                "category": row["category"],
                "area": row["area"],
                "rating": float(row["rating"]),
                "score": round(float(row["final_score"]), 2),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
            })

    return jsonify(gems)


# ====================
# RUN
# ====================

if __name__ == "__main__":
    app.run(debug=True)
