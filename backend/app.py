from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
import os
import re
import requests
import math

from localbot.brain import get_aiml_response
from localbot.ml_intent import get_intent
from flask import request, jsonify
from flask import render_template

# ====================
# GLOBAL CHAT MEMORY
# ====================

chat_context = {}
pending_whatsapp_vendors = {}

# ====================
# CONFIG
# ====================

VERIFY_TOKEN = "hiddenlocal_verify"
WHATSAPP_TOKEN = "EAAJPzzTrFMoBQWAftZCIUyxf9ZAahqYZAXr9w4glyEAdkjgBIg7IZA2WpXDD1Sy5ZAOt4C41MZAtAou5pbNTbcdfg4WkxI8gXWVqUhrozrudgNzmbZARVILoT3ZBtRrHjhItiiU6x6x7DyV3ZBMk8YeNoLnohKZCQKI04jocKrgbNzfcaOM6u1SF9FxKSxZCKlWXAVbaDcoHtrDNGVTHs6i2UsOJ0wDxYQUB7NBF8TxtXDeJtxYdkapt0YwqPAqGBsZCUmZBb0z73e5QTD0XhxxqZBTBbCUQZDZD"
PHONE_NUMBER_ID = "857978597408213"

# ====================
# APP SETUP
# ====================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "../frontend/templates"),
    static_folder=os.path.join(BASE_DIR, "../frontend/static"),
    static_url_path="/static"
)

CORS(app)

# ====================
# DATABASE
# ====================

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="stuti123",
        database="hidden_local"
    )
    print("Connected to database:", conn.database)
    return conn

def search_vendors_from_db(category=None, area=None, limit=5):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT name, category, area FROM vendors"
    params = []

    if category:
        query += " AND category=%s"
        params.append(category)

    if area:
        query += " AND area LIKE %s"
        params.append(f"%{area}%")

    query += " LIMIT %s"
    params.append(limit)

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

# ====================
# HELPERS
# ====================

def slugify(name):
    name = name.lower().strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name

