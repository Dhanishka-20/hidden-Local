from flask import Flask, render_template, request, redirect
import pymysql

app = Flask(__name__)

# ================= DATABASE CONNECTION =================
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",          
        password="cookie@123", 
        database="hidden_local",
        cursorclass=pymysql.cursors.DictCursor
    )

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")

# ================= EXPLORE =================
@app.route("/explore")
def explore():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, city, category, description, lat, lng
        FROM hidden_places
    """)
    places = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("explore.html", places=places)

# ================= ADD PLACE =================
@app.route("/add-place", methods=["GET", "POST"])
def add_place():
    if request.method == "POST":
        name = request.form["name"]
        city = request.form["city"]
        category = request.form["category"]
        description = request.form["description"]
        lat = request.form.get("lat")
        lng = request.form.get("lng")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO hidden_places
            (name, city, category, description, lat, lng)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, city, category, description, lat, lng))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/explore")

    return render_template("add_place.html")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
