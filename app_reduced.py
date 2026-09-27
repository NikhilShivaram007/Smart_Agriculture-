from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "smart_agriculture"


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS farmers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS crops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farmer_id INTEGER NOT NULL,
                crop_name TEXT NOT NULL,
                area REAL NOT NULL,
                planting_date TEXT NOT NULL,
                soil_type TEXT,
                irrigation_status TEXT,
                notes TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farmer_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT DEFAULT 'kg',
                location TEXT,
                description TEXT
            )
            """
        )


init_db()


@app.route("/")
def home():
    return render_template_string('''
        <h2>Smart Agriculture</h2>
        <a href="/register">Register</a> |
        <a href="/login">Login</a> |
        <a href="/dashboard">Dashboard</a>
    ''')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        phone = request.form["phone"].strip()
        password = request.form["password"].strip()

        if not name or not phone or not password:
            return "Please fill all fields."

        with get_db_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM farmers WHERE phone = ?",
                (phone,),
            ).fetchone()
            if existing:
                return "Phone already registered."

            cursor = conn.execute(
                "INSERT INTO farmers (name, phone, password) VALUES (?, ?, ?)",
                (name, phone, password),
            )
            session["farmer_id"] = cursor.lastrowid
            session["name"] = name
            session["logged_in"] = True

        return redirect(url_for("dashboard"))

    return render_template_string('''
        <h3>Register Farmer</h3>
        <form method="post">
            Name: <input name="name"><br>
            Phone: <input name="phone"><br>
            Password: <input type="password" name="password"><br>
            <button type="submit">Register</button>
        </form>
    ''')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form["phone"].strip()
        password = request.form["password"].strip()

        user = get_db_connection().execute(
            "SELECT * FROM farmers WHERE phone = ? AND password = ?",
            (phone, password),
        ).fetchone()

        if user:
            session["logged_in"] = True
            session["farmer_id"] = user["id"]
            session["name"] = user["name"]
            return redirect(url_for("dashboard"))

        return "Invalid phone or password."

    return render_template_string('''
        <h3>Login</h3>
        <form method="post">
            Phone: <input name="phone"><br>
            Password: <input type="password" name="password"><br>
            <button type="submit">Login</button>
        </form>
    ''')


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    with get_db_connection() as conn:
        crops = conn.execute(
            "SELECT * FROM crops WHERE farmer_id = ? ORDER BY id DESC",
            (session["farmer_id"],),
        ).fetchall()
        products = conn.execute(
            "SELECT * FROM market_products WHERE farmer_id = ? ORDER BY id DESC",
            (session["farmer_id"],),
        ).fetchall()

    return render_template_string('''
        <h2>Welcome, {{ name }}</h2>
        <a href="/crops">Add Crop</a> |
        <a href="/marketplace">Add Product</a> |
        <a href="/logout">Logout</a>
        <h3>My Crops</h3>
        {% if crops %}
            <ul>
            {% for c in crops %}
                <li>{{ c["crop_name"] }} - {{ c["area"] }} acres</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No crops added yet.</p>
        {% endif %}
        <h3>My Products</h3>
        {% if products %}
            <ul>
            {% for p in products %}
                <li>{{ p["product_name"] }} - ₹{{ p["price"] }}/{{ p["unit"] }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No products added yet.</p>
        {% endif %}
    ''', name=session["name"], crops=crops, products=products)


@app.route("/crops", methods=["GET", "POST"])
def crops():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO crops (farmer_id, crop_name, area, planting_date, soil_type, irrigation_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["farmer_id"],
                request.form["crop_name"].strip(),
                float(request.form["area"]),
                request.form["planting_date"],
                request.form.get("soil_type", ""),
                request.form.get("irrigation_status", ""),
                request.form.get("notes", ""),
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    return render_template_string('''
        <h3>Add Crop</h3>
        <form method="post">
            Crop Name: <input name="crop_name"><br>
            Area (acres): <input type="number" step="0.1" name="area"><br>
            Planting Date: <input type="date" name="planting_date"><br>
            Soil Type: <input name="soil_type"><br>
            Irrigation: <input name="irrigation_status"><br>
            Notes: <textarea name="notes"></textarea><br>
            <button type="submit">Save</button>
        </form>
    ''')


@app.route("/marketplace", methods=["GET", "POST"])
def marketplace():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO market_products (farmer_id, product_name, price, quantity, unit, location, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["farmer_id"],
                request.form["product_name"].strip(),
                float(request.form["price"]),
                float(request.form["quantity"]),
                request.form.get("unit", "kg"),
                request.form.get("location", ""),
                request.form.get("description", ""),
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    return render_template_string('''
        <h3>Add Product</h3>
        <form method="post">
            Product: <input name="product_name"><br>
            Price: <input type="number" step="0.01" name="price"><br>
            Quantity: <input type="number" step="0.1" name="quantity"><br>
            Unit: <input name="unit" value="kg"><br>
            Location: <input name="location"><br>
            Description: <textarea name="description"></textarea><br>
            <button type="submit">Save</button>
        </form>
    ''')


if __name__ == "__main__":
    app.run(debug=True)
