from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import webbrowser
from threading import Timer

app = Flask(__name__)

app.secret_key = "smart_farm_secret_key"


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_db_connection():

    conn = sqlite3.connect("database.db")

    conn.row_factory = sqlite3.Row

    return conn


# ==================================================
# CREATE CROP TABLE
# ==================================================

def create_crop_table():

    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS crops (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            farmer_id INTEGER NOT NULL,

            crop_name TEXT NOT NULL,

            area REAL NOT NULL,

            planting_date TEXT NOT NULL,

            crop_variety TEXT,

            growth_stage TEXT,

            irrigation_status TEXT,

            soil_condition TEXT,

            pest_status TEXT,

            notes TEXT,

            FOREIGN KEY (farmer_id)
            REFERENCES farmers(id)

        )
    """)

    conn.commit()

    conn.close()


# ==================================================
# LOGIN
# ==================================================

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        username = request.form.get("username")

        password = request.form.get("password")

        conn = get_db_connection()

        farmer = conn.execute(
            "SELECT * FROM farmers WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()

        conn.close()

        if farmer:

            session["logged_in"] = True

            session["farmer_id"] = farmer["id"]

            session["username"] = farmer["username"]

            session["full_name"] = farmer["full_name"]

            return redirect(url_for("dashboard"))

        else:

            error = "Invalid username or password."

    return render_template(
        "login.html",
        error=error
    )


# ==================================================
# REGISTER
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":

        full_name = request.form.get("full_name")

        username = request.form.get("username")

        email = request.form.get("email")

        phone = request.form.get("phone")

        password = request.form.get("password")

        conn = get_db_connection()

        existing_user = conn.execute(
            "SELECT * FROM farmers WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:

            conn.close()

            error = "Username already exists."

            return render_template(
                "register.html",
                error=error
            )

        conn.execute(
            """
            INSERT INTO farmers
            (full_name, username, email, phone, password)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                full_name,
                username,
                email,
                phone,
                password
            )
        )

        conn.commit()

        conn.close()

        return redirect(url_for("login"))

    return render_template(
        "register.html",
        error=error
    )


# ==================================================
# DASHBOARD / HOME
# ==================================================

@app.route("/dashboard")
def dashboard():

    if not session.get("logged_in"):

        return redirect(url_for("login"))

    return render_template("dashboard.html")


# ==================================================
# CROP RECOMMENDATION
# ==================================================