def send_whatsapp_reply(to, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    requests.post(url, headers=headers, json=payload)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in KM

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def generate_hidden_reason(v):
    if v["rating"] >= 4.5 and v["distance_km"] <= 1:
        return "🌟 Highly rated local spot very close to you, but not widely known"
    elif v["rating"] >= 4 and v["distance_km"] <= 3:
        return "🔥 Loved by locals and slightly off the main radar"
    elif v["distance_km"] <= 2:
        return "📍 Very close to you and often missed by tourists"
    else:
        return "💎 A hidden gem worth exploring"


def explain_hidden_gem(v):
    reasons = []

    if v["rating"] >= 4.5:
        reasons.append("has an excellent rating")
    elif v["rating"] >= 4:
        reasons.append("is well liked by locals")

    if v["distance_km"] <= 1:
        reasons.append("is very close to your location")
    elif v["distance_km"] <= 3:
        reasons.append("is nearby and easy to reach")

    if not reasons:
        return "It’s a lesser-known local spot worth exploring."

    return "This place " + " and ".join(reasons) + ", but isn’t crowded or commercial yet."

def send_whatsapp_reply(to, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    res = requests.post(url, headers=headers, json=payload)
    print("📤 WhatsApp reply:", res.status_code, res.text)

def extract_lat_lng_from_text(text):
    match = re.search(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", text)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None

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
# ADD VENDOR (FORM)
# ====================

@app.route("/add-vendor", methods=["POST"])
def add_vendor():
    data = request.form
    images = request.files.getlist("images")

    vendor_slug = slugify(data["name"])
    image_dir = os.path.join(app.static_folder, "images", "vendors", vendor_slug)
    os.makedirs(image_dir, exist_ok=True)

    for i, img in enumerate(images, start=1):
        img.save(os.path.join(image_dir, f"{i}.jpg"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO vendors
        (name, slug, category, area, description, rating, latitude, longitude, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'approved')
    """, (
        data["name"],
        vendor_slug,
        data["category"],
        data["area"],
        data["description"],
        data["rating"],
        float(data["latitude"]),
        float(data["longitude"])
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Vendor added successfully"})

# ====================
# CHATBOT API (AIML + ML + DB SEARCH)
# ====================

@app.route("/api/chat", methods=["POST"])
def chatbot():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip().lower()

        if not user_message:
            return jsonify({"reply": "Please say something 🙂"})

        user_id = request.remote_addr
        last_intent = chat_context.get(user_id)

        # YES FOLLOW-UP
        if user_message in ["yes", "yeah", "yep", "sure"]:
            if last_intent == "add_vendor":
                return jsonify({
                    "reply": (
                        "Here are the steps:\n"
                        "1️⃣ Open Hidden Local website\n"
                        "2️⃣ Click on 'Add Vendor'\n"
                        "3️⃣ Fill vendor details\n"
                        "4️⃣ Select location on map\n"
                        "5️⃣ Submit for review"
                    )
                })

        # INTENT DETECTION
        intent = get_intent(user_message)

        # 🔎 LIVE VENDOR SEARCH
        if intent == "search_vendor":
            category = None
            area = None

            if "food" in user_message:
                category = "Food"
            elif "shop" in user_message:
                category = "Shop"
            elif "service" in user_message:
                category = "Service"

            # AREA DETECTION (only if 'in' or 'near' used)
            if " in " in user_message:
                area = user_message.split(" in ")[-1].strip()
            elif " near " in user_message:
                area = user_message.split(" near ")[-1].strip()
            else:
                area = None


            vendors = search_vendors_from_db(category, area)

            if not vendors:
                return jsonify({
                    "reply": "😕 I couldn’t find vendors matching that. Try another area or category."
                })

            reply = "Here are some vendors I found:\n"
            for v in vendors:
                reply += f"• {v['name']} ({v['category']} – {v['area']})\n"

            return jsonify({"reply": reply})
        
        # 🔍 HIDDEN GEMS INTENT
            if any(k in user_message for k in ["hidden gem", "near me", "best place", "underrated"]):

    # fallback location (Jaipur center)
              user_lat, user_lng = 26.9124, 75.7873

              conn = get_db_connection()
              cursor = conn.cursor(dictionary=True)

              cursor.execute("""
                SELECT id, name, category, rating, latitude, longitude
                FROM vendors
                WHERE status='approved'
             """)

            vendors = cursor.fetchall()
            cursor.close()
            conn.close()

            gems = []

            for v in vendors:
              distance = haversine(
                 user_lat, user_lng,
                 float(v["latitude"]), float(v["longitude"])
               )

            if distance <= 5:
              hidden_score = (5 - v["rating"]) * 2 + distance * 1.5
              gems.append((hidden_score, v["name"]))

            gems.sort()

        if not gems:
          return jsonify({"reply": "😕 I couldn’t find hidden gems near you."})

        top = gems[:3]
        reply = "✨ Hidden gems near you:\n"

        for i, (_, name) in enumerate(top, 1):
         reply += f"{i}. {name}\n"

         return jsonify({"reply": reply})


        # AIML + ML DEFAULT RESPONSE
        response = get_aiml_response(user_message)

        if "want steps" in response.lower():
            chat_context[user_id] = "add_vendor"
        else:
            chat_context[user_id] = None

        return jsonify({"reply": response})

    except Exception as e:
        print("❌ Chatbot error:", e)
        return jsonify({"reply": "⚠️ Server error. Please try again."}), 500
    
@app.route("/api/hidden-gems", methods=["GET"])
def hidden_gems():
    try:
        user_lat = float(request.args.get("lat"))
        user_lng = float(request.args.get("lng"))
        radius = float(request.args.get("radius", 5))  # default 5 km

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, category, area, rating, latitude, longitude
            FROM vendors
            WHERE status='approved'
        """)
        vendors = cursor.fetchall()

        results = []

        for v in vendors:
            distance = haversine(
            user_lat,
            user_lng,
            float(v["latitude"]),
            float(v["longitude"])
            )

            if distance <= radius:
                hidden_score = round((5 - v["rating"]) + distance, 2)

                v["distance_km"] = round(distance, 2)
                v["hidden_score"] = hidden_score
                results.append(v)

        # 🔥 SMART SORTING
        results.sort(
            key=lambda x: (
                x["distance_km"],     # nearest first
                -x["rating"],         # higher rating
                x["hidden_score"]     # more hidden
            )
        )

        cursor.close()
        conn.close()

        seen = set()
        results = []

        for v in vendors:
            distance = haversine(
                user_lat,
                user_lng,
                float(v["latitude"]),
                float(v["longitude"])
            )

            if distance <= radius:
                key = (v["name"], float(v["latitude"]), float(v["longitude"]))
                if key in seen:
                    continue
                seen.add(key)

                hidden_score = (5 - v["rating"]) * 2 + distance * 1.5

                v["distance_km"] = round(distance, 2)
                v["hidden_score"] = round(hidden_score, 2)

                results.append(v)

        results.sort(key=lambda x: x["hidden_score"])

        return jsonify(results)

    except Exception as e:
        print("❌ Hidden Gems Error:", e)
        return jsonify({"error": "Failed to fetch hidden gems"}), 500

@app.route("/api/why-hidden", methods=["GET"])
def why_hidden():
    vendor_id = request.args.get("vendor_id")

    if not vendor_id:
        return jsonify({"error": "vendor_id required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, rating, latitude, longitude
        FROM vendors
        WHERE id=%s AND status='approved'
    """, (vendor_id,))

    v = cursor.fetchone()
    cursor.close()
    conn.close()

    if not v:
        return jsonify({"error": "Vendor not found"}), 404

    # Use Jaipur center as fallback user location
    user_lat, user_lng = 26.9124, 75.7873

    distance = haversine(
        user_lat,
        user_lng,
        float(v["latitude"]),
        float(v["longitude"])
    )

    v["distance_km"] = round(distance, 2)

    explanation = explain_hidden_gem(v)

    return jsonify({
        "vendor": v["name"],
        "reason": explanation
    })

# ====================
# GET ALL APPROVED VENDORS (FOR EXPLORE PAGE)
# ====================

@app.route("/vendors")
def get_vendors():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM vendors
        """)

        vendors = cursor.fetchall()

        safe_vendors = []

        for v in vendors:
            # 🔐 NULL SAFETY (MOST IMPORTANT)
            safe_vendors.append({
                "id": v.get("id"),
                "name": v.get("name") or "Unknown Place",
                "category": v.get("category") or "Other",
                "area": v.get("area") or "Unknown Area",
                "description": v.get("description") or "",
                "rating": v.get("rating") or 0,
                "latitude": v.get("latitude"),
                "longitude": v.get("longitude"),

                # ✅ IMAGE SAFETY
                "image": (
                    v.get("image_path")
                    if v.get("image_path") and v.get("image_path").startswith("/static")
                    else "/static/images/placeholder.jpg"
                )
            })

        cursor.close()
        conn.close()

        print("✅ Vendors sent:", len(safe_vendors))
        return jsonify(safe_vendors)

    except Exception as e:
        print("❌ /vendors error:", e)
        return jsonify([]), 200



@app.route("/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook():
    data = request.get_json()
    print("📩 Incoming:", json.dumps(data, indent=2))

    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return jsonify({"status": "no message"}), 200

        message = messages[0]
        sender = message["from"]
        msg_type = message["type"]

        # Ensure sender state exists
        if sender not in pending_whatsapp_vendors:
            pending_whatsapp_vendors[sender] = {}

        vendor = pending_whatsapp_vendors[sender]

        # ================= TEXT =================
        if msg_type == "text":
            text = message["text"]["body"].strip()
            text_lower = text.lower()

            print("📝 Text:", text)

            if text_lower.startswith("add"):
                vendor.clear()
                send_whatsapp_reply(
                    sender,
                    "🧾 Vendor details bhejo is format me:\n\n"
                    "Name:\nCategory:\nArea:\nRating:\nDescription:\n\n"
                    "📍 Uske baad location bhejo (map / live location)"
                )
                return jsonify({"status": "add started"}), 200

            # Parse key:value lines
            for line in text.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    vendor[k.strip().lower()] = v.strip()

            pending_whatsapp_vendors[sender] = vendor
            send_whatsapp_reply(sender, "📍 Ab location bhejo (WhatsApp map se)")
            return jsonify({"status": "details saved"}), 200

        # ================= LOCATION =================
        if msg_type == "location":
            lat = message["location"]["latitude"]
            lng = message["location"]["longitude"]

            vendor["latitude"] = lat
            vendor["longitude"] = lng

            # Save to DB
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO pending_vendors
                (name, category, area, rating, description, latitude, longitude)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                vendor.get("name"),
                vendor.get("category"),
                vendor.get("area"),
                int(vendor.get("rating", 0)),
                vendor.get("description"),
                float(lat),
                float(lng)
            ))

            conn.commit()
            cursor.close()
            conn.close()

            send_whatsapp_reply(sender, "✅ Vendor submitted! Admin approval pending 🙌")
            pending_whatsapp_vendors.pop(sender, None)

            return jsonify({"status": "vendor saved"}), 200

        # ================= IMAGE =================
        if msg_type == "image":
            send_whatsapp_reply(sender, "Image recieved. Now send text.")
            return jsonify({"status": "image received"}), 200

    except Exception as e:
        print("❌ Error:", e)

    return jsonify({"status": "ok"}), 200

@app.route("/admin")
def admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM pending_vendors")
    vendors = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("admin_vendors.html", vendors=vendors)

@app.route("/admin/vendor/<int:id>/approve", methods=["POST"])
def approve_vendor(id):
    print("Approve Clicked for ID:",id)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1️⃣ Fetch pending vendor
    cursor.execute(
        "SELECT * FROM pending_vendors WHERE id = %s",
        (id,)
    )
    v = cursor.fetchone()

    if not v:
        cursor.close()
        conn.close()
        print("Vendor not found")
        return "Vendor not found", 404

    # 2️⃣ Insert into main vendors table
    cursor.execute("""
        INSERT INTO vendors
        (name, category, area, rating, description, latitude, longitude, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'approved')
    """, (
        v["name"],
        v["category"],
        v["area"],
        v["rating"],
        v["description"],
        v["latitude"],
        v["longitude"]
    ))

    # 3️⃣ Remove from pending
    cursor.execute(
        "DELETE FROM pending_vendors WHERE id = %s",
        (id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status" : "approved"}),200

@app.route("/admin/vendor/<int:id>/reject", methods=["POST"])
def reject_vendor(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM pending_vendors WHERE id = %s",
        (id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status" : "rejected"}),200
# ====================
# RUN
# ====================

if __name__ == "__main__":
    app.run(debug=True)
