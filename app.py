from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import webbrowser
import json
import urllib.request
import urllib.parse
from threading import Timer
from datetime import datetime
import os
from werkzeug.utils import secure_filename
\
app = Flask(__name__)
app.secret_key = "smart_farm_secret_key"
\
\
\
\
\
\
def get_db_connection():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "database.db")
    \
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
def create_users_table():
    conn = get_db_connection()
    \
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone_number TEXT,
            vehicle_number TEXT,
            password TEXT NOT NULL
        )
    """)
    \
    conn.commit()
    conn.close()
def create_activity_table():
    conn = get_db_connection()
    \
    conn.execute("""
        CREATE TABLE IF NOT EXISTS farmer_activities(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            crop_name TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            activity_date TEXT NOT NULL,
            reminder_time TEXT,
            priority TEXT DEFAULT 'Medium',
            description TEXT,
            location TEXT,
            assigned_person TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    \
    conn.commit()
    conn.close()
def create_expenses_table():
    conn = get_db_connection()
    \
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            expense_date TEXT NOT NULL,
            crop TEXT,
            payment_method TEXT,
            receipt_number TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    \
    conn.commit()
    conn.close()
def create_farm_waste_table():
    conn = get_db_connection()
    \
    conn.execute("""
        CREATE TABLE IF NOT EXISTS farm_waste(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            waste_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            waste_date TEXT NOT NULL,
            source TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    \
    conn.commit()
    conn.close()
def create_alerts_table():
    \
    conn = get_db_connection()
    \
    conn.execute("""
        CREATE TABLE IF NOT EXISTS farming_alerts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            alert_date TEXT NOT NULL,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Unread',
            related_activity_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    \
\
    columns = conn.execute(\
        "PRAGMA table_info(farming_alerts)"\
    ).fetchall()
    \
    existing_columns = [column["name"] for column in columns]
    \
    if "related_activity_id" not in existing_columns:
        conn.execute("""
            ALTER TABLE farming_alerts
            ADD COLUMN related_activity_id INTEGER
        """)
    conn.commit()
    conn.close()
def create_expenses_table():
    conn = get_db_connection()
    \
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            expense_date TEXT NOT NULL,
            crop TEXT,
            payment_method TEXT,
            receipt_number TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    \
    conn.commit()
    conn.close()
def create_crop_table():
    conn = get_db_connection()
    \
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    \
    columns = conn.execute("PRAGMA table_info(crops)").fetchall()
    existing = [column["name"] for column in columns]
    \
    for name, data_type in {\
        "soil_type": "TEXT",\
        "irrigation_method": "TEXT",\
        "harvest_date": "TEXT"\
    }.items():
        \
        if name not in existing:
            conn.execute(\
                f"ALTER TABLE crops ADD COLUMN {name} {data_type}"\
            )
    conn.commit()
    conn.close()
MARKETPLACE_CATEGORIES = [\
    "All Products",\
    "Fruits",\
    "Vegetables",\
    "Grains",\
    "Pulses",\
    "Spices",\
    "Dairy",\
    "Farm Equipment",\
    "Other Farm Products"\
]
PRODUCTS_BY_CATEGORY = {\
    "Fruits": [\
        "Apple", "Banana", "Mango", "Orange", "Grapes",\
        "Papaya", "Guava", "Pomegranate", "Watermelon",\
        "Pineapple", "Jackfruit", "Sapota", "Custard Apple",\
        "Dragon Fruit", "Strawberry", "Muskmelon", "Kiwi",\
        "Lemon", "Sweet Lime", "Coconut"\
    ],\
    "Vegetables": [\
        "Tomato", "Potato", "Onion", "Carrot", "Brinjal",\
        "Cabbage", "Cauliflower", "Beans", "Beetroot",\
        "Radish", "Spinach", "Drumstick", "Capsicum",\
        "Green Chilli", "Lady Finger", "Bottle Gourd",\
        "Bitter Gourd", "Pumpkin", "Cucumber", "Peas"\
    ],\
    "Grains": [\
        "Rice", "Ragi", "Wheat", "Maize",\
        "Jowar", "Bajra", "Barley", "Oats"\
    ],\
    "Pulses": [\
        "Toor Dal", "Green Gram", "Black Gram", "Chickpeas",\
        "Bengal Gram", "Masoor Dal", "Horse Gram", "Cowpea"\
    ],\
    "Spices": [\
        "Red Chilli", "Turmeric", "Black Pepper",\
        "Coriander", "Cardamom", "Cloves", "Cumin",\
        "Ginger", "Garlic"\
    ],\
    "Dairy": [\
        "Milk", "Curd", "Paneer", "Buttermilk", "Ghee"\
    ],\
    "Farm Equipment": [\
        "Tractor", "Power Tiller", "Cultivator", "Seed Drill",\
        "Plough", "Rotavator", "Sprayer", "Water Pump",\
        "Harvester", "Threshing Machine", "Drip Irrigation Kit",\
        "Agricultural Tools"\
    ],\
    "Other Farm Products": [\
        "Honey", "Jaggery", "Coconut Oil", "Groundnut",\
        "Sesame", "Sunflower Seeds", "Farm Eggs"\
    ]\
}
DEFAULT_MARKETPLACE_PRODUCTS = [\
    ("Apple", 120, 50, "kg", "Karnataka", "Fresh farm apples", "Fruits"),\
    ("Banana", 60, 100, "kg", "Karnataka", "Fresh ripe bananas", "Fruits"),\
    ("Mango", 100, 75, "kg", "Karnataka", "Fresh seasonal mangoes", "Fruits"),\
    ("Orange", 90, 60, "kg", "Karnataka", "Fresh oranges", "Fruits"),\
    ("Grapes", 110, 50, "kg", "Karnataka", "Fresh farm grapes", "Fruits"),\
    ("Papaya", 50, 80, "kg", "Karnataka", "Fresh papaya", "Fruits"),\
    ("Guava", 70, 60, "kg", "Karnataka", "Fresh guava", "Fruits"),\
    ("Pomegranate", 150, 40, "kg", "Karnataka", "Fresh pomegranate", "Fruits"),\
    ("Watermelon", 35, 80, "kg", "Karnataka", "Fresh watermelons", "Fruits"),\
    ("Pineapple", 80, 50, "kg", "Karnataka", "Fresh pineapples", "Fruits"),\
    ("Tomato", 40, 100, "kg", "Karnataka", "Fresh farm tomatoes", "Vegetables"),\
    ("Potato", 35, 100, "kg", "Karnataka", "Fresh potatoes", "Vegetables"),\
    ("Onion", 45, 100, "kg", "Karnataka", "Fresh farm onions", "Vegetables"),\
    ("Carrot", 50, 75, "kg", "Karnataka", "Fresh carrots", "Vegetables"),\
    ("Brinjal", 45, 60, "kg", "Karnataka", "Fresh brinjal", "Vegetables"),\
    ("Cabbage", 35, 70, "kg", "Karnataka", "Fresh cabbage", "Vegetables"),\
    ("Cauliflower", 55, 60, "kg", "Karnataka", "Fresh cauliflower", "Vegetables"),\
    ("Beans", 80, 50, "kg", "Karnataka", "Fresh green beans", "Vegetables"),\
    ("Beetroot", 60, 50, "kg", "Karnataka", "Fresh beetroot", "Vegetables"),\
    ("Radish", 40, 50, "kg", "Karnataka", "Fresh radish", "Vegetables"),\
    ("Spinach", 30, 50, "kg", "Karnataka", "Fresh spinach", "Vegetables"),\
    ("Capsicum", 90, 40, "kg", "Karnataka", "Fresh capsicum", "Vegetables"),\
    ("Green Chilli", 70, 40, "kg", "Karnataka", "Fresh green chilli", "Vegetables"),\
    ("Lady Finger", 60, 50, "kg", "Karnataka", "Fresh lady finger", "Vegetables"),\
    ("Cucumber", 40, 60, "kg", "Karnataka", "Fresh cucumbers", "Vegetables"),\
    ("Rice", 65, 100, "kg", "Karnataka", "Quality farm rice", "Grains"),\
    ("Ragi", 55, 80, "kg", "Karnataka", "Healthy farm ragi", "Grains"),\
    ("Wheat", 50, 100, "kg", "Karnataka", "Fresh wheat grain", "Grains"),\
    ("Maize", 35, 100, "kg", "Karnataka", "Fresh maize", "Grains"),\
    ("Toor Dal", 140, 50, "kg", "Karnataka", "Farm packed toor dal", "Pulses"),\
    ("Green Gram", 120, 50, "kg", "Karnataka", "Fresh green gram", "Pulses"),\
    ("Chickpeas", 110, 50, "kg", "Karnataka", "Quality chickpeas", "Pulses"),\
    ("Turmeric", 180, 40, "kg", "Karnataka", "Natural farm turmeric", "Spices"),\
    ("Black Pepper", 650, 20, "kg", "Karnataka", "Farm grown black pepper", "Spices"),\
    ("Coriander", 160, 30, "kg", "Karnataka", "Fresh coriander", "Spices"),\
    ("Ginger", 120, 40, "kg", "Karnataka", "Fresh farm ginger", "Spices"),\
    ("Garlic", 150, 40, "kg", "Karnataka", "Fresh garlic", "Spices"),\
    ("Milk", 60, 100, "litre", "Karnataka", "Fresh farm milk", "Dairy"),\
    ("Curd", 70, 50, "kg", "Karnataka", "Fresh farm curd", "Dairy"),\
    ("Paneer", 320, 30, "kg", "Karnataka", "Fresh paneer", "Dairy"),\
    ("Honey", 350, 25, "kg", "Karnataka", "Natural farm honey", "Other Farm Products"),\
    ("Jaggery", 80, 50, "kg", "Karnataka", "Natural jaggery", "Other Farm Products"),\
    ("Farm Eggs", 8, 200, "piece", "Karnataka", "Fresh farm eggs", "Other Farm Products")\
]
\
\
\
def create_marketplace_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS market_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT DEFAULT 'kg',
            location TEXT,
            description TEXT,
            image TEXT,
            category TEXT DEFAULT 'Other Farm Products',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS marketplace_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Placed',
            payment_status TEXT DEFAULT 'Pending',
            payment_method TEXT,
            payment_reference TEXT,
            delivery_name TEXT,
            delivery_phone TEXT,
            delivery_address TEXT,
            latitude REAL,
            longitude REAL,
            location_method TEXT DEFAULT 'address',
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS marketplace_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            farmer_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT,
            price REAL NOT NULL,
            subtotal REAL NOT NULL
        )
    """)
    columns = conn.execute(\
        "PRAGMA table_info(market_products)"\
    ).fetchall()
    existing = [column["name"] for column in columns]
    if "category" not in existing:
        conn.execute("""
            ALTER TABLE market_products
            ADD COLUMN category TEXT DEFAULT 'Other Farm Products'
        """)
    order_columns = conn.execute(\
        "PRAGMA table_info(marketplace_orders)"\
    ).fetchall()
    existing_orders = [column["name"] for column in order_columns]
    new_order_columns = {\
        "payment_status": "TEXT DEFAULT 'Pending'",\
        "payment_method": "TEXT",\
        "payment_reference": "TEXT",\
        "delivery_name": "TEXT",\
        "delivery_phone": "TEXT",\
        "delivery_address": "TEXT",\
        "latitude": "REAL",\
        "longitude": "REAL",\
        "location_method": "TEXT DEFAULT 'address'"\
    }
    for name, data_type in new_order_columns.items():
        if name not in existing_orders:
            conn.execute(\
                f"ALTER TABLE marketplace_orders ADD COLUMN {name} {data_type}"\
            )
    conn.commit()
    conn.close()
def create_default_marketplace_products(farmer_id):
    conn = get_db_connection()
    try:
        for product in DEFAULT_MARKETPLACE_PRODUCTS:
            exists = conn.execute("""
                SELECT id
                FROM market_products
                WHERE product_name = ?
                AND category = ?
                LIMIT 1
            """, (product[0], product[6])).fetchone()
            \
            if exists:
                continue
            conn.execute("""
                INSERT INTO market_products
                (
                    farmer_id, product_name, price, quantity,
                    unit, location, description, image, category
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (\
                farmer_id,\
                product[0],\
                product[1],\
                product[2],\
                product[3],\
                product[4],\
                product[5],\
                None,\
                product[6]\
            ))
        conn.commit()
    except Exception as error:
        print("DEFAULT MARKETPLACE PRODUCT ERROR:", error)
    finally:
        conn.close()
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db_connection()
        farmer = conn.execute("""
            SELECT *
            FROM farmers
            WHERE username = ?
            AND password = ?
        """, (username, password)).fetchone()
        conn.close()
        if farmer:
            session["logged_in"] = True
            session["farmer_id"] = farmer["id"]
            session["username"] = farmer["username"]
            session["full_name"] = farmer["full_name"]
            return redirect(url_for("dashboard"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        conn = get_db_connection()
        existing = conn.execute("""
            SELECT *
            FROM farmers
            WHERE username = ?
        """, (username,)).fetchone()
        if existing:
            conn.close()
            return render_template(\
                "register.html",\
                error="Username already exists."\
            )
        conn.execute("""
            INSERT INTO farmers
            (full_name, username, email, phone, password)
            VALUES (?, ?, ?, ?, ?)
        """, (full_name, username, email, phone, password))
        conn.commit()
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html", error=error)
@app.route("/add-expense", methods=["GET", "POST"])
def add_expense():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount = request.form.get("amount", "").strip()
        expense_date = request.form.get("expense_date", "").strip()
        crop = request.form.get("crop", "").strip()
        payment_method = request.form.get("payment_method", "").strip()
        receipt_number = request.form.get("receipt_number", "").strip()
        description = request.form.get("description", "").strip()
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return render_template(\
                "add_expense.html",\
                error="Please enter a valid expense amount."\
            )
        if not category or not expense_date:
            return render_template(\
                "add_expense.html",\
                error="Please enter category and expense date."\
            )
        try:
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO expenses
                (
                    farmer_id,
                    category,
                    amount,
                    expense_date,
                    crop,
                    payment_method,
                    receipt_number,
                    description
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (\
                session["farmer_id"],\
                category,\
                amount,\
                expense_date,\
                crop,\
                payment_method,\
                receipt_number,\
                description\
            ))
            conn.commit()
            conn.close()
            return redirect(url_for("expense_management"))
        except Exception as error:
            print("EXPENSE SAVE ERROR:", error)
            try:
                conn.close()
            except Exception:
                pass
            return render_template(\
                "add_expense.html",\
                error="Unable to save expense."\
            )
    return render_template("add_expense.html")
@app.route("/expense-management")
def expense_management():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    expenses = conn.execute("""
        SELECT *
        FROM expenses
        WHERE farmer_id = ?
        ORDER BY id DESC
    """, (\
        session["farmer_id"],\
    )).fetchall()
    total_expense = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE farmer_id = ?
    """, (\
        session["farmer_id"],\
    )).fetchone()[0]
    current_month = datetime.now().strftime("%Y-%m")
    monthly_expense = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE farmer_id = ?
        AND substr(expense_date, 1, 7) = ?
    """, (\
        session["farmer_id"],\
        current_month\
    )).fetchone()[0]
    conn.close()
    return render_template(\
        "expense_management.html",\
        expenses=expenses,\
        total_expense=total_expense,\
        monthly_expense=monthly_expense\
    )
@app.route("/farm-profit-loss")
def farm_profit_loss():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    farmer_id = session["farmer_id"]
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    conn = get_db_connection()
    \
\
\
    date_condition_sales = ""
    date_condition_expenses = ""
    sales_params = [farmer_id]
    expense_params = [farmer_id]
    if start_date:
        date_condition_sales += " AND DATE(o.order_date) >= ? "
        sales_params.append(start_date)
        date_condition_expenses += " AND expense_date >= ? "
        expense_params.append(start_date)
    if end_date:
        date_condition_sales += " AND DATE(o.order_date) <= ? "
        sales_params.append(end_date)
        date_condition_expenses += " AND expense_date <= ? "
        expense_params.append(end_date)
    total_income = conn.execute("""
        SELECT COALESCE(SUM(oi.subtotal), 0)
        FROM marketplace_order_items oi
        JOIN marketplace_orders o
            ON oi.order_id = o.id
        WHERE oi.farmer_id = ?
        AND o.payment_status = 'Paid'
    """ + date_condition_sales, sales_params).fetchone()[0]
    \
\
\
    total_expenses = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE farmer_id = ?
    """ + date_condition_expenses, expense_params).fetchone()[0]
    profit_loss = float(total_income) - float(total_expenses)
    \
\
\
    sales = conn.execute("""
        SELECT
            DATE(o.order_date) AS sale_date,
            oi.product_name AS crop,
            SUM(oi.quantity) AS quantity,
            oi.unit AS unit,
            SUM(oi.subtotal) AS income
        FROM marketplace_order_items oi
        JOIN marketplace_orders o
            ON oi.order_id = o.id
        WHERE oi.farmer_id = ?
        AND o.payment_status = 'Paid'
    """ + date_condition_sales + """
        GROUP BY DATE(o.order_date), oi.product_name, oi.unit
        ORDER BY sale_date DESC
    """, sales_params).fetchall()
    \
\
\
    expense_rows = conn.execute("""
        SELECT
            expense_date,
            category,
            crop,
            amount,
            payment_method,
            description
        FROM expenses
        WHERE farmer_id = ?
    """ + date_condition_expenses + """
        ORDER BY expense_date DESC, id DESC
    """, expense_params).fetchall()
    \
\
\
    crop_income = conn.execute("""
        SELECT
            oi.product_name AS crop,
            SUM(oi.subtotal) AS income
        FROM marketplace_order_items oi
        JOIN marketplace_orders o
            ON oi.order_id = o.id
        WHERE oi.farmer_id = ?
        AND o.payment_status = 'Paid'
    """ + date_condition_sales + """
        GROUP BY oi.product_name
    """, sales_params).fetchall()
    crop_expense = conn.execute("""
        SELECT
            COALESCE(NULLIF(crop, ''), 'Farm') AS crop,
            SUM(amount) AS expense
        FROM expenses
        WHERE farmer_id = ?
    """ + date_condition_expenses + """
        GROUP BY COALESCE(NULLIF(crop, ''), 'Farm')
    """, expense_params).fetchall()
    crop_data = {}
    for row in crop_income:
        crop = row["crop"] or "Farm"
        crop_data[crop] = {\
            "crop": crop,\
            "income": float(row["income"] or 0),\
            "expense": 0\
        }
    for row in crop_expense:
        crop = row["crop"] or "Farm"
        if crop not in crop_data:
            crop_data[crop] = {\
                "crop": crop,\
                "income": 0,\
                "expense": 0\
            }
        crop_data[crop]["expense"] += float(\
            row["expense"] or 0\
        )
    crop_report = []
    for item in crop_data.values():
        item["profit"] = (\
            item["income"] - item["expense"]\
        )
        crop_report.append(item)
    crop_report.sort(\
        key=lambda x: x["profit"],\
        reverse=True\
    )
    \
\
\
    monthly_income = conn.execute("""
        SELECT
            strftime('%Y-%m', o.order_date) AS month,
            SUM(oi.subtotal) AS income
        FROM marketplace_order_items oi
        JOIN marketplace_orders o
            ON oi.order_id = o.id
        WHERE oi.farmer_id = ?
        AND o.payment_status = 'Paid'
    """ + date_condition_sales + """
        GROUP BY strftime('%Y-%m', o.order_date)
        ORDER BY month DESC
    """, sales_params).fetchall()
    monthly_expenses = conn.execute("""
        SELECT
            substr(expense_date, 1, 7) AS month,
            SUM(amount) AS expense
        FROM expenses
        WHERE farmer_id = ?
    """ + date_condition_expenses + """
        GROUP BY substr(expense_date, 1, 7)
        ORDER BY month DESC
    """, expense_params).fetchall()
    monthly_data = {}
    for row in monthly_income:
        month = row["month"]
        monthly_data[month] = {\
            "month": month,\
            "income": float(row["income"] or 0),\
            "expense": 0\
        }
    for row in monthly_expenses:
        month = row["month"]
        if month not in monthly_data:
            monthly_data[month] = {\
                "month": month,\
                "income": 0,\
                "expense": 0\
            }
        monthly_data[month]["expense"] += float(\
            row["expense"] or 0\
        )
    monthly_report = []
    for item in monthly_data.values():
        item["profit"] = (\
            item["income"] - item["expense"]\
        )
        monthly_report.append(item)
    monthly_report.sort(\
        key=lambda x: x["month"] or "",\
        reverse=True\
    )
    \
\
\
    chart_labels = []
    chart_income = []
    chart_expenses = []
    chart_profit = []
    chart_data = list(reversed(monthly_report))
    for item in chart_data:
        chart_labels.append(item["month"])
        chart_income.append(round(item["income"], 2))
        chart_expenses.append(round(item["expense"], 2))
        chart_profit.append(round(item["profit"], 2))
    report_data = {}
    for sale in sales:
        key = (\
            sale["sale_date"],\
            sale["crop"] or "Farm"\
        )
        if key not in report_data:
            report_data[key] = {\
                "date": sale["sale_date"],\
                "crop": sale["crop"] or "Farm",\
                "income": 0,\
                "expense": 0\
            }
        report_data[key]["income"] += float(\
            sale["income"] or 0\
        )
    for expense in expense_rows:
        key = (\
            expense["expense_date"],\
            expense["crop"] or "Farm"\
        )
        if key not in report_data:
            report_data[key] = {\
                "date": expense["expense_date"],\
                "crop": expense["crop"] or "Farm",\
                "income": 0,\
                "expense": 0\
            }
        report_data[key]["expense"] += float(\
            expense["amount"] or 0\
        )
    report = []
    for item in report_data.values():
        item["profit"] = (\
            item["income"] - item["expense"]\
        )
        report.append(item)
    report.sort(\
        key=lambda x: x["date"] or "",\
        reverse=True\
    )
    conn.close()
    return render_template(\
        "farm_profit_loss.html",\
        total_income=round(float(total_income), 2),\
        total_expenses=round(float(total_expenses), 2),\
        profit_loss=round(float(profit_loss), 2),\
        report=report,\
        crop_report=crop_report,\
        monthly_report=monthly_report,\
        sales=sales,\
        expense_rows=expense_rows,\
        chart_labels=json.dumps(chart_labels),\
        chart_income=json.dumps(chart_income),\
        chart_expenses=json.dumps(chart_expenses),\
        chart_profit=json.dumps(chart_profit),\
        start_date=start_date,\
        end_date=end_date\
    )
@app.route("/farm-profit-loss/download")
def download_farm_profit_loss():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    farmer_id = session["farmer_id"]
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    conn = get_db_connection()
    sales_query = """
        SELECT
            DATE(o.order_date) AS sale_date,
            oi.product_name AS product,
            oi.quantity,
            oi.unit,
            oi.subtotal
        FROM marketplace_order_items oi
        JOIN marketplace_orders o
            ON oi.order_id = o.id
        WHERE oi.farmer_id = ?
        AND o.payment_status = 'Paid'
    """
    sales_params = [farmer_id]
    if start_date:
        sales_query += " AND DATE(o.order_date) >= ? "
        sales_params.append(start_date)
    if end_date:
        sales_query += " AND DATE(o.order_date) <= ? "
        sales_params.append(end_date)
    sales_query += " ORDER BY sale_date DESC"
    sales = conn.execute(\
        sales_query,\
        sales_params\
    ).fetchall()
    expense_query = """
        SELECT
            expense_date,
            category,
            crop,
            amount,
            payment_method,
            description
        FROM expenses
        WHERE farmer_id = ?
    """
    expense_params = [farmer_id]
    if start_date:
        expense_query += " AND expense_date >= ? "
        expense_params.append(start_date)
    if end_date:
        expense_query += " AND expense_date <= ? "
        expense_params.append(end_date)
    expense_query += " ORDER BY expense_date DESC"
    expenses = conn.execute(\
        expense_query,\
        expense_params\
    ).fetchall()
    conn.close()
    csv_lines = []
    csv_lines.append(\
        "Type,Date,Product/Category,Crop,Quantity,Unit,"\
        "Income,Expense,Payment Method,Description"\
    )
    for sale in sales:
        product = str(\
            sale["product"] or ""\
        ).replace(",", " ")
        csv_lines.append(\
            f"Income,"\
            f"{sale['sale_date']},"\
            f"{product},"\
            f"{product},"\
            f"{sale['quantity'] or 0},"\
            f"{sale['unit'] or ''},"\
            f"{float(sale['subtotal'] or 0):.2f},"\
            f"0,"\
            f","\
            f""\
        )
    for expense in expenses:
        category = str(\
            expense["category"] or ""\
        ).replace(",", " ")
        crop = str(\
            expense["crop"] or "Farm"\
        ).replace(",", " ")
        payment_method = str(\
            expense["payment_method"] or ""\
        ).replace(",", " ")
        description = str(\
            expense["description"] or ""\
        ).replace(",", " ")
        csv_lines.append(\
            f"Expense,"\
            f"{expense['expense_date']},"\
            f"{category},"\
            f"{crop},"\
            f",,"\
            f"0,"\
            f"{float(expense['amount'] or 0):.2f},"\
            f"{payment_method},"\
            f"{description}"\
        )
    csv_data = "\n".join(csv_lines)
    from flask import Response
    return Response(\
        csv_data,\
        mimetype="text/csv",\
        headers={\
            "Content-Disposition":\
                "attachment; filename=farm_profit_loss.csv"\
        }\
    )
    \
\
\
    total_expenses = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE farmer_id = ?
    """, (farmer_id,)).fetchone()[0]
    \
\
\
    profit_loss = float(total_income) - float(total_expenses)
    \
\
\
    sales = conn.execute("""
        SELECT
            DATE(o.order_date) AS sale_date,
            oi.product_name AS crop,
            SUM(oi.subtotal) AS income
        FROM marketplace_order_items oi
        JOIN marketplace_orders o
            ON oi.order_id = o.id
        WHERE oi.farmer_id = ?
        AND o.payment_status = 'Paid'
        GROUP BY DATE(o.order_date), oi.product_name
        ORDER BY sale_date DESC
    """, (farmer_id,)).fetchall()
    \
\
\
    expenses = conn.execute("""
        SELECT
            expense_date,
            crop,
            SUM(amount) AS expense
        FROM expenses
        WHERE farmer_id = ?
        GROUP BY expense_date, crop
        ORDER BY expense_date DESC
    """, (farmer_id,)).fetchall()
    conn.close()
    \
\
\
    report_data = {}
    for sale in sales:
        key = (\
            sale["sale_date"],\
            sale["crop"] or "Farm"\
        )
        if key not in report_data:
            report_data[key] = {\
                "date": sale["sale_date"],\
                "crop": sale["crop"] or "Farm",\
                "income": 0,\
                "expense": 0\
            }
        report_data[key]["income"] += float(\
            sale["income"] or 0\
        )
    for expense in expenses:
        key = (\
            expense["expense_date"],\
            expense["crop"] or "Farm"\
        )
        if key not in report_data:
            report_data[key] = {\
                "date": expense["expense_date"],\
                "crop": expense["crop"] or "Farm",\
                "income": 0,\
                "expense": 0\
            }
        report_data[key]["expense"] += float(\
            expense["expense"] or 0\
        )
    report = []
    for item in report_data.values():
        item["profit"] = (\
            item["income"] - item["expense"]\
        )
        report.append(item)
    report.sort(\
        key=lambda x: x["date"] or "",\
        reverse=True\
    )
    return render_template(\
        "farm_profit_loss.html",\
        total_income=round(float(total_income), 2),\
        total_expenses=round(float(total_expenses), 2),\
        profit_loss=round(float(profit_loss), 2),\
        report=report\
    )
@app.route(\
    "/edit-expense/<int:expense_id>",\
    methods=["GET", "POST"]\
)
def edit_expense(expense_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    expense = conn.execute("""
        SELECT *
        FROM expenses
        WHERE id = ?
        AND farmer_id = ?
    """, (\
        expense_id,\
        session["farmer_id"]\
    )).fetchone()
    conn.close()
    if not expense:
        return redirect(url_for("expense_management"))
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount = request.form.get("amount", "").strip()
        expense_date = request.form.get("expense_date", "").strip()
        crop = request.form.get("crop", "").strip()
        payment_method = request.form.get("payment_method", "").strip()
        receipt_number = request.form.get("receipt_number", "").strip()
        description = request.form.get("description", "").strip()
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return render_template(\
                "add_expense.html",\
                expense=expense,\
                edit_mode=True,\
                error="Please enter a valid expense amount."\
            )
        if not category or not expense_date:
            return render_template(\
                "add_expense.html",\
                expense=expense,\
                edit_mode=True,\
                error="Please enter category and expense date."\
            )
        conn = get_db_connection()
        conn.execute("""
            UPDATE expenses
            SET
                category = ?,
                amount = ?,
                expense_date = ?,
                crop = ?,
                payment_method = ?,
                receipt_number = ?,
                description = ?
            WHERE id = ?
            AND farmer_id = ?
        """, (\
            category,\
            amount,\
            expense_date,\
            crop,\
            payment_method,\
            receipt_number,\
            description,\
            expense_id,\
            session["farmer_id"]\
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("expense_management"))
    return render_template(\
        "add_expense.html",\
        expense=expense,\
        edit_mode=True\
    )
@app.route("/delete-expense/<int:expense_id>")
def delete_expense(expense_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("""
        DELETE FROM expenses
        WHERE id = ?
        AND farmer_id = ?
    """, (\
        expense_id,\
        session["farmer_id"]\
    ))
    conn.commit()
    conn.close()
    return redirect(url_for("expense_management"))
@app.route("/complete-activity/<int:activity_id>")
def complete_activity(activity_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    \
    conn.execute("""
        UPDATE farmer_activities
        SET status = 'Completed'
        WHERE id = ? AND farmer_id = ?
    """, (\
        activity_id,\
        session["farmer_id"]\
    ))
    \
    conn.commit()
    conn.close()
    \
    return redirect(url_for("farmer_activity_planner"))
@app.route("/edit-activity/<int:activity_id>", methods=["GET", "POST"])
def edit_activity(activity_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    \
    activity = conn.execute("""
        SELECT *
        FROM farmer_activities
        WHERE id = ? AND farmer_id = ?
    """, (\
        activity_id,\
        session["farmer_id"]\
    )).fetchone()
    \
    if not activity:
        conn.close()
        return redirect(url_for("farmer_activity_planner"))
    if request.method == "POST":
        \
        crop_name = request.form.get("crop_name", "").strip()
        activity_type = request.form.get("activity_type", "").strip()
        activity_date = request.form.get("activity_date", "").strip()
        reminder_time = request.form.get("reminder_time", "").strip()
        priority = request.form.get("priority", "Medium").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        assigned_person = request.form.get("assigned_person", "").strip()
        \
        conn.execute("""
            UPDATE farmer_activities
            SET crop_name = ?,
                activity_type = ?,
                activity_date = ?,
                reminder_time = ?,
                priority = ?,
                description = ?,
                location = ?,
                assigned_person = ?
            WHERE id = ? AND farmer_id = ?
        """, (\
            crop_name,\
            activity_type,\
            activity_date,\
            reminder_time,\
            priority,\
            description,\
            location,\
            assigned_person,\
            activity_id,\
            session["farmer_id"]\
        ))
        \
        conn.commit()
        conn.close()
        \
        return redirect(url_for("farmer_activity_planner"))
    conn.close()
    \
    return render_template(\
        "edit_activity.html",\
        activity=activity\
    )
@app.route("/delete-activity/<int:activity_id>")
def delete_activity(activity_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    \
    conn.execute("""
        DELETE FROM farmer_activities
        WHERE id = ? AND farmer_id = ?
    """, (\
        activity_id,\
        session["farmer_id"]\
    ))
    \
    conn.commit()
    conn.close()
    \
    return redirect(url_for("farmer_activity_planner"))
@app.route("/farmer-activity-planner", methods=["GET", "POST"])
def farmer_activity_planner():
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    farmer_id = session["farmer_id"]
    \
    conn = get_db_connection()
    \
    if request.method == "POST":
        \
        crop_name = request.form.get("crop_name", "").strip()
        activity_type = request.form.get("activity_type", "").strip()
        activity_date = request.form.get("activity_date", "").strip()
        reminder_time = request.form.get("reminder_time", "").strip()
        priority = request.form.get("priority", "Medium").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        assigned_person = request.form.get("assigned_person", "").strip()
        \
        if crop_name and activity_type and activity_date:
            \
\
            cursor = conn.execute("""
                INSERT INTO farmer_activities (
                    farmer_id,
                    crop_name,
                    activity_type,
                    activity_date,
                    reminder_time,
                    priority,
                    description,
                    location,
                    assigned_person,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
            """, (\
                farmer_id,\
                crop_name,\
                activity_type,\
                activity_date,\
                reminder_time,\
                priority,\
                description,\
                location,\
                assigned_person\
            ))
            \
            activity_id = cursor.lastrowid
            \
\
            alert_type = "Activity"
            \
            if activity_type == "Irrigation":
                alert_type = "Irrigation"
            elif activity_type == "Fertilizer":
                alert_type = "Fertilizer"
            elif activity_type == "Pest & Disease Inspection":
                alert_type = "Pest & Disease"
            elif activity_type == "Harvesting":
                alert_type = "Harvest"
            elif activity_type == "Marketing / Sales":
                alert_type = "Marketing / Sales"
            alert_title = f"{activity_type} Reminder"
            \
            alert_message = (\
                f"{activity_type} activity for {crop_name} "\
                f"is scheduled on {activity_date}"\
            )
            \
            if reminder_time:
                alert_message += f" at {reminder_time}"
            if location:
                alert_message += f". Location: {location}"
            if description:
                alert_message += f". {description}"
            conn.execute("""
                INSERT INTO farming_alerts (
                    farmer_id,
                    alert_type,
                    title,
                    message,
                    alert_date,
                    priority,
                    status,
                    related_activity_id
                )
                VALUES (?, ?, ?, ?, ?, ?, 'Unread', ?)
            """, (\
                farmer_id,\
                alert_type,\
                alert_title,\
                alert_message,\
                activity_date,\
                priority,\
                activity_id\
            ))
            \
            conn.commit()
        conn.close()
        \
        return redirect(url_for("farmer_activity_planner"))
    if request.method == "POST":
        \
        crop_name = request.form.get("crop_name", "").strip()
        activity_type = request.form.get("activity_type", "").strip()
        activity_date = request.form.get("activity_date", "").strip()
        reminder_time = request.form.get("reminder_time", "").strip()
        priority = request.form.get("priority", "Medium").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        assigned_person = request.form.get("assigned_person", "").strip()
        \
        if crop_name and activity_type and activity_date:
            \
\
\
\
\
            cursor = conn.execute("""
                INSERT INTO farmer_activities (
                    farmer_id,
                    crop_name,
                    activity_type,
                    activity_date,
                    reminder_time,
                    priority,
                    description,
                    location,
                    assigned_person,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
            """, (\
                farmer_id,\
                crop_name,\
                activity_type,\
                activity_date,\
                reminder_time,\
                priority,\
                description,\
                location,\
                assigned_person\
            ))
            \
            activity_id = cursor.lastrowid
            \
\
\
\
            alert_title = f"{activity_type} Activity Reminder"
            \
            alert_message = (\
                f"{activity_type} activity for {crop_name} "\
                f"is scheduled on {activity_date}"\
            )
            \
            if reminder_time:
                alert_message += f" at {reminder_time}."
            if location:
                alert_message += f" Location: {location}."
            if description:
                alert_message += f" {description}"
            conn.execute("""
                INSERT INTO farming_alerts (
                    farmer_id,
                    alert_type,
                    title,
                    message,
                    alert_date,
                    priority,
                    status,
                    related_activity_id
                )
                VALUES (?, ?, ?, ?, ?, ?, 'Unread', ?)
            """, (\
                farmer_id,\
                "Activity",\
                alert_title,\
                alert_message,\
                activity_date,\
                priority,\
                activity_id\
            ))
            \
            conn.commit()
        conn.close()
        \
        return redirect(url_for("farmer_activity_planner"))
    search = request.args.get("search", "").strip()
    filter_date = request.args.get("date", "").strip()
    filter_priority = request.args.get("priority", "").strip()
    filter_status = request.args.get("status", "").strip()
    \
    query = """
        SELECT *
        FROM farmer_activities
        WHERE farmer_id = ?
    """
    \
    params = [farmer_id]
    \
    if search:
        \
        query += """
            AND (
                crop_name LIKE ?
                OR activity_type LIKE ?
                OR location LIKE ?
                OR assigned_person LIKE ?
            )
        """
        \
        search_value = f"%{search}%"
        \
        params.extend([\
            search_value,\
            search_value,\
            search_value,\
            search_value\
        ])
    if filter_date:
        \
        query += """
            AND activity_date = ?
        """
        \
        params.append(filter_date)
    if filter_priority:
        \
        query += """
            AND priority = ?
        """
        \
        params.append(filter_priority)
    if filter_status:
        \
        query += """
            AND status = ?
        """
        \
        params.append(filter_status)
    query += """
        ORDER BY activity_date ASC, reminder_time ASC
    """
    \
    activities = conn.execute(\
        query,\
        params\
    ).fetchall()
    \
\
\
\
\
    total = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
    """, (farmer_id,)).fetchone()[0]
    \
    pending = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
        AND status = 'Pending'
    """, (farmer_id,)).fetchone()[0]
    \
    completed = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
        AND status = 'Completed'
    """, (farmer_id,)).fetchone()[0]
    \
    today = datetime.now().strftime("%Y-%m-%d")
    \
    today_count = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
        AND activity_date = ?
    """, (farmer_id, today)).fetchone()[0]
    \
    upcoming = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
        AND activity_date > ?
        AND status = 'Pending'
    """, (farmer_id, today)).fetchone()[0]
    \
    overdue = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
        AND activity_date < ?
        AND status != 'Completed'
    """, (farmer_id, today)).fetchone()[0]
    \
    conn.close()
    \
    return render_template(\
        "farmer_activity_planner.html",\
        activities=activities,\
        total=total,\
        pending=pending,\
        completed=completed,\
        overdue=overdue,\
        today_count=today_count,\
        upcoming=upcoming,\
        today=today,\
        search=search,\
        filter_date=filter_date,\
        filter_priority=filter_priority,\
        filter_status=filter_status\
    )
    \
\
\
\
\
    if request.method == "POST":
        \
        crop_name = request.form.get("crop_name", "").strip()
        activity_type = request.form.get("activity_type", "").strip()
        activity_date = request.form.get("activity_date", "").strip()
        reminder_time = request.form.get("reminder_time", "").strip()
        priority = request.form.get("priority", "Medium").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        assigned_person = request.form.get("assigned_person", "").strip()
        \
        if crop_name and activity_type and activity_date:
            \
            conn.execute("""
                INSERT INTO farmer_activities (
                    farmer_id,
                    crop_name,
                    activity_type,
                    activity_date,
                    reminder_time,
                    priority,
                    description,
                    location,
                    assigned_person,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
            """, (\
                farmer_id,\
                crop_name,\
                activity_type,\
                activity_date,\
                reminder_time,\
                priority,\
                description,\
                location,\
                assigned_person\
            ))
            \
            conn.commit()
        conn.close()
        \
        return redirect(url_for("farmer_activity_planner"))
    search = request.args.get("search", "").strip()
    filter_date = request.args.get("date", "").strip()
    filter_priority = request.args.get("priority", "").strip()
    filter_status = request.args.get("status", "").strip()
    \
    query = """
        SELECT *
        FROM farmer_activities
        WHERE farmer_id = ?
    """
    \
    params = [farmer_id]
    \
    if search:
        query += """
            AND (
                crop_name LIKE ?
                OR activity_type LIKE ?
                OR location LIKE ?
                OR assigned_person LIKE ?
            )
        """
        \
        search_value = f"%{search}%"
        \
        params.extend([\
            search_value,\
            search_value,\
            search_value,\
            search_value\
        ])
    if filter_date:
        query += " AND activity_date = ?"
        params.append(filter_date)
    if filter_priority:
        query += " AND priority = ?"
        params.append(filter_priority)
    if filter_status:
        query += " AND status = ?"
        params.append(filter_status)
    query += """
        ORDER BY activity_date ASC, reminder_time ASC
    """
    \
    activities = conn.execute(\
        query,\
        params\
    ).fetchall()
    \
\
\
\
\
    total = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
    """, (farmer_id,)).fetchone()[0]
    \
    pending = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
        AND status = 'Pending'
    """, (farmer_id,)).fetchone()[0]
    \
    completed = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
        AND status = 'Completed'
    """, (farmer_id,)).fetchone()[0]
    \
    today = datetime.now().strftime("%Y-%m-%d")
    \
    today_count = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
        AND activity_date = ?
    """, (\
        farmer_id,\
        today\
    )).fetchone()[0]
    \
    upcoming = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
        AND activity_date > ?
        AND status = 'Pending'
    """, (\
        farmer_id,\
        today\
    )).fetchone()[0]
    \
    overdue = conn.execute("""
        SELECT COUNT(*)
        FROM farmer_activities
        WHERE farmer_id = ?
        AND activity_date < ?
        AND status != 'Completed'
    """, (\
        farmer_id,\
        today\
    )).fetchone()[0]
    \
    conn.close()
    \
    return render_template(\
        "farmer_activity_planner.html",\
        activities=activities,\
        total=total,\
        pending=pending,\
        completed=completed,\
        overdue=overdue,\
        today_count=today_count,\
        upcoming=upcoming,\
        today=today,\
        search=search,\
        filter_date=filter_date,\
        filter_priority=filter_priority,\
        filter_status=filter_status\
    )
def create_farming_alert(conn, farmer_id, alert_type, title, message, alert_date=None, priority="Medium"):
    """
    Create a notification in the existing farming_alerts table.
    """
    if not farmer_id:
        return
    if not alert_date:
        alert_date = datetime.now().strftime("%Y-%m-%d")
    conn.execute("""
        INSERT INTO farming_alerts (
            farmer_id,
            alert_type,
            title,
            message,
            alert_date,
            priority,
            status,
            related_activity_id
        )
        VALUES (?, ?, ?, ?, ?, ?, 'Unread', NULL)
    """, (\
        farmer_id,\
        alert_type,\
        title,\
        message,\
        alert_date,\
        priority\
    ))
@app.route("/farming-alerts")
def farming_alerts():
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    farmer_id = session["farmer_id"]
    \
\
    search = request.args.get("search", "").strip()
    alert_type = request.args.get("alert_type", "").strip()
    priority = request.args.get("priority", "").strip()
    status = request.args.get("status", "").strip()
    \
    conn = get_db_connection()
    \
\
\
\
\
    query = """
        SELECT *
        FROM farming_alerts
        WHERE farmer_id = ?
    """
    \
    params = [farmer_id]
    \
    if search:
        query += """
            AND (
                title LIKE ?
                OR message LIKE ?
                OR alert_type LIKE ?
            )
        """
        \
        search_value = f"%{search}%"
        \
        params.extend([\
            search_value,\
            search_value,\
            search_value\
        ])
    if alert_type:
        query += """
            AND alert_type = ?
        """
        params.append(alert_type)
    if priority:
        query += """
            AND priority = ?
        """
        params.append(priority)
    if status:
        query += """
            AND status = ?
        """
        params.append(status)
    query += """
        ORDER BY alert_date DESC, id DESC
    """
    \
    alerts = conn.execute(\
        query,\
        params\
    ).fetchall()
    \
\
\
\
\
    total = conn.execute("""
        SELECT COUNT(*)
        FROM farming_alerts
        WHERE farmer_id = ?
    """, (\
        farmer_id,\
    )).fetchone()[0]
    \
\
\
\
\
    unread = conn.execute("""
        SELECT COUNT(*)
        FROM farming_alerts
        WHERE farmer_id = ?
        AND status = 'Unread'
    """, (\
        farmer_id,\
    )).fetchone()[0]
    \
\
\
\
\
    high = conn.execute("""
        SELECT COUNT(*)
        FROM farming_alerts
        WHERE farmer_id = ?
        AND priority = 'High'
    """, (\
        farmer_id,\
    )).fetchone()[0]
    \
\
\
\
\
    read = conn.execute("""
        SELECT COUNT(*)
        FROM farming_alerts
        WHERE farmer_id = ?
        AND status = 'Read'
    """, (\
        farmer_id,\
    )).fetchone()[0]
    \
\
\
\
\
    today = datetime.now().strftime("%Y-%m-%d")
    \
    today_count = conn.execute("""
        SELECT COUNT(*)
        FROM farming_alerts
        WHERE farmer_id = ?
        AND alert_date = ?
    """, (\
        farmer_id,\
        today\
    )).fetchone()[0]
    \
\
\
\
\
    overdue_count = conn.execute("""
        SELECT COUNT(*)
        FROM farming_alerts
        WHERE farmer_id = ?
        AND alert_date < ?
        AND status = 'Unread'
    """, (\
        farmer_id,\
        today\
    )).fetchone()[0]
    \
    conn.close()
    \
    return render_template(\
        "farming_alerts.html",\
        alerts=alerts,\
        total=total,\
        unread=unread,\
        high=high,\
        read=read,\
        today_count=today_count,\
        overdue_count=overdue_count,\
        search=search,\
        alert_type=alert_type,\
        priority=priority,\
        status=status\
    )
@app.route("/mark-alert-read/<int:alert_id>")
def mark_alert_read(alert_id):
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    farmer_id = session["farmer_id"]
    \
    conn = get_db_connection()
    \
    conn.execute("""
        UPDATE farming_alerts
        SET status = 'Read'
        WHERE id = ?
        AND farmer_id = ?
    """, (\
        alert_id,\
        farmer_id\
    ))
    \
    conn.commit()
    conn.close()
    \
    return redirect(url_for("farming_alerts"))
@app.route("/delete-alert/<int:alert_id>")
def delete_alert(alert_id):
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    farmer_id = session["farmer_id"]
    \
    conn = get_db_connection()
    \
    conn.execute("""
        DELETE FROM farming_alerts
        WHERE id = ?
        AND farmer_id = ?
    """, (\
        alert_id,\
        farmer_id\
    ))
    \
    conn.commit()
    conn.close()
    \
    return redirect(url_for("farming_alerts"))
@app.route("/crop-recommendation", methods=["GET", "POST"])
def crop_recommendation():
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    recommendation = None
    suitability = 0
    reason = ""
    water_need = ""
    advice = ""
    \
    scores = {\
        "Rice": 0,\
        "Maize": 0,\
        "Ragi": 0,\
        "Cotton": 0,\
        "Wheat": 0\
    }
    \
    if request.method == "POST":
        \
        try:
            \
            nitrogen = float(request.form.get("nitrogen", 0))
            phosphorus = float(request.form.get("phosphorus", 0))
            potassium = float(request.form.get("potassium", 0))
            temperature = float(request.form.get("temperature", 0))
            humidity = float(request.form.get("humidity", 0))
            ph = float(request.form.get("ph", 0))
            rainfall = float(request.form.get("rainfall", 0))
        except ValueError:
            \
            return render_template(\
                "crop_recommendation.html",\
                error="Please enter valid numbers."\
            )
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
        recommendation = max(scores, key=scores.get)
        \
        suitability = scores[recommendation]
        \
        information = {\
\
            "Rice": (\
                "Rice is suitable because temperature, humidity, rainfall and soil conditions are favorable.",\
                "High",\
                "Rice needs plenty of water. Maintain proper irrigation and monitor pests."\
            ),\
\
            "Maize": (\
                "Temperature, humidity, soil pH and rainfall conditions are suitable for Maize.",\
                "Medium",\
                "Provide regular irrigation and ensure proper nitrogen supply."\
            ),\
\
            "Ragi": (\
                "Ragi can grow well under moderate rainfall and suitable soil pH conditions.",\
                "Low to Medium",\
                "Avoid excess watering and maintain good soil nutrients."\
            ),\
\
            "Cotton": (\
                "Warm temperature and moderate rainfall conditions are suitable for Cotton.",\
                "Medium",\
                "Provide balanced irrigation and monitor the crop regularly for pests."\
            ),\
\
            "Wheat": (\
                "Cooler temperature and moderate rainfall conditions are suitable for Wheat.",\
                "Medium",\
                "Maintain proper irrigation and provide sufficient nitrogen during growth."\
            )\
        }
        \
        reason, water_need, advice = information[recommendation]
        \
\
\
\
\
        try:
            \
            farmer_id = session["farmer_id"]
            \
            conn = get_db_connection()
            \
            today = datetime.now().strftime("%Y-%m-%d")
            \
\
            if suitability >= 80:
                notification_priority = "High"
            elif suitability >= 50:
                notification_priority = "Medium"
            else:
                notification_priority = "Low"
            notification_message = (\
                f"Recommended crop: {recommendation}. "\
                f"Suitability score: {suitability}%. "\
                f"Water requirement: {water_need}. "\
                f"{advice}"\
            )
            \
            conn.execute("""
                INSERT INTO farming_alerts
                (
                    farmer_id,
                    alert_type,
                    title,
                    message,
                    alert_date,
                    priority,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (\
                farmer_id,\
                "Crop Recommendation",\
                "🌾 New Crop Recommendation",\
                notification_message,\
                today,\
                notification_priority,\
                "Unread"\
            ))
            \
            conn.commit()
            conn.close()
        except Exception as alert_error:
            \
            print("CROP RECOMMENDATION ALERT ERROR:", alert_error)
    return render_template(\
\
        "crop_recommendation.html",\
\
        recommendation=recommendation,\
\
        suitability=suitability,\
\
        reason=reason,\
\
        water_need=water_need,\
\
        advice=advice,\
\
        rice_score=scores["Rice"],\
\
        maize_score=scores["Maize"],\
\
        ragi_score=scores["Ragi"],\
\
        cotton_score=scores["Cotton"],\
\
        wheat_score=scores["Wheat"]\
    )
@app.route("/crop-management", methods=["GET", "POST"])
def crop_management():
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    success = None
    error = None
    \
    if request.method == "POST":
        \
        crop_name = request.form.get("crop_name", "").strip()
        area = request.form.get("area", "").strip()
        planting_date = request.form.get("planting_date", "").strip()
        growth_stage = request.form.get("growth_stage", "").strip()
        soil_type = request.form.get("soil_type", "").strip()
        irrigation_method = request.form.get("irrigation_method", "").strip()
        harvest_date = request.form.get("harvest_date", "").strip()
        notes = request.form.get("notes", "").strip()
        \
        if not crop_name:
            error = "Please select a crop."
        elif not area:
            error = "Please enter farm area."
        elif not planting_date:
            error = "Please select planting date."
        elif not growth_stage:
            error = "Please select growth stage."
        elif not soil_type:
            error = "Please select soil type."
        elif not irrigation_method:
            error = "Please select irrigation method."
        elif not harvest_date:
            error = "Please select expected harvest date."
        else:
            try:
                area = float(area)
                \
                if area <= 0:
                    error = "Farm area must be greater than 0."
            except ValueError:
                error = "Please enter a valid farm area."
        if not error:
            \
            try:
                \
                farmer_id = session["farmer_id"]
                \
                conn = get_db_connection()
                \
\
\
\
\
                cursor = conn.execute("""
                    INSERT INTO crops
                    (
                        farmer_id,
                        crop_name,
                        area,
                        planting_date,
                        growth_stage,
                        soil_type,
                        irrigation_method,
                        harvest_date,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (\
                    farmer_id,\
                    crop_name,\
                    area,\
                    planting_date,\
                    growth_stage,\
                    soil_type,\
                    irrigation_method,\
                    harvest_date,\
                    notes\
                ))
                \
                crop_id = cursor.lastrowid
                \
\
\
\
\
                conn.execute("""
                    INSERT INTO farming_alerts
                    (
                        farmer_id,
                        alert_type,
                        title,
                        message,
                        alert_date,
                        priority,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (\
                    farmer_id,\
                    "Crop Management",\
                    "🌱 New Crop Added",\
                    f"{crop_name} has been added to your Crop Management. "\
                    f"Farm area: {area}.",\
                    planting_date,\
                    "Medium",\
                    "Unread"\
                ))
                \
\
\
\
\
                conn.execute("""
                    INSERT INTO farming_alerts
                    (
                        farmer_id,
                        alert_type,
                        title,
                        message,
                        alert_date,
                        priority,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (\
                    farmer_id,\
                    "Planting",\
                    "🌱 Planting Schedule",\
                    f"{crop_name} planting is scheduled for "\
                    f"{planting_date}.",\
                    planting_date,\
                    "Medium",\
                    "Unread"\
                ))
                \
\
\
\
\
                irrigation_priority = "High"
                \
                if irrigation_method.lower() in [\
                    "rainfed",\
                    "rain fed",\
                    "rain-fed"\
                ]:
                    irrigation_priority = "Medium"
                conn.execute("""
                    INSERT INTO farming_alerts
                    (
                        farmer_id,
                        alert_type,
                        title,
                        message,
                        alert_date,
                        priority,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (\
                    farmer_id,\
                    "Irrigation",\
                    "💧 Irrigation Reminder",\
                    f"{crop_name} is using {irrigation_method} irrigation. "\
                    f"Monitor soil moisture and provide water according "\
                    f"to crop requirements.",\
                    planting_date,\
                    irrigation_priority,\
                    "Unread"\
                ))
                \
\
\
\
\
                growth_priority = "Medium"
                \
                if growth_stage == "Harvest Ready":
                    growth_priority = "High"
                conn.execute("""
                    INSERT INTO farming_alerts
                    (
                        farmer_id,
                        alert_type,
                        title,
                        message,
                        alert_date,
                        priority,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (\
                    farmer_id,\
                    "Crop Growth",\
                    "🌿 Crop Growth Stage",\
                    f"{crop_name} is currently in the "\
                    f"'{growth_stage}' growth stage.",\
                    planting_date,\
                    growth_priority,\
                    "Unread"\
                ))
                \
\
\
\
\
                conn.execute("""
                    INSERT INTO farming_alerts
                    (
                        farmer_id,
                        alert_type,
                        title,
                        message,
                        alert_date,
                        priority,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (\
                    farmer_id,\
                    "Soil",\
                    "🧪 Soil Information",\
                    f"{crop_name} is being managed using "\
                    f"{soil_type} soil.",\
                    planting_date,\
                    "Low",\
                    "Unread"\
                ))
                \
\
\
\
\
                conn.execute("""
                    INSERT INTO farming_alerts
                    (
                        farmer_id,
                        alert_type,
                        title,
                        message,
                        alert_date,
                        priority,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (\
                    farmer_id,\
                    "Harvest",\
                    "🌾 Harvest Reminder",\
                    f"Expected harvest date for {crop_name} is "\
                    f"{harvest_date}. Plan harvesting activities "\
                    f"and prepare storage or marketplace arrangements.",\
                    harvest_date,\
                    "High",\
                    "Unread"\
                ))
                \
\
\
\
\
                if notes:
                    \
                    conn.execute("""
                        INSERT INTO farming_alerts
                        (
                            farmer_id,
                            alert_type,
                            title,
                            message,
                            alert_date,
                            priority,
                            status
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (\
                        farmer_id,\
                        "Crop Management",\
                        "📝 Crop Management Note",\
                        f"Note for {crop_name}: {notes}",\
                        planting_date,\
                        "Low",\
                        "Unread"\
                    ))
                conn.commit()
                conn.close()
                \
                success = (\
                    "Crop details saved successfully! "\
                    "Farming notifications have been created."\
                )
            except Exception as db_error:
                \
                print("CROP DATABASE ERROR:", db_error)
                \
                error = "Unable to save crop details."
    try:
        \
        conn = get_db_connection()
        \
        crop = conn.execute("""
            SELECT *
            FROM crops
            WHERE farmer_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (\
            session["farmer_id"],\
        )).fetchone()
        \
        conn.close()
    except Exception as db_error:
        \
        print("CROP LOAD ERROR:", db_error)
        \
        crop = None
        \
        error = "Unable to load crop details."
    requirements_data = {\
\
        "Rice": {\
            "water": "High water requirement.",\
            "soil": "Clay or loamy soil is suitable.",\
            "temperature": "20°C - 35°C",\
            "fertilizer": "Nitrogen, phosphorus and potassium are required.",\
            "pest": "Monitor for stem borers and leaf pests.",\
            "advice": "Maintain sufficient water and regularly monitor the field for pests and diseases."\
        },\
\
        "Maize": {\
            "water": "Medium water requirement.",\
            "soil": "Well-drained loamy soil is suitable.",\
            "temperature": "18°C - 32°C",\
            "fertilizer": "Nitrogen is especially important during growth.",\
            "pest": "Monitor for fall armyworm and stem borers.",\
            "advice": "Maintain proper irrigation, nutrition and regular pest monitoring."\
        },\
\
        "Ragi": {\
            "water": "Low to medium water requirement.",\
            "soil": "Red and loamy soils are suitable.",\
            "temperature": "20°C - 32°C",\
            "fertilizer": "Balanced fertilizer with nitrogen and phosphorus.",\
            "pest": "Monitor for finger millet pests and diseases.",\
            "advice": "Avoid excess irrigation and maintain good soil fertility."\
        },\
\
        "Cotton": {\
            "water": "Medium water requirement.",\
            "soil": "Black soil and well-drained soil are suitable.",\
            "temperature": "21°C - 35°C",\
            "fertilizer": "Balanced NPK fertilizer is recommended.",\
            "pest": "Monitor for bollworms and sucking pests.",\
            "advice": "Monitor pests regularly and maintain balanced irrigation."\
        },\
\
        "Wheat": {\
            "water": "Medium water requirement.",\
            "soil": "Loamy and well-drained soil is suitable.",\
            "temperature": "15°C - 25°C",\
            "fertilizer": "Nitrogen is important during growth.",\
            "pest": "Monitor for aphids and rust diseases.",\
            "advice": "Maintain proper irrigation and monitor the crop during growth."\
        },\
\
        "Tomato": {\
            "water": "Medium water requirement.",\
            "soil": "Well-drained loamy soil is suitable.",\
            "temperature": "18°C - 30°C",\
            "fertilizer": "Balanced NPK fertilizer is recommended.",\
            "pest": "Monitor for whiteflies, aphids and fruit borers.",\
            "advice": "Avoid waterlogging and regularly inspect leaves and fruits."\
        },\
\
        "Other": {\
            "water": "Depends on the crop.",\
            "soil": "Use soil suitable for the selected crop.",\
            "temperature": "Depends on crop variety.",\
            "fertilizer": "Apply fertilizer based on soil testing.",\
            "pest": "Regularly monitor for pests and diseases.",\
            "advice": "Monitor soil moisture, crop growth and pest conditions regularly."\
        }\
    }
    \
    requirements = None
    growth_percentage = 0
    \
\
\
\
\
    if crop:
        \
        requirements = requirements_data.get(\
            crop["crop_name"],\
            requirements_data["Other"]\
        )
        \
        growth_progress = {\
\
            "Seedling": 25,\
\
            "Growing": 50,\
\
            "Flowering": 75,\
\
            "Harvest Ready": 100\
        }
        \
        growth_percentage = growth_progress.get(\
            crop["growth_stage"],\
            0\
        )
    return render_template(\
        "crop_management.html",\
        crop=crop,\
        requirements=requirements,\
        growth_percentage=growth_percentage,\
        success=success,\
        error=error\
    )
@app.route("/add-crop", methods=["POST"])
def add_crop():
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return redirect(url_for("crop_management"))
@app.route("/weather", methods=["GET", "POST"])
def weather():
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    south_india_locations = {\
\
        "Karnataka": [\
            "Bengaluru", "Mysuru", "Mangaluru", "Hubballi",\
            "Dharwad", "Belagavi", "Shivamogga", "Tumakuru",\
            "Ballari", "Kalaburagi", "Udupi", "Hassan", "Kodagu"\
        ],\
\
        "Tamil Nadu": [\
            "Chennai", "Coimbatore", "Madurai", "Salem",\
            "Tiruchirappalli", "Tirunelveli", "Erode",\
            "Vellore", "Thanjavur", "Thoothukudi",\
            "Dindigul", "Hosur"\
        ],\
\
        "Kerala": [\
            "Thiruvananthapuram", "Kochi", "Kozhikode",\
            "Thrissur", "Kollam", "Kannur", "Alappuzha",\
            "Palakkad", "Kottayam", "Malappuram"\
        ],\
\
        "Andhra Pradesh": [\
            "Visakhapatnam", "Vijayawada", "Tirupati",\
            "Guntur", "Nellore", "Kurnool", "Rajahmundry",\
            "Kakinada", "Kadapa", "Anantapur"\
        ],\
\
        "Telangana": [\
            "Hyderabad", "Warangal", "Nizamabad",\
            "Karimnagar", "Khammam", "Ramagundam",\
            "Nalgonda", "Mahbubnagar"\
        ],\
\
        "Puducherry": [\
            "Puducherry"\
        ]\
    }
    \
    location = "Bengaluru"
    \
    if request.method == "POST":
        \
        location = request.form.get(\
            "location",\
            ""\
        ).strip()
        \
        if not location:
            location = "Bengaluru"
    weather_data = {\
        "location": location,\
        "temperature": "--",\
        "humidity": "--",\
        "wind": "--",\
        "rainfall": "--",\
        "cloud": "--",\
        "condition": "Weather data not loaded",\
        "weather_icon": "🌤️",\
        "forecast": [],\
        "irrigation_advice":\
            "Weather data will determine whether irrigation is required.",\
        "crop_advice":\
            "Weather-based crop care advice will appear here.",\
        "fertilizer_advice":\
            "Fertilizer application advice will appear here.",\
        "weather_alert":\
            "No weather alerts available.",\
        "error": None\
    }
    \
    try:
        \
        search_locations = [location]
        \
        if "," in location:
            \
            first = location.split(",")[0].strip()
            \
            if first:
                search_locations.append(first)
        if "mahadevapura" in location.lower():
            \
            search_locations.extend([\
                "Mahadevapura",\
                "Bengaluru",\
                "Bangalore"\
            ])
        unique_locations = []
        \
        for item in search_locations:
            \
            if item and item.lower() not in [\
                x.lower() for x in unique_locations\
            ]:
                \
                unique_locations.append(item)
        place = None
        \
\
\
\
\
        for search_name in unique_locations:
            \
            encoded = urllib.parse.quote(search_name)
            \
            url = (\
                "https://geocoding-api.open-meteo.com/v1/search"\
                "?name=" + encoded +\
                "&count=10"\
                "&language=en"\
                "&format=json"\
            )
            \
            try:
                \
                req = urllib.request.Request(\
                    url,\
                    headers={\
                        "User-Agent":\
                            "Smart-Agriculture-App"\
                    }\
                )
                \
                with urllib.request.urlopen(\
                    req,\
                    timeout=10\
                ) as response:
                    \
                    data = json.loads(\
                        response.read().decode("utf-8")\
                    )
                results = data.get(\
                    "results",\
                    []\
                )
                \
                india_results = [\
                    item\
                    for item in results\
                    if item.get(\
                        "country_code",\
                        ""\
                    ).upper() == "IN"\
                ]
                \
                if india_results:
                    \
                    place = india_results[0]
                elif results:
                    \
                    place = results[0]
                if place:
                    break
            except Exception as search_error:
                \
                print(\
                    "Location search error:",\
                    search_error\
                )
        if place is None:
            \
            weather_data["error"] = (\
                "Location was not found. "\
                "Please search for a valid South Indian city."\
            )
            \
            return render_template(\
                "weather.html",\
                weather=weather_data,\
                south_india_locations=south_india_locations\
            )
        latitude = place.get("latitude")
        longitude = place.get("longitude")
        \
        city_name = place.get(\
            "name",\
            location\
        )
        \
        country = place.get(\
            "country",\
            ""\
        )
        \
        admin1 = place.get(\
            "admin1",\
            ""\
        )
        \
        display_location = city_name
        \
        if admin1:
            display_location += ", " + admin1
        if country:
            display_location += ", " + country
        weather_url = (\
            "https://api.open-meteo.com/v1/forecast"\
            "?latitude=" + str(latitude) +\
            "&longitude=" + str(longitude) +\
            "&current="\
            "temperature_2m,"\
            "relative_humidity_2m,"\
            "precipitation,"\
            "cloud_cover,"\
            "wind_speed_10m,"\
            "weather_code"\
            "&daily="\
            "temperature_2m_max,"\
            "temperature_2m_min,"\
            "precipitation_sum,"\
            "precipitation_probability_max,"\
            "weather_code"\
            "&forecast_days=7"\
            "&timezone=auto"\
            "&temperature_unit=celsius"\
            "&wind_speed_unit=kmh"\
            "&precipitation_unit=mm"\
        )
        \
        req = urllib.request.Request(\
            weather_url,\
            headers={\
                "User-Agent":\
                    "Smart-Agriculture-App"\
            }\
        )
        \
        with urllib.request.urlopen(\
            req,\
            timeout=15\
        ) as response:
            \
            api_data = json.loads(\
                response.read().decode("utf-8")\
            )
        current = api_data.get(\
            "current",\
            {}\
        )
        \
        temperature = current.get(\
            "temperature_2m",\
            "--"\
        )
        \
        humidity = current.get(\
            "relative_humidity_2m",\
            "--"\
        )
        \
        wind = current.get(\
            "wind_speed_10m",\
            "--"\
        )
        \
        rainfall = current.get(\
            "precipitation",\
            0\
        )
        \
        cloud = current.get(\
            "cloud_cover",\
            "--"\
        )
        \
        weather_code = current.get(\
            "weather_code",\
            0\
        )
        \
        condition, icon = get_weather_condition(\
            weather_code\
        )
        \
\
\
\
\
        daily = api_data.get(\
            "daily",\
            {}\
        )
        \
        dates = daily.get(\
            "time",\
            []\
        )
        \
        max_temperatures = daily.get(\
            "temperature_2m_max",\
            []\
        )
        \
        min_temperatures = daily.get(\
            "temperature_2m_min",\
            []\
        )
        \
        precipitation = daily.get(\
            "precipitation_sum",\
            []\
        )
        \
        rain_probability = daily.get(\
            "precipitation_probability_max",\
            []\
        )
        \
        daily_codes = daily.get(\
            "weather_code",\
            []\
        )
        \
        forecast = []
        \
        for index in range(\
            min(7, len(dates))\
        ):
            \
            day_condition, day_icon = (\
                get_weather_condition(\
                    daily_codes[index]\
                )\
            )
            \
            if index == 0:
                day_name = "Today"
            elif index == 1:
                day_name = "Tomorrow"
            else:
                \
                try:
                    \
                    date_object = datetime.strptime(\
                        dates[index],\
                        "%Y-%m-%d"\
                    )
                    \
                    day_name = date_object.strftime(\
                        "%a"\
                    )
                except Exception:
                    \
                    day_name = (\
                        f"Day {index + 1}"\
                    )
            forecast.append({\
\
                "date": dates[index],\
\
                "day": day_name,\
\
                "icon": day_icon,\
\
                "condition": day_condition,\
\
                "max_temp":\
                    max_temperatures[index],\
\
                "min_temp":\
                    min_temperatures[index],\
\
                "rain":\
                    precipitation[index],\
\
                "rain_probability":\
                    rain_probability[index]\
            })
        irrigation_advice = get_irrigation_advice(\
            temperature,\
            humidity,\
            rainfall,\
            cloud\
        )
        \
        crop_advice = get_crop_advice(\
            weather_code,\
            temperature,\
            humidity,\
            rainfall\
        )
        \
        fertilizer_advice = get_fertilizer_advice(\
            rainfall,\
            humidity\
        )
        \
        weather_alert = get_weather_alert(\
            weather_code,\
            temperature,\
            rainfall,\
            wind\
        )
        \
\
\
\
\
        weather_data = {\
\
            "location":\
                display_location,\
\
            "temperature":\
                temperature,\
\
            "humidity":\
                humidity,\
\
            "wind":\
                wind,\
\
            "rainfall":\
                rainfall,\
\
            "cloud":\
                cloud,\
\
            "condition":\
                condition,\
\
            "weather_icon":\
                icon,\
\
            "forecast":\
                forecast,\
\
            "irrigation_advice":\
                irrigation_advice,\
\
            "crop_advice":\
                crop_advice,\
\
            "fertilizer_advice":\
                fertilizer_advice,\
\
            "weather_alert":\
                weather_alert,\
\
            "error":\
                None\
        }
        \
\
\
\
\
        try:
            \
            farmer_id = session["farmer_id"]
            \
            conn = get_db_connection()
            \
            today = datetime.now().strftime(\
                "%Y-%m-%d"\
            )
            \
\
            notification_priority = "Low"
            \
            if rainfall >= 20:
                notification_priority = "High"
            elif rainfall >= 5:
                notification_priority = "Medium"
            if wind != "--":
                \
                try:
                    \
                    if float(wind) >= 40:
                        notification_priority = "High"
                except Exception:
                    pass
            weather_message = (\
                f"Weather in {display_location}: "\
                f"{temperature}°C, humidity {humidity}%, "\
                f"rainfall {rainfall} mm, wind {wind} km/h. "\
                f"{weather_alert}"\
            )
            \
            conn.execute("""
                INSERT INTO farming_alerts
                (
                    farmer_id,
                    alert_type,
                    title,
                    message,
                    alert_date,
                    priority,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (\
                farmer_id,\
                "Weather",\
                "🌦️ Weather Update",\
                weather_message,\
                today,\
                notification_priority,\
                "Unread"\
            ))
            \
\
\
\
\
            if rainfall >= 5:
                \
                conn.execute("""
                    INSERT INTO farming_alerts
                    (
                        farmer_id,
                        alert_type,
                        title,
                        message,
                        alert_date,
                        priority,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (\
                    farmer_id,\
                    "Weather",\
                    "🌧️ Rainfall Alert",\
                    f"Rainfall of {rainfall} mm is currently "\
                    f"reported in {display_location}. "\
                    f"Check drainage and avoid unnecessary irrigation.",\
                    today,\
                    "High" if rainfall >= 20 else "Medium",\
                    "Unread"\
                ))
            conn.execute("""
                INSERT INTO farming_alerts
                (
                    farmer_id,
                    alert_type,
                    title,
                    message,
                    alert_date,
                    priority,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (\
                farmer_id,\
                "Irrigation",\
                "💧 Weather-Based Irrigation Advice",\
                irrigation_advice,\
                today,\
                "Medium",\
                "Unread"\
            ))
            \
\
\
\
\
            conn.execute("""
                INSERT INTO farming_alerts
                (
                    farmer_id,
                    alert_type,
                    title,
                    message,
                    alert_date,
                    priority,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (\
                farmer_id,\
                "Crop Weather",\
                "🌾 Crop Weather Advisory",\
                crop_advice,\
                today,\
                "Medium",\
                "Unread"\
            ))
            \
\
\
\
\
            conn.execute("""
                INSERT INTO farming_alerts
                (
                    farmer_id,
                    alert_type,
                    title,
                    message,
                    alert_date,
                    priority,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (\
                farmer_id,\
                "Fertilizer",\
                "🧪 Fertilizer Weather Advisory",\
                fertilizer_advice,\
                today,\
                "Low",\
                "Unread"\
            ))
            \
            conn.commit()
            conn.close()
        except Exception as alert_error:
            \
            print(\
                "WEATHER ALERT ERROR:",\
                alert_error\
            )
    except Exception as error:
        \
        print(\
            "WEATHER ERROR:",\
            error\
        )
        \
        weather_data["error"] = (\
            "Unable to load weather data. "\
            "Please check your internet connection "\
            "and try again."\
        )
    return render_template(\
        "weather.html",\
        weather=weather_data,\
        south_india_locations=south_india_locations\
    )
def get_weather_condition(weather_code):
    try:
        weather_code = int(weather_code)
    except Exception:
        weather_code = 0
    conditions = {\
        0: ("Clear Sky", "☀️"),\
        1: ("Partly Cloudy", "🌤️"),\
        2: ("Partly Cloudy", "🌤️"),\
        3: ("Cloudy", "☁️"),\
        45: ("Foggy", "🌫️"),\
        48: ("Foggy", "🌫️"),\
        51: ("Drizzle", "🌦️"),\
        53: ("Drizzle", "🌦️"),\
        55: ("Drizzle", "🌦️"),\
        56: ("Drizzle", "🌦️"),\
        57: ("Drizzle", "🌦️"),\
        61: ("Rain", "🌧️"),\
        63: ("Rain", "🌧️"),\
        65: ("Rain", "🌧️"),\
        66: ("Rain", "🌧️"),\
        67: ("Rain", "🌧️"),\
        71: ("Snow", "❄️"),\
        73: ("Snow", "❄️"),\
        75: ("Snow", "❄️"),\
        77: ("Snow", "❄️"),\
        80: ("Rain Showers", "🌦️"),\
        81: ("Rain Showers", "🌦️"),\
        82: ("Rain Showers", "🌦️"),\
        85: ("Snow Showers", "🌨️"),\
        86: ("Snow Showers", "🌨️"),\
        95: ("Thunderstorm", "⛈️"),\
        96: ("Thunderstorm with Hail", "⛈️"),\
        99: ("Thunderstorm with Hail", "⛈️")\
    }
    return conditions.get(weather_code, ("Unknown", "🌤️"))
def get_irrigation_advice(temperature, humidity, rainfall, cloud):
    try:
        temperature = float(temperature)
        humidity = float(humidity)
        rainfall = float(rainfall)
        cloud = float(cloud)
    except Exception:
        return "Check soil moisture before irrigation."
    if rainfall >= 5:
        return (\
            "Recent rainfall is sufficient. Avoid unnecessary irrigation "\
            "and check soil moisture."\
        )
    if temperature >= 32 and humidity < 60:
        return (\
            "Hot and dry conditions detected. Check soil moisture and "\
            "irrigate if required."\
        )
    if humidity >= 80 and cloud >= 70:
        return (\
            "Humidity and cloud cover are high. Avoid unnecessary "\
            "irrigation and monitor soil."\
        )
    return "Current conditions are moderate. Check soil moisture before irrigation."
def get_crop_advice(weather_code, temperature, humidity, rainfall):
    try:
        weather_code = int(weather_code)
        temperature = float(temperature)
        humidity = float(humidity)
        rainfall = float(rainfall)
    except Exception:
        return "Monitor crop conditions regularly."
    if weather_code in [95, 96, 99]:
        return (\
            "Thunderstorm conditions possible. Avoid field operations "\
            "during severe weather."\
        )
    if rainfall >= 10:
        return (\
            "Significant rainfall present. Check drainage and monitor "\
            "crops for fungal disease."\
        )
    if temperature >= 35:
        return "High temperature detected. Monitor crops for heat stress."
    if humidity >= 85:
        return "High humidity may increase disease risk. Monitor leaves regularly."
    return "Weather conditions are moderate. Continue regular crop monitoring."
def get_fertilizer_advice(rainfall, humidity):
    try:
        rainfall = float(rainfall)
        humidity = float(humidity)
    except Exception:
        return "Apply fertilizer according to soil test results."
    if rainfall >= 10:
        return (\
            "Rainfall is significant. Avoid applying fertilizer immediately "\
            "to prevent nutrient loss."\
        )
    if humidity >= 85:
        return (\
            "Humidity is high. Monitor crop health before applying fertilizer."\
        )
    return "Apply fertilizer according to soil test results and crop growth stage."
def get_weather_alert(weather_code, temperature, rainfall, wind):
    try:
        weather_code = int(weather_code)
        temperature = float(temperature)
        rainfall = float(rainfall)
        wind = float(wind)
    except Exception:
        return "No weather alerts available."
    if weather_code in [95, 96, 99]:
        return "⚠️ Thunderstorm conditions detected."
    if rainfall >= 20:
        return "⚠️ Heavy rainfall detected. Check farm drainage."
    if wind >= 40:
        return "⚠️ Strong winds detected. Protect young plants."
    if temperature >= 38:
        return "⚠️ Very high temperature detected. Monitor for heat stress."
    return "No major weather alert detected."
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
def allowed_file(filename):
    return (\
        "." in filename\
        and filename.rsplit(".", 1)[1].lower()\
        in ALLOWED_EXTENSIONS\
    )
@app.route("/disease-detection", methods=["GET", "POST"])
def disease_detection():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    uploaded_image = None
    error = None
    if request.method == "POST":
        if "leaf_image" not in request.files:
            error = "Please select a leaf image."
        else:
            file = request.files["leaf_image"]
            if file.filename == "":
                error = "Please select an image."
            elif not allowed_file(file.filename):
                error = "Only JPG, JPEG and PNG images are allowed."
            else:
                filename = secure_filename(file.filename)
                file.save(\
                    os.path.join(\
                        app.config["UPLOAD_FOLDER"],\
                        filename\
                    )\
                )
                uploaded_image = filename
    return render_template(\
        "disease_detection.html",\
        uploaded_image=uploaded_image,\
        error=error\
    )
@app.route("/farm-marketplace")
def farm_marketplace():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    create_default_marketplace_products(\
        session["farmer_id"]\
    )
    search = request.args.get("search", "").strip()
    category = request.args.get(\
        "category",\
        "All Products"\
    ).strip()
    if category not in MARKETPLACE_CATEGORIES:
        category = "All Products"
    conn = get_db_connection()
    query = """
        SELECT market_products.*,
               farmers.full_name AS farmer_name,
               farmers.username AS farmer_username
        FROM market_products
        LEFT JOIN farmers
            ON market_products.farmer_id = farmers.id
    """
    params = []
    conditions = []
    if category != "All Products":
        conditions.append("market_products.category = ?")
        params.append(category)
    if search:
        conditions.append("market_products.product_name LIKE ?")
        params.append("%" + search + "%")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY market_products.id DESC"
    products = conn.execute(query, params).fetchall()
    conn.close()
    cart = session.get("cart", {})
    cart_count = 0
    for item in cart.values():
        try:
            cart_count += int(float(item.get("quantity", 0)))
        except Exception:
            pass
    return render_template(\
        "farm_marketplace.html",\
        products=products,\
        categories=MARKETPLACE_CATEGORIES,\
        search=search,\
        selected_category=category,\
        cart_count=cart_count,\
        farmer_id=session.get("farmer_id")\
    )
@app.route("/farmer/add-product", methods=["GET", "POST"])
def add_product():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    error = None
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        product_name = request.form.get("product_name", "").strip()
        price = request.form.get("price", "").strip()
        quantity = request.form.get("quantity", "").strip()
        unit = request.form.get("unit", "kg").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        if category not in PRODUCTS_BY_CATEGORY:
            error = "Please select a valid product category."
        elif not product_name:
            error = "Please enter product name."
        elif product_name not in PRODUCTS_BY_CATEGORY[category]:
            error = "Please select a valid product from the selected category."
        elif not price or not quantity:
            error = "Please enter price and available quantity."
        else:
            try:
                price = float(price)
                quantity = float(quantity)
                if price <= 0 or quantity <= 0:
                    error = "Price and quantity must be greater than 0."
            except ValueError:
                error = "Price and quantity must be valid numbers."
        image_name = None
        if not error:
            file = request.files.get("product_image")
            if file and file.filename:
                if not allowed_file(file.filename):
                    error = "Only JPG, JPEG and PNG images are allowed."
                else:
                    original_name = secure_filename(file.filename)
                    \
                    filename_without_ext, extension = os.path.splitext(\
                        original_name\
                    )
                    image_name = (\
                        f"{filename_without_ext}_"\
                        f"{session['farmer_id']}_"\
                        f"{int(datetime.now().timestamp())}"\
                        f"{extension}"\
                    )
                    folder = os.path.join(\
                        "static",\
                        "marketplace"\
                    )
                    os.makedirs(folder, exist_ok=True)
                    file.save(\
                        os.path.join(folder, image_name)\
                    )
        if not error:
            try:
                conn = get_db_connection()
                conn.execute("""
                    INSERT INTO market_products
                    (
                        farmer_id,
                        product_name,
                        price,
                        quantity,
                        unit,
                        location,
                        description,
                        image,
                        category
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (\
                    session["farmer_id"],\
                    product_name,\
                    price,\
                    quantity,\
                    unit,\
                    location,\
                    description,\
                    image_name,\
                    category\
                ))
                \
                create_farming_alert(\
                    conn,\
                    session["farmer_id"],\
                    "Marketplace",\
                    "Product Listed Successfully",\
                    f"{product_name} has been added to your Farm Marketplace.",\
                    datetime.now().strftime("%Y-%m-%d"),\
                    "Low"\
                )
                \
                conn.commit()
                conn.close()
                return redirect(url_for("my_products"))
            except Exception as db_error:
                print("MARKETPLACE ADD ERROR:", db_error)
                error = "Unable to add product."
    return render_template(\
        "add_product.html",\
        categories=MARKETPLACE_CATEGORIES,\
        products_by_category=PRODUCTS_BY_CATEGORY,\
        error=error\
    )
@app.route("/farmer/my-products")
def my_products():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    products = conn.execute("""
        SELECT *
        FROM market_products
        WHERE farmer_id = ?
        ORDER BY id DESC
    """, (session["farmer_id"],)).fetchall()
    conn.close()
    return render_template(\
        "my_products.html",\
        products=products\
    )
@app.route("/farmer/my-fruits")
def my_fruits():
    return redirect(url_for("my_products"))
@app.route(\
    "/farmer/edit-product/<int:product_id>",\
    methods=["GET", "POST"]\
)
def edit_product(product_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    product = conn.execute("""
        SELECT *
        FROM market_products
        WHERE id = ?
        AND farmer_id = ?
    """, (\
        product_id,\
        session["farmer_id"]\
    )).fetchone()
    conn.close()
    if not product:
        return redirect(url_for("my_products"))
    error = None
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        product_name = request.form.get("product_name", "").strip()
        price = request.form.get("price", "").strip()
        quantity = request.form.get("quantity", "").strip()
        unit = request.form.get("unit", "kg").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        if category not in PRODUCTS_BY_CATEGORY:
            error = "Please select a valid category."
        elif not product_name:
            error = "Please enter product name."
        elif product_name not in PRODUCTS_BY_CATEGORY[category]:
            error = "Please select a valid product."
        else:
            try:
                price = float(price)
                quantity = float(quantity)
                if price <= 0 or quantity <= 0:
                    error = "Price and quantity must be greater than 0."
            except ValueError:
                error = "Price and quantity must be valid numbers."
        image_name = product["image"]
        if not error:
            file = request.files.get("product_image")
            if file and file.filename:
                if not allowed_file(file.filename):
                    error = "Only JPG, JPEG and PNG images are allowed."
                else:
                    original_name = secure_filename(file.filename)
                    \
                    filename_without_ext, extension = os.path.splitext(\
                        original_name\
                    )
                    image_name = (\
                        f"{filename_without_ext}_"\
                        f"{session['farmer_id']}_"\
                        f"{int(datetime.now().timestamp())}"\
                        f"{extension}"\
                    )
                    folder = os.path.join(\
                        "static",\
                        "marketplace"\
                    )
                    os.makedirs(folder, exist_ok=True)
                    file.save(\
                        os.path.join(folder, image_name)\
                    )
        if not error:
            try:
                conn = get_db_connection()
                conn.execute("""
                    UPDATE market_products
                    SET
                        category = ?,
                        product_name = ?,
                        price = ?,
                        quantity = ?,
                        unit = ?,
                        location = ?,
                        description = ?,
                        image = ?
                    WHERE id = ?
                    AND farmer_id = ?
                """, (\
                    category,\
                    product_name,\
                    price,\
                    quantity,\
                    unit,\
                    location,\
                    description,\
                    image_name,\
                    product_id,\
                    session["farmer_id"]\
                ))
                conn.commit()
                conn.close()
                return redirect(url_for("my_products"))
            except Exception as db_error:
                print("MARKETPLACE EDIT ERROR:", db_error)
                error = "Unable to update product."
    return render_template(\
        "edit_product.html",\
        product=product,\
        categories=MARKETPLACE_CATEGORIES,\
        products_by_category=PRODUCTS_BY_CATEGORY,\
        error=error\
    )
@app.route(\
    "/farmer/edit-fruit/<int:product_id>",\
    methods=["GET", "POST"]\
)
def edit_fruit(product_id):
    return redirect(\
        url_for(\
            "edit_product",\
            product_id=product_id\
        )\
    )
@app.route(\
    "/farmer/delete-product/<int:product_id>",\
    methods=["POST"]\
)
def delete_product(product_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    try:
        conn = get_db_connection()
        product = conn.execute("""
            SELECT image
            FROM market_products
            WHERE id = ?
            AND farmer_id = ?
        """, (\
            product_id,\
            session["farmer_id"]\
        )).fetchone()
        if product:
            image_name = product["image"]
            conn.execute("""
                DELETE FROM market_products
                WHERE id = ?
                AND farmer_id = ?
            """, (\
                product_id,\
                session["farmer_id"]\
            ))
            conn.commit()
            if image_name:
                image_path = os.path.join(\
                    "static",\
                    "marketplace",\
                    image_name\
                )
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception:
                        pass
        conn.close()
    except Exception as db_error:
        print("MARKETPLACE DELETE ERROR:", db_error)
    return redirect(url_for("my_products"))
@app.route(\
    "/farmer/delete-fruit/<int:product_id>",\
    methods=["POST"]\
)
def delete_fruit(product_id):
    return delete_product(product_id)
@app.route(\
    "/marketplace/add-to-cart/<int:product_id>",\
    methods=["POST"]\
)
def add_to_cart(product_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    try:
        requested_quantity = float(\
            request.form.get("quantity", 1)\
        )
    except (ValueError, TypeError):
        requested_quantity = 1
    if requested_quantity <= 0:
        requested_quantity = 1
    conn = get_db_connection()
    product = conn.execute("""
        SELECT *
        FROM market_products
        WHERE id = ?
    """, (product_id,)).fetchone()
    conn.close()
    if not product or float(product["quantity"] or 0) <= 0:
        return redirect(\
            request.referrer or url_for("farm_marketplace")\
        )
    cart = session.get("cart", {})
    product_key = str(product_id)
    if product_key in cart:
        new_quantity = (\
            float(cart[product_key]["quantity"])\
            + requested_quantity\
        )
        cart[product_key]["quantity"] = min(\
            new_quantity,\
            float(product["quantity"])\
        )
    else:
        cart[product_key] = {\
            "product_id": product["id"],\
            "product_name": product["product_name"],\
            "price": product["price"],\
            "quantity": min(\
                requested_quantity,\
                float(product["quantity"])\
            ),\
            "unit": product["unit"],\
            "image": product["image"],\
            "farmer_id": product["farmer_id"],\
            "category": product["category"]\
        }
    session["cart"] = cart
    session.modified = True
    return redirect(\
        request.referrer or url_for("farm_marketplace")\
    )
@app.route("/marketplace/cart")
def marketplace_cart():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    cart = session.get("cart", {})
    total = 0
    for item in cart.values():
        item["subtotal"] = (\
            float(item["price"])\
            * float(item["quantity"])\
        )
        total += item["subtotal"]
    return render_template(\
        "marketplace_cart.html",\
        cart=cart,\
        total=total\
    )
@app.route(\
    "/marketplace/remove-from-cart/<int:product_id>",\
    methods=["POST"]\
)
def remove_from_cart(product_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    cart = session.get("cart", {})
    product_key = str(product_id)
    if product_key in cart:
        del cart[product_key]
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("marketplace_cart"))
@app.route(\
    "/marketplace/clear-cart",\
    methods=["POST"]\
)
def clear_cart():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    session["cart"] = {}
    session.modified = True
    return redirect(url_for("marketplace_cart"))
@app.route(\
    "/marketplace/checkout",\
    methods=["GET", "POST"]\
)
def marketplace_checkout():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    cart = session.get("cart", {})
    if not cart:
        return redirect(url_for("marketplace_cart"))
    total = sum(\
        float(item["price"]) * float(item["quantity"])\
        for item in cart.values()\
    )
    if request.method == "POST":
        location_method = request.form.get(\
            "location_method",\
            "address"\
        ).strip().lower()
        if location_method not in ["address", "gps"]:
            location_method = "address"
        session["checkout_delivery"] = {\
            "delivery_name": request.form.get(\
                "delivery_name", ""\
            ).strip(),\
            "delivery_phone": request.form.get(\
                "delivery_phone", ""\
            ).strip(),\
            "delivery_address": request.form.get(\
                "delivery_address", ""\
            ).strip(),\
            "location_method": location_method,\
            "latitude": request.form.get(\
                "latitude", ""\
            ).strip(),\
            "longitude": request.form.get(\
                "longitude", ""\
            ).strip()\
        }
        session.modified = True
        return redirect(url_for("marketplace_payment"))
    return render_template(\
        "marketplace_checkout.html",\
        cart=cart,\
        cart_items=list(cart.values()),\
        total=total\
    )
@app.route(\
    "/marketplace/payment",\
    methods=["GET", "POST"]\
)
def marketplace_payment():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    cart = session.get("cart", {})
    if not cart:
        return redirect(url_for("marketplace_cart"))
    delivery = session.get("checkout_delivery", {})
    delivery_name = request.form.get(\
        "delivery_name",\
        delivery.get(\
            "delivery_name",\
            session.get("full_name", "")\
        )\
    ).strip()
    delivery_phone = request.form.get(\
        "delivery_phone",\
        delivery.get("delivery_phone", "")\
    ).strip()
    delivery_address = request.form.get(\
        "delivery_address",\
        delivery.get("delivery_address", "")\
    ).strip()
    location_method = request.form.get(\
        "location_method",\
        delivery.get("location_method", "address")\
    ).strip().lower()
    latitude = request.form.get(\
        "latitude",\
        delivery.get("latitude", "")\
    ).strip()
    longitude = request.form.get(\
        "longitude",\
        delivery.get("longitude", "")\
    ).strip()
    total = sum(\
        float(item.get("price", 0))\
        * float(item.get("quantity", 0))\
        for item in cart.values()\
    )
    error = None
    if request.method == "POST":
        payment_method = request.form.get(\
            "payment_method",\
            ""\
        ).strip()
        payment_reference = request.form.get(\
            "payment_reference",\
            ""\
        ).strip()
        clean_phone = "".join(\
            filter(str.isdigit, delivery_phone)\
        )
        allowed_payment_methods = [\
            "PhonePe",\
            "Google Pay",\
            "WhatsApp Pay"\
        ]
        if payment_method not in allowed_payment_methods:
            error = (\
                "Please select PhonePe, Google Pay or WhatsApp Pay."\
            )
        elif not delivery_name:
            error = "Please enter delivery name."
        elif len(clean_phone) != 10:
            error = "Please enter a valid 10-digit phone number."
        elif location_method not in ["address", "gps"]:
            error = "Please select a valid delivery location method."
        elif location_method == "address" and not delivery_address:
            error = "Please enter delivery address."
        elif location_method == "gps" and (\
            not latitude or not longitude\
        ):
            error = (\
                "Please use the GPS location option before placing the order."\
            )
        elif location_method == "gps":
            try:
                latitude_value = float(latitude)
                longitude_value = float(longitude)
                if not (\
                    -90 <= latitude_value <= 90\
                    and -180 <= longitude_value <= 180\
                ):
                    raise ValueError
            except (ValueError, TypeError):
                error = (\
                    "Invalid GPS location. Please use the location button again."\
                )
        if not error:
            conn = get_db_connection()
            try:
                valid_items = []
                for item in cart.values():
                    product = conn.execute("""
                        SELECT *
                        FROM market_products
                        WHERE id = ?
                    """, (\
                        item.get("product_id"),\
                    )).fetchone()
                    if not product:
                        raise ValueError(\
                            f"Product '{item.get('product_name', 'Unknown')}' "\
                            "is no longer available."\
                        )
                    requested_quantity = float(\
                        item.get("quantity", 0)\
                    )
                    available_quantity = float(\
                        product["quantity"] or 0\
                    )
                    if requested_quantity <= 0:
                        raise ValueError(\
                            "Invalid product quantity."\
                        )
                    if available_quantity < requested_quantity:
                        raise ValueError(\
                            f"Only {available_quantity:g} "\
                            f"{product['unit'] or 'unit'} of "\
                            f"{product['product_name']} is available."\
                        )
                    valid_items.append(\
                        (product, requested_quantity)\
                    )
                if not valid_items:
                    raise ValueError(\
                        "Your cart is empty or products are unavailable."\
                    )
                final_total = sum(\
                    float(product["price"]) * quantity\
                    for product, quantity in valid_items\
                )
                reference = payment_reference
                if not reference:
                    reference = (\
                        "PAY"\
                        + datetime.now().strftime("%Y%m%d%H%M%S")\
                        + str(session["farmer_id"])\
                    )
                if location_method == "gps":
                    latitude_value = float(latitude)
                    longitude_value = float(longitude)
                else:
                    latitude_value = None
                    longitude_value = None
                cursor = conn.execute("""
                    INSERT INTO marketplace_orders
                    (
                        buyer_id,
                        total_amount,
                        status,
                        payment_status,
                        payment_method,
                        payment_reference,
                        delivery_name,
                        delivery_phone,
                        delivery_address,
                        latitude,
                        longitude,
                        location_method
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (\
                    session["farmer_id"],\
                    final_total,\
                    "Placed",\
                    "Paid",\
                    payment_method,\
                    reference,\
                    delivery_name,\
                    delivery_phone,\
                    delivery_address,\
                    latitude_value,\
                    longitude_value,\
                    location_method\
                ))
                order_id = cursor.lastrowid
                for product, quantity in valid_items:
                    subtotal = (\
                        float(product["price"])\
                        * quantity\
                    )
                    conn.execute("""
                        INSERT INTO marketplace_order_items
                        (
                            order_id,
                            product_id,
                            farmer_id,
                            product_name,
                            quantity,
                            unit,
                            price,
                            subtotal
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (\
                        order_id,\
                        product["id"],\
                        product["farmer_id"],\
                        product["product_name"],\
                        quantity,\
                        product["unit"],\
                        product["price"],\
                        subtotal\
                    ))
                    new_quantity = (\
                        float(product["quantity"])\
                        - quantity\
                    )
                    conn.execute("""
                        UPDATE market_products
                        SET quantity = ?
                        WHERE id = ?
                    """, (\
                        max(0, new_quantity),\
                        product["id"]\
                    ))
                    \
\
\
\
\
                    seller_id = product["farmer_id"]
                    product_name = product["product_name"]
                    unit_name = product["unit"] or "unit"
                    \
\
                    create_farming_alert(\
                        conn,\
                        seller_id,\
                        "Marketplace Order",\
                        "🛒 New Marketplace Order",\
                        (\
                            f"Your product {product_name} was ordered. "\
                            f"Quantity: {quantity:g} {unit_name}. "\
                            f"Order #{order_id} has been placed."\
                        ),\
                        datetime.now().strftime("%Y-%m-%d"),\
                        "High"\
                    )
                    \
\
                    create_farming_alert(\
                        conn,\
                        seller_id,\
                        "Marketplace Payment",\
                        "💰 Payment Received",\
                        (\
                            f"Payment received for {product_name}. "\
                            f"Amount: ₹{subtotal:.2f}. "\
                            f"Order #{order_id} is paid."\
                        ),\
                        datetime.now().strftime("%Y-%m-%d"),\
                        "High"\
                    )
                    \
\
                    if new_quantity <= 0:
                        create_farming_alert(\
                            conn,\
                            seller_id,\
                            "Marketplace Stock",\
                            "📦 Product Sold Out",\
                            (\
                                f"{product_name} is now sold out. "\
                                f"Please update the stock to sell it again."\
                            ),\
                            datetime.now().strftime("%Y-%m-%d"),\
                            "High"\
                        )
                    elif new_quantity <= 5:
                        create_farming_alert(\
                            conn,\
                            seller_id,\
                            "Marketplace Stock",\
                            "⚠️ Low Marketplace Stock",\
                            (\
                                f"{product_name} has only "\
                                f"{new_quantity:g} {unit_name} remaining."\
                            ),\
                            datetime.now().strftime("%Y-%m-%d"),\
                            "Medium"\
                        )
                create_farming_alert(\
                    conn,\
                    session["farmer_id"],\
                    "Marketplace Order",\
                    "📦 Order Placed Successfully",\
                    (\
                        f"Your marketplace order #{order_id} was placed "\
                        f"successfully. Total amount: ₹{final_total:.2f}. "\
                        f"Payment status: Paid."\
                    ),\
                    datetime.now().strftime("%Y-%m-%d"),\
                    "High"\
                )
                \
                conn.commit()
                session["cart"] = {}
                session.pop("checkout_delivery", None)
                session.modified = True
                return redirect(\
                    url_for(\
                        "payment_success",\
                        order_id=order_id\
                    )\
                )
            except Exception as payment_error:
                conn.rollback()
                error = str(payment_error)
                print("PAYMENT ERROR:", payment_error)
            finally:
                conn.close()
    return render_template(\
        "marketplace_payment.html",\
        cart=cart,\
        total=total,\
        error=error,\
        delivery_name=delivery_name,\
        delivery_phone=delivery_phone,\
        delivery_address=delivery_address,\
        location_method=location_method,\
        latitude=latitude,\
        longitude=longitude\
    )
@app.route("/marketplace/payment-success/<int:order_id>")
def payment_success(order_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    \
    order = conn.execute("""
        SELECT *
        FROM marketplace_orders
        WHERE id = ?
        AND buyer_id = ?
    """, (order_id, session["farmer_id"])).fetchone()
    \
    if not order:
        conn.close()
        return redirect(url_for("marketplace_orders"))
    items = conn.execute("""
        SELECT *
        FROM marketplace_order_items
        WHERE order_id = ?
        ORDER BY id ASC
    """, (order_id,)).fetchall()
    \
    conn.close()
    \
    return render_template(\
        "payment_success.html",\
        order=order,\
        items=items\
    )
@app.route(\
    "/marketplace/buy-now/<int:product_id>",\
    methods=["POST"]\
)
def buy_now(product_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    try:
        requested_quantity = float(\
            request.form.get("quantity", 1)\
        )
    except (ValueError, TypeError):
        requested_quantity = 1
    if requested_quantity <= 0:
        requested_quantity = 1
    conn = get_db_connection()
    product = conn.execute("""
        SELECT *
        FROM market_products
        WHERE id = ?
    """, (product_id,)).fetchone()
    conn.close()
    if not product or float(product["quantity"] or 0) <= 0:
        return redirect(\
            request.referrer or url_for("farm_marketplace")\
        )
    requested_quantity = min(\
        requested_quantity,\
        float(product["quantity"])\
    )
    session["cart"] = {\
        str(product_id): {\
            "product_id": product["id"],\
            "product_name": product["product_name"],\
            "price": product["price"],\
            "quantity": requested_quantity,\
            "unit": product["unit"],\
            "image": product["image"],\
            "farmer_id": product["farmer_id"],\
            "category": product["category"]\
        }\
    }
    session.modified = True
    return redirect(\
        url_for("marketplace_payment")\
    )
@app.route("/add-product")
def add_product_alias():
    return redirect(url_for("add_product"))
@app.route("/my-products")
def my_products_alias():
    return redirect(url_for("my_products"))
@app.route("/cart")
def cart_alias():
    return redirect(url_for("marketplace_cart"))
@app.route("/orders")
def orders_alias():
    return redirect(url_for("marketplace_orders"))
@app.route("/payment")
def payment_alias():
    return redirect(url_for("marketplace_payment"))
@app.route("/marketplace/orders")
def marketplace_orders():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    orders = conn.execute("""
        SELECT *
        FROM marketplace_orders
        WHERE buyer_id = ?
        ORDER BY id DESC
    """, (\
        session["farmer_id"],\
    )).fetchall()
    order_items = {}
    for order in orders:
        order_items[order["id"]] = conn.execute("""
            SELECT *
            FROM marketplace_order_items
            WHERE order_id = ?
        """, (\
            order["id"],\
        )).fetchall()
    conn.close()
    return render_template(\
        "marketplace_orders.html",\
        orders=orders,\
        order_items=order_items\
    )
@app.route("/shop")
def shop():
    return redirect(url_for("farm_marketplace"))
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
@app.route("/agribot")
def agribot():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("agribot.html")
def open_browser():
    webbrowser.open_new(\
        "http://127.0.0.1:5000/login"\
    )
@app.route("/dashboard")
def dashboard():
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template(\
        "dashboard.html",\
        farmer_name=session.get("full_name", "Farmer")\
    )
@app.route("/farm-waste", methods=["GET", "POST"])
def farm_waste():
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    waste_type = None
    waste_emoji = "♻️"
    waste_uses = []
    \
    if request.method == "POST":
        \
        waste_type = request.form.get("waste_type")
        \
        waste_data = {\
\
            "Rice Straw": {\
                "emoji": "🌾",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Rice straw can be converted into useful organic compost."\
                    },\
                    {\
                        "icon": "🐄",\
                        "title": "Animal Feed",\
                        "description": "Processed rice straw can be used as livestock feed."\
                    },\
                    {\
                        "icon": "🍄",\
                        "title": "Mushroom Cultivation",\
                        "description": "Rice straw can be used as a growing material for mushrooms."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biofuel",\
                        "description": "Rice straw can be used as biomass fuel."\
                    }\
                ]\
            },\
\
            "Corn Stalk": {\
                "emoji": "🌽",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Corn stalks can be processed into organic compost."\
                    },\
                    {\
                        "icon": "🐄",\
                        "title": "Animal Feed",\
                        "description": "Processed corn stalks can be used as livestock feed."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Organic Mulch",\
                        "description": "Corn stalks can be used as mulch around crops."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biochar",\
                        "description": "Corn residues can be converted into biochar."\
                    }\
                ]\
            },\
\
            "Wheat Straw": {\
                "emoji": "🌾",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Wheat straw can be converted into organic compost."\
                    },\
                    {\
                        "icon": "🐄",\
                        "title": "Animal Bedding",\
                        "description": "Dry wheat straw can be used as animal bedding."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Wheat straw can protect soil and help retain moisture."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biofuel",\
                        "description": "Wheat straw can be used as biomass fuel."\
                    }\
                ]\
            },\
\
            "Ragi Waste": {\
                "emoji": "🌱",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Ragi residues can be converted into compost."\
                    },\
                    {\
                        "icon": "🐄",\
                        "title": "Animal Feed",\
                        "description": "Suitable ragi residues can be used as animal feed."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Ragi waste can be used as organic mulch."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Manure",\
                        "description": "It can be processed into useful organic manure."\
                    }\
                ]\
            },\
\
            "Banana Leaves": {\
                "emoji": "🍌",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Banana leaves can be composted into organic manure."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Banana leaves can be used as natural soil mulch."\
                    },\
                    {\
                        "icon": "🐄",\
                        "title": "Animal Feed",\
                        "description": "Suitable banana leaves can be used as animal feed."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Biodegradable Products",\
                        "description": "Banana leaves can be used for biodegradable products."\
                    }\
                ]\
            },\
\
            "Banana Stem": {\
                "emoji": "🍌",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Banana stems can be processed into compost."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biogas",\
                        "description": "Banana stem waste can be used as biomass for biogas."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Chopped banana stems can be used as organic mulch."\
                    },\
                    {\
                        "icon": "🧵",\
                        "title": "Fiber Products",\
                        "description": "Banana stems contain fibers that can be used in products."\
                    }\
                ]\
            },\
\
            "Coconut Shell": {\
                "emoji": "🥥",\
                "uses": [\
                    {\
                        "icon": "🔥",\
                        "title": "Charcoal",\
                        "description": "Coconut shells can be converted into charcoal."\
                    },\
                    {\
                        "icon": "⚡",\
                        "title": "Fuel",\
                        "description": "Coconut shells can be used as biomass fuel."\
                    },\
                    {\
                        "icon": "🧪",\
                        "title": "Activated Carbon",\
                        "description": "Processed coconut shells can be used to produce activated carbon."\
                    },\
                    {\
                        "icon": "♻️",\
                        "title": "Biomass Products",\
                        "description": "Shells can be processed into various biomass products."\
                    }\
                ]\
            },\
\
            "Coconut Husk": {\
                "emoji": "🥥",\
                "uses": [\
                    {\
                        "icon": "🧵",\
                        "title": "Coir",\
                        "description": "Coconut husk is widely used to produce coir fiber."\
                    },\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Husk can be processed into organic compost."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Coconut husk can be used as natural mulch."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Growing Material",\
                        "description": "Processed coconut fiber can be used as a growing medium."\
                    }\
                ]\
            },\
\
            "Sugarcane Bagasse": {\
                "emoji": "🎋",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Bagasse can be processed into organic compost."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biofuel",\
                        "description": "Sugarcane bagasse can be used as biomass fuel."\
                    },\
                    {\
                        "icon": "📄",\
                        "title": "Paper Products",\
                        "description": "Bagasse fiber can be used to make paper products."\
                    },\
                    {\
                        "icon": "⚡",\
                        "title": "Biomass Energy",\
                        "description": "Bagasse can be used for biomass energy production."\
                    }\
                ]\
            },\
\
            "Groundnut Shell": {\
                "emoji": "🥜",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Groundnut shells can be processed into compost."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Fuel",\
                        "description": "Groundnut shells can be used as biomass fuel."\
                    },\
                    {\
                        "icon": "🐄",\
                        "title": "Animal Bedding",\
                        "description": "Processed shells can be used as animal bedding."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Biochar",\
                        "description": "Groundnut shells can be converted into biochar."\
                    }\
                ]\
            },\
\
            "Pulses Waste": {\
                "emoji": "🫘",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Pulse residues can be converted into compost."\
                    },\
                    {\
                        "icon": "🐄",\
                        "title": "Animal Feed",\
                        "description": "Suitable pulse residues can be used as animal feed."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Manure",\
                        "description": "Pulse waste can be processed into organic manure."\
                    }\
                ]\
            },\
\
            "Vegetable Waste": {\
                "emoji": "🥬",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Vegetable waste can be converted into organic compost."\
                    },\
                    {\
                        "icon": "🪱",\
                        "title": "Vermicompost",\
                        "description": "Vegetable waste can be used for vermicomposting."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biogas",\
                        "description": "Organic vegetable waste can be used for biogas production."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Fertilizer",\
                        "description": "Processed vegetable waste can become organic fertilizer."\
                    }\
                ]\
            },\
\
            "Fruit Waste": {\
                "emoji": "🍎",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Fruit waste can be converted into compost."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Fertilizer",\
                        "description": "Fruit residues can be processed into organic fertilizer."\
                    },\
                    {\
                        "icon": "🐄",\
                        "title": "Animal Feed",\
                        "description": "Some suitable fruit residues can be used as animal feed."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biogas",\
                        "description": "Fruit waste can be used as organic material for biogas."\
                    }\
                ]\
            },\
\
            "Leaves": {\
                "emoji": "🌿",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Dry leaves are useful for making organic compost."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Leaves can be used as natural soil mulch."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Fertilizer",\
                        "description": "Decomposed leaves improve soil organic matter."\
                    }\
                ]\
            },\
\
            "Weeds": {\
                "emoji": "🌱",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Suitable weeds can be processed into compost."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Manure",\
                        "description": "Processed weed material can become organic manure."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Properly prepared weed material can be used as mulch."\
                    }\
                ]\
            },\
\
            "Dry Grass": {\
                "emoji": "🌾",\
                "uses": [\
                    {\
                        "icon": "🐄",\
                        "title": "Animal Feed",\
                        "description": "Suitable dry grass can be used as livestock feed."\
                    },\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Dry grass is useful as a carbon-rich compost material."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Dry grass can help protect soil and retain moisture."\
                    },\
                    {\
                        "icon": "🐄",\
                        "title": "Animal Bedding",\
                        "description": "Dry grass can be used as animal bedding."\
                    }\
                ]\
            },\
\
            "Cow Dung": {\
                "emoji": "🐄",\
                "uses": [\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Fertilizer",\
                        "description": "Cow dung can be processed into organic fertilizer."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biogas",\
                        "description": "Cow dung is commonly used as feedstock for biogas."\
                    },\
                    {\
                        "icon": "🪱",\
                        "title": "Vermicompost",\
                        "description": "Cow dung can be used in vermicomposting."\
                    },\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Cow dung can be combined with crop residues for compost."\
                    }\
                ]\
            },\
\
            "Goat Manure": {\
                "emoji": "🐐",\
                "uses": [\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Manure",\
                        "description": "Goat manure is a useful organic nutrient source."\
                    },\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Goat manure can be processed into compost."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Soil Improvement",\
                        "description": "Processed manure can help improve soil organic matter."\
                    }\
                ]\
            },\
\
            "Poultry Waste": {\
                "emoji": "🐔",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Poultry waste can be processed into compost."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Fertilizer",\
                        "description": "Properly processed poultry waste can provide nutrients."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Soil Improvement",\
                        "description": "Composted poultry waste can improve soil fertility."\
                    }\
                ]\
            },\
\
            "Tree Branches": {\
                "emoji": "🌳",\
                "uses": [\
                    {\
                        "icon": "🪵",\
                        "title": "Wood Chips",\
                        "description": "Branches can be chipped for various farm uses."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Wood chips can be used as natural mulch."\
                    },\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Small branches can be processed as compost material."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biomass Fuel",\
                        "description": "Dry branches can be used as biomass fuel."\
                    }\
                ]\
            },\
\
            "Tree Leaves": {\
                "emoji": "🌳",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Tree leaves can be converted into organic compost."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Leaves can be used as natural mulch around plants."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Fertilizer",\
                        "description": "Decomposed leaves contribute organic matter to soil."\
                    }\
                ]\
            },\
\
            "Wood Waste": {\
                "emoji": "🪵",\
                "uses": [\
                    {\
                        "icon": "🔥",\
                        "title": "Biomass Fuel",\
                        "description": "Suitable dry wood waste can be used as biomass fuel."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Wood chips can be used as soil mulch."\
                    },\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Small untreated wood pieces can be processed with other compost materials."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Biochar",\
                        "description": "Suitable wood waste can be converted into biochar."\
                    }\
                ]\
            },\
\
            "Potato Peels": {\
                "emoji": "🥔",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Potato peels can be added to compost."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Manure",\
                        "description": "Processed potato waste can contribute to organic manure."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biogas",\
                        "description": "Potato waste can be used as organic feedstock for biogas."\
                    }\
                ]\
            },\
\
            "Onion Peels": {\
                "emoji": "🧅",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Onion peels can be added to organic compost."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Fertilizer",\
                        "description": "Processed onion waste can contribute to organic fertilizer."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Organic Waste Recycling",\
                        "description": "Onion peels can be recycled through suitable composting methods."\
                    }\
                ]\
            },\
\
            "Tomato Waste": {\
                "emoji": "🍅",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Tomato waste can be converted into compost."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Manure",\
                        "description": "Processed tomato residues can contribute to organic manure."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biogas",\
                        "description": "Tomato waste can be used as organic material for biogas."\
                    }\
                ]\
            },\
\
            "Vegetable Crop Residue": {\
                "emoji": "🌶️",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Compost",\
                        "description": "Crop residues can be converted into useful compost."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Mulch",\
                        "description": "Suitable residues can be used as organic mulch."\
                    },\
                    {\
                        "icon": "🐄",\
                        "title": "Animal Feed",\
                        "description": "Some suitable crop residues can be used as livestock feed."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Organic Manure",\
                        "description": "Crop residues can be processed into organic manure."\
                    }\
                ]\
            },\
\
            "Other Farm Waste": {\
                "emoji": "♻️",\
                "uses": [\
                    {\
                        "icon": "♻️",\
                        "title": "Recycling",\
                        "description": "Suitable farm waste can be sorted and recycled."\
                    },\
                    {\
                        "icon": "🌿",\
                        "title": "Compost",\
                        "description": "Organic waste can often be processed into compost."\
                    },\
                    {\
                        "icon": "🌱",\
                        "title": "Organic Manure",\
                        "description": "Suitable organic residues can be converted into manure."\
                    },\
                    {\
                        "icon": "🔥",\
                        "title": "Biomass",\
                        "description": "Suitable dry agricultural residues can be used as biomass."\
                    }\
                ]\
            }\
\
        }
        \
\
        if waste_type in waste_data:
            \
            waste_emoji = waste_data[waste_type]["emoji"]
            \
            waste_uses = waste_data[waste_type]["uses"]
    return render_template(\
        "farm_waste.html",\
\
        waste_type=waste_type,\
\
        waste_emoji=waste_emoji,\
\
        waste_uses=waste_uses\
    )
@app.route("/profile")
def profile():
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    farmer = {\
        "full_name": session.get("full_name", "Farmer"),\
        "username": session.get("username", "Not available"),\
        "email": session.get("email", "Not available"),\
        "phone_number": session.get("phone_number", "Not available"),\
        "vehicle_number": session.get("vehicle_number", "Not available")\
    }
    \
    return render_template(\
        "profile.html",\
        farmer=farmer\
    )
@app.route("/edit-profile")
def edit_profile():
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    farmer = {\
        "full_name": session.get("full_name", ""),\
        "username": session.get("username", ""),\
        "email": session.get("email", ""),\
        "phone_number": session.get("phone_number", ""),\
        "vehicle_number": session.get("vehicle_number", "")\
    }
    \
    return render_template(\
        "edit_profile.html",\
        farmer=farmer\
    )
@app.route("/update-profile", methods=["POST"])
def update_profile():
    \
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    session["full_name"] = request.form.get("full_name", "")
    session["username"] = request.form.get("username", "")
    session["email"] = request.form.get("email", "")
    session["phone_number"] = request.form.get("phone_number", "")
    session["vehicle_number"] = request.form.get("vehicle_number", "")
    \
    return redirect(url_for("profile"))
@app.route("/predict-disease", methods=["POST"])
def predict_disease():

    import os
    import json
    import torch
    import torch.nn as nn
    from PIL import Image
    from torchvision import models, transforms

    # ==========================================================
    # MODEL FILES
    # ==========================================================

    MODEL_PATH = os.path.join(
        "disease_model",
        "plant_disease_model.pth"
    )

    CLASSES_PATH = os.path.join(
        "disease_model",
        "classes.json"
    )

    # ==========================================================
    # CHECK MODEL
    # ==========================================================

    if not os.path.exists(MODEL_PATH):
        return {
            "success": False,
            "message": "Disease model file not found."
        }

    if not os.path.exists(CLASSES_PATH):
        return {
            "success": False,
            "message": "Disease classes file not found."
        }

    # ==========================================================
    # GET UPLOADED IMAGE
    # ==========================================================

    uploaded_file = request.files.get("image")

    if uploaded_file is None:
        uploaded_file = request.files.get("file")

    if uploaded_file is None:
        return {
            "success": False,
            "message": "Please upload a plant image."
        }

    if uploaded_file.filename == "":
        return {
            "success": False,
            "message": "Please select an image."
        }

    # ==========================================================
    # LOAD CLASS NAMES
    # ==========================================================

    with open(CLASSES_PATH, "r", encoding="utf-8") as file:
        classes = json.load(file)

    # ==========================================================
    # LOAD MODEL
    # ==========================================================

    model = models.resnet18(weights=None)

    number_of_classes = len(classes)

    model.fc = nn.Linear(
        model.fc.in_features,
        number_of_classes
    )

    model.load_state_dict(
        torch.load(
            MODEL_PATH,
            map_location=torch.device("cpu")
        )
    )

    model.eval()

    # ==========================================================
    # IMAGE TRANSFORM
    # ==========================================================

    transform = transforms.Compose([
        transforms.Resize((160, 160)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    # ==========================================================
    # OPEN IMAGE
    # ==========================================================

    try:
        image = Image.open(uploaded_file).convert("RGB")
    except Exception:
        return {
            "success": False,
            "message": "Invalid image file."
        }

    image_tensor = transform(image)

    image_tensor = image_tensor.unsqueeze(0)

    # ==========================================================
    # PREDICTION
    # ==========================================================

    with torch.no_grad():

        outputs = model(image_tensor)

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

        confidence, predicted_index = torch.max(
            probabilities,
            1
        )

    predicted_index = predicted_index.item()

    confidence = confidence.item() * 100

    disease = classes[predicted_index]

    # ==========================================================
    # FORMAT DISEASE NAME
    # ==========================================================

    display_disease = disease.replace("___", " - ")
    display_disease = display_disease.replace("_", " ")

    # ==========================================================
    # RETURN RESULT
    # ==========================================================

    return {
        "success": True,
        "disease": display_disease,
        "confidence": round(confidence, 2),
        "symptoms": (
            "Dark brown to black spots may appear on the leaves. "
        "In humid conditions, the affected areas can spread quickly. "
        "Leaves may eventually turn brown and dry."
    ),

    "treatment": (
        "Remove and safely dispose of severely infected leaves. "
        "Avoid overhead watering and improve air circulation. "
        "Use an appropriate fungicide according to the product label "
        "and local agricultural recommendations."
    ),

    "message": "Disease prediction completed successfully."
}
if __name__ == "__main__":
    create_crop_table()
    create_expenses_table()
    create_marketplace_table()
    create_activity_table()
    create_alerts_table()
    create_farm_waste_table()
    \
    Timer(1, open_browser).start()
    app.run(debug=True)