@app.route("/crop-recommendation", methods=["GET", "POST"])
def crop_recommendation():

    if not session.get("logged_in"):

        return redirect(url_for("login"))

    recommendation = None

    suitability = 0

    reason = ""

    water_need = ""

    advice = ""

    rice_score = 0

    maize_score = 0

    ragi_score = 0

    cotton_score = 0

    wheat_score = 0

    if request.method == "POST":

        try:

            nitrogen = float(request.form.get("nitrogen", 0))

            phosphorus = float(request.form.get("phosphorus", 0))

            potassium = float(request.form.get("potassium", 0))

            temperature = float(request.form.get("temperature", 0))

            humidity = float(request.form.get("humidity", 0))

            ph = float(request.form.get("ph", 0))

            rainfall = float(request.form.get("rainfall", 0))

        except (ValueError, TypeError):

            return render_template(
                "crop_recommendation.html",
                error="Please enter valid numbers."
            )

        # ==================================================
        # CROP SCORING
        # ==================================================

        scores = {

            "Rice": 0,

            "Maize": 0,

            "Ragi": 0,

            "Cotton": 0,

            "Wheat": 0

        }

        # --------------------------------------------------
        # RICE
        # --------------------------------------------------

        if 20 <= temperature <= 35:
            scores["Rice"] += 20

        if humidity >= 70:
            scores["Rice"] += 20

        if rainfall >= 150:
            scores["Rice"] += 25

        if 5.5 <= ph <= 7.5:
            scores["Rice"] += 15

        if nitrogen >= 60:
            scores["Rice"] += 10

        if phosphorus >= 30:
            scores["Rice"] += 5

        if potassium >= 30:
            scores["Rice"] += 5

        # --------------------------------------------------
        # MAIZE
        # --------------------------------------------------

        if 18 <= temperature <= 32:
            scores["Maize"] += 20

        if 50 <= humidity <= 80:
            scores["Maize"] += 15

        if 50 <= rainfall <= 150:
            scores["Maize"] += 20

        if 5.5 <= ph <= 7.5:
            scores["Maize"] += 15

        if nitrogen >= 50:
            scores["Maize"] += 15

        if phosphorus >= 30:
            scores["Maize"] += 10

        if potassium >= 25:
            scores["Maize"] += 5

        # --------------------------------------------------
        # RAGI
        # --------------------------------------------------

        if 20 <= temperature <= 32:
            scores["Ragi"] += 20

        if 40 <= humidity <= 75:
            scores["Ragi"] += 15

        if 40 <= rainfall <= 100:
            scores["Ragi"] += 20

        if 5.5 <= ph <= 7.5:
            scores["Ragi"] += 20

        if nitrogen >= 30:
            scores["Ragi"] += 10

        if phosphorus >= 20:
            scores["Ragi"] += 10

        if potassium >= 20:
            scores["Ragi"] += 5

        # --------------------------------------------------
        # COTTON
        # --------------------------------------------------

        if 21 <= temperature <= 35:
            scores["Cotton"] += 20

        if 50 <= humidity <= 75:
            scores["Cotton"] += 15

        if 50 <= rainfall <= 120:
            scores["Cotton"] += 20

        if 5.5 <= ph <= 8:
            scores["Cotton"] += 15

        if nitrogen >= 40:
            scores["Cotton"] += 10

        if phosphorus >= 25:
            scores["Cotton"] += 10

        if potassium >= 25:
            scores["Cotton"] += 10

        # --------------------------------------------------
        # WHEAT
        # --------------------------------------------------

        if 15 <= temperature <= 25:
            scores["Wheat"] += 20

        if 40 <= humidity <= 70:
            scores["Wheat"] += 15

        if 40 <= rainfall <= 100:
            scores["Wheat"] += 20

        if 6 <= ph <= 7.5:
            scores["Wheat"] += 20

        if nitrogen >= 50:
            scores["Wheat"] += 10

        if phosphorus >= 25:
            scores["Wheat"] += 10

        if potassium >= 25:
            scores["Wheat"] += 5

        # ==================================================
        # FIND BEST CROP
        # ==================================================

        recommendation = max(
            scores,
            key=scores.get
        )

        suitability = scores[recommendation]

        # ==================================================
        # CROP INFORMATION
        # ==================================================

        crop_information = {

            "Rice": {

                "reason":
                    "Rice is suitable because the temperature, humidity, rainfall and soil conditions are favorable.",

                "water":
                    "High",

                "advice":
                    "Rice needs plenty of water. Maintain proper irrigation and monitor pests."

            },

            "Maize": {

                "reason":
                    "The temperature, humidity, soil pH and rainfall conditions are suitable for Maize.",

                "water":
                    "Medium",

                "advice":
                    "Provide regular irrigation and ensure proper nitrogen supply."

            },

            "Ragi": {

                "reason":
                    "Ragi can grow well under moderate rainfall and suitable soil pH conditions.",

                "water":
                    "Low to Medium",

                "advice":
                    "Avoid excess watering and maintain good soil nutrients."

            },

            "Cotton": {

                "reason":
                    "The warm temperature and moderate rainfall conditions are suitable for Cotton.",

                "water":
                    "Medium",

                "advice":
                    "Provide balanced irrigation and monitor the crop regularly for pests."

            },

            "Wheat": {

                "reason":
                    "The cooler temperature and moderate rainfall conditions are suitable for Wheat.",

                "water":
                    "Medium",

                "advice":
                    "Maintain proper irrigation and provide sufficient nitrogen during growth."

            }

        }

        reason = crop_information[recommendation]["reason"]

        water_need = crop_information[recommendation]["water"]

        advice = crop_information[recommendation]["advice"]

        # ==================================================
        # COMPARISON SCORES
        # ==================================================

        rice_score = scores["Rice"]

        maize_score = scores["Maize"]

        ragi_score = scores["Ragi"]

        cotton_score = scores["Cotton"]

        wheat_score = scores["Wheat"]

    return render_template(
        "crop_recommendation.html",

        recommendation=recommendation,

        suitability=suitability,

        reason=reason,

        water_need=water_need,

        advice=advice,

        rice_score=rice_score,

        maize_score=maize_score,

        ragi_score=ragi_score,

        cotton_score=cotton_score,

        wheat_score=wheat_score
    )


# ==================================================
# CROP MANAGEMENT
# ==================================================

@app.route("/crop-management")
def crop_management():

    if not session.get("logged_in"):

        return redirect(url_for("login"))

    return render_template(
        "crop_management.html"
    )


# ==================================================
# ADD CROP
# ==================================================

@app.route("/add-crop", methods=["POST"])
def add_crop():

    if not session.get("logged_in"):

        return redirect(url_for("login"))

    crop_name = request.form.get("crop_name")

    area = request.form.get("area")

    planting_date = request.form.get("planting_date")

    crop_variety = request.form.get("crop_variety")

    growth_stage = request.form.get("growth_stage")

    irrigation_status = request.form.get("irrigation_status")

    soil_condition = request.form.get("soil_condition")

    pest_status = request.form.get("pest_status")

    notes = request.form.get("notes")

    if not crop_name or not area or not planting_date:

        return redirect(
            url_for("crop_management")
        )

    try:

        area = float(area)

    except ValueError:

        return redirect(
            url_for("crop_management")
        )

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO crops
        (
            farmer_id,
            crop_name,
            area,
            planting_date,
            crop_variety,
            growth_stage,
            irrigation_status,
            soil_condition,
            pest_status,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (
            session["farmer_id"],
            crop_name,
            area,
            planting_date,
            crop_variety,
            growth_stage,
            irrigation_status,
            soil_condition,
            pest_status,
            notes
        )
    )

    conn.commit()

    conn.close()

    return redirect(
        url_for("crop_management")
    )


# ==================================================
# FARM SHOP
# ==================================================

@app.route("/shop")
def shop():

    if not session.get("logged_in"):

        return redirect(url_for("login"))

    return render_template(
        "shop.html"
    )


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ==================================================
# OPEN BROWSER AUTOMATICALLY
# ==================================================

def open_browser():

    webbrowser.open_new(
        "http://127.0.0.1:5000/login"
    )


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":

    create_crop_table()

    Timer(
        1,
        open_browser
    ).start()

    app.run(debug=True)

