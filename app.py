import json
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
WHATSAPP_TOKEN = "EAAJPzzTrFMoBQiyVvJFoUCPQS3xYWsScH6lxtXmtMPpAo0owDHCOTJkcZAv0rfYFZCVEMtc04XErBgDozDaFkf8MHgHdGbR2Rx3V3OC40AtRZCExWI83KZCRij3reZBmndtz2G35JupovvdCZAUf20ujXZBNT7iiqlSqB0Ceykgi7AMJKbPrNZCuwkPBUK1RdlF1RAgh7bZAP7l8xWYn15JTwgpA2q62o5MAgMFgMN0ZBPjPZA6ZAiVmncQNCQx4hWitgSJf5GboZCahp2hzfgVZCJYqjAhwZDZD"
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
        password="cookie@123",
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
        return " Highly rated local spot very close to you, but not widely known"
    elif v["rating"] >= 4 and v["distance_km"] <= 3:
        return " Loved by locals and slightly off the main radar"
    elif v["distance_km"] <= 2:
        return " Very close to you and often missed by tourists"
    else:
        return " A hidden gem worth exploring"


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
    print(" WhatsApp reply:", res.status_code, res.text)

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

    vendor_slug = slugify(data.get("name"))
    image_dir = os.path.join(app.static_folder, "images", "vendors", vendor_slug)
    os.makedirs(image_dir, exist_ok=True)

    image_path = None
    if images and images[0].filename != "":
        image_path = f"/static/images/vendors/{vendor_slug}/1.jpg"

        for i, img in enumerate(images, start=1):
            img.save(os.path.join(image_dir, f"{i}.jpg"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pending_vendors
        (name, category, area, rating, description, latitude, longitude, image_path)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data.get("name"),
        data.get("category"),
        data.get("area"),
        int(data.get("rating")),
        data.get("description"),
        float(data.get("latitude")),
        float(data.get("longitude")),
        image_path
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Vendor submitted for approval"})
# ====================
# CHATBOT API (AIML + ML + DB SEARCH)
# ====================

@app.route("/api/chat", methods=["POST"])
def chatbot():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip().lower()

        if not user_message:
            return jsonify({"reply": "Please say something "})

        # 1️⃣ Try ML intent detection
        try:
            intent = get_intent(user_message)
        except Exception as e:
            print("ML Intent Error:", e)
            intent = None

        # 2️⃣ Vendor search intent
        if intent == "search_vendor":
            category = None
            area = None

            if "food" in user_message:
                category = "Food"
            elif "shop" in user_message:
                category = "Shop"
            elif "service" in user_message:
                category = "Service"
            elif "market" in user_message:
                category = "Market"

            if " in " in user_message:
                area = user_message.split(" in ")[-1].strip()
            elif " near " in user_message:
                area = user_message.split(" near ")[-1].strip()

            vendors = search_vendors_from_db(category, area)

            if not vendors:
                return jsonify({
                    "reply": " I couldn’t find places matching that. Try another area or category."
                })

            reply = " Here are some places you may like:\n"
            for v in vendors:
                reply += f"• {v['name']} ({v['category']} – {v['area']})\n"

            return jsonify({"reply": reply})

        # 3️⃣ AIML fallback (safe)
        try:
            response = get_aiml_response(user_message)
            if response:
                return jsonify({"reply": response})
        except Exception as e:
            print("AIML Error:", e)

        # 4️⃣ Final fallback
        return jsonify({
            "reply": " I can help you discover hidden local food, markets, and services. Try asking something like:\n• best food places\n• hidden markets in Jaipur"
        })

    except Exception as e:
        print(" Chatbot error:", e)
        return jsonify({"reply": "⚠️ Server error. Please try again."}), 500

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
                    "reply": " I couldn’t find vendors matching that. Try another area or category."
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
          return jsonify({"reply": " I couldn’t find hidden gems near you."})

        top = gems[:3]
        reply = " Hidden gems near you:\n"

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
        print("Chatbot error:", e)
        return jsonify({"reply": "⚠️ Server error. Please try again."}), 500
    
@app.route("/api/hidden-gems", methods=["GET"])
def hidden_gems():
    try:
        user_lat = float(request.args.get("lat"))
        user_lng = float(request.args.get("lng"))
        radius = float(request.args.get("radius", 5))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, category, area, rating, latitude, longitude
            FROM vendors
            WHERE status='approved'
        """)
        vendors = cursor.fetchall()
        cursor.close()
        conn.close()

        results = []

        for v in vendors:
            if not v["latitude"] or not v["longitude"]:
                continue

            distance = haversine(
                user_lat,
                user_lng,
                float(v["latitude"]),
                float(v["longitude"])
            )

            if distance <= radius:
                v["distance_km"] = round(distance, 2)
                v["hidden_score"] = round((5 - v["rating"]) + distance, 2)
                results.append(v)

        results.sort(key=lambda x: (x["distance_km"], -x["rating"]))

        return jsonify(results)

    except Exception as e:
        print(" Hidden Gems Error:", e)
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
        cursor.execute("SELECT * FROM vendors")
        vendors = cursor.fetchall()
        cursor.close()
        conn.close()

        safe_vendors = []

        for v in vendors:
            vendor_slug = slugify(v.get("name", ""))

            image_folder = os.path.join(
                app.static_folder,
                "images",
                "vendors",
                vendor_slug
            )

            if os.path.exists(image_folder):
                images = sorted([
                    img for img in os.listdir(image_folder)
                    if img.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
                ])
                image_url = f"/static/images/vendors/{vendor_slug}/{images[0]}" if images else "/static/images/placeholder.jpg"
            else:
                image_url = "/static/images/placeholder.jpg"

            safe_vendors.append({
                "id": v.get("id"),
                "name": v.get("name"),
                "category": v.get("category"),
                "area": v.get("area"),
                "description": v.get("description"),
                "rating": v.get("rating"),
                "latitude": v.get("latitude"),
                "longitude": v.get("longitude"),
                "image": image_url
            })

        return jsonify(safe_vendors)

    except Exception as e:
        print(" /vendors error:", e)
        return jsonify([])


@app.route("/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook():
    data = request.get_json()
    print(" Incoming:", json.dumps(data, indent=2))

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

            print(" Text:", text)

            if text_lower.startswith("add"):
                vendor.clear()
                send_whatsapp_reply(
                    sender,
                    " Vendor details bhejo is format me:\n\n"
                    "Name:\nCategory:\nArea:\nRating:\nDescription:\n\n"
                    " Uske baad location bhejo (map / live location)"
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
        print(" Error:", e)

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
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM pending_vendors WHERE id=%s", (id,))
    v = cursor.fetchone()

    if not v:
        return jsonify({"error": "Vendor not found"}), 404

    cursor.execute("""
        INSERT INTO vendors
        (name, category, area, rating, description, latitude, longitude, image_path, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'approved')
    """, (
        v["name"],
        v["category"],
        v["area"],
        v["rating"],
        v["description"],
        v["latitude"],
        v["longitude"],
        v["image_path"]
    ))

    cursor.execute("DELETE FROM pending_vendors WHERE id=%s", (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "approved"})

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
