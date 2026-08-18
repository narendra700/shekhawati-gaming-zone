from flask import Flask, request, jsonify, send_from_directory, session, redirect
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

ENV_FILE = os.path.join(
    BASE_DIR,
    ".env"
)

print("======================================")
print("ENV FILE:", ENV_FILE)
print("ENV EXISTS:", os.path.exists(ENV_FILE))
print("======================================")


load_dotenv(
    ENV_FILE,
    override=True
)


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)


# Same-origin website ke liye CORS required nahi hai,
# lekin existing project compatibility ke liye enabled rakha hai.
CORS(app)


# =========================================================
# SESSION CONFIGURATION
# =========================================================

app.secret_key = os.getenv(
    "SECRET_KEY",
    "temporary-secret-key-change-this"
)


# Session 8 hours tak valid rahegi
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
    hours=8
)


# Browser JavaScript ko session cookie read nahi karne dena
app.config["SESSION_COOKIE_HTTPONLY"] = True


# Normal same-site protection
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# Render HTTPS par secure cookie
# Local computer par HTTP hone par False rahega
app.config["SESSION_COOKIE_SECURE"] = (
    os.getenv(
        "SESSION_COOKIE_SECURE",
        "false"
    ).lower() == "true"
)


# =========================================================
# ADMIN LOGIN SETTINGS
# =========================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "admin123"
)


# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


# =========================================================
# GET DATABASE CONNECTION
# =========================================================

def get_database():

    if not DATABASE_URL:

        raise Exception(
            "DATABASE_URL environment variable is missing."
        )

    connection = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor,
        connect_timeout=10
    )

    return connection


# =========================================================
# INDIA TIME
# =========================================================

def get_india_time():

    india_timezone = timezone(
        timedelta(
            hours=5,
            minutes=30
        )
    )

    return datetime.now(
        india_timezone
    ).strftime(
        "%Y-%m-%d %I:%M:%S %p"
    )


# =========================================================
# CREATE / UPDATE DATABASE
# =========================================================

def create_table():

    connection = None
    cursor = None

    try:

        connection = get_database()

        cursor = connection.cursor()


        # -------------------------------------------------
        # CREATE BOOKINGS TABLE
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (

                id SERIAL PRIMARY KEY,

                name TEXT NOT NULL,

                mobile TEXT NOT NULL,

                service TEXT NOT NULL,

                date TEXT NOT NULL,

                time TEXT NOT NULL,

                message TEXT,

                status TEXT DEFAULT 'Pending',

                received_at TEXT

            )
        """)


        # -------------------------------------------------
        # GET EXISTING COLUMNS
        # -------------------------------------------------

        cursor.execute("""
            SELECT column_name

            FROM information_schema.columns

            WHERE table_name = 'bookings'
        """)


        columns = [
            column["column_name"]
            for column in cursor.fetchall()
        ]


        # -------------------------------------------------
        # MESSAGE COLUMN
        # -------------------------------------------------

        if "message" not in columns:

            cursor.execute("""
                ALTER TABLE bookings
                ADD COLUMN message TEXT
            """)

            print(
                "Message column added."
            )


        # -------------------------------------------------
        # STATUS COLUMN
        # -------------------------------------------------

        if "status" not in columns:

            cursor.execute("""
                ALTER TABLE bookings
                ADD COLUMN status TEXT DEFAULT 'Pending'
            """)

            print(
                "Status column added."
            )


        # -------------------------------------------------
        # RECEIVED_AT COLUMN
        # -------------------------------------------------

        if "received_at" not in columns:

            cursor.execute("""
                ALTER TABLE bookings
                ADD COLUMN received_at TEXT
            """)

            print(
                "Received At column added."
            )


        # -------------------------------------------------
        # FIX EMPTY STATUS
        # -------------------------------------------------

        cursor.execute("""
            UPDATE bookings

            SET status = 'Pending'

            WHERE status IS NULL
            OR status = ''
        """)


        # -------------------------------------------------
        # FIX OLD BOOKING TIME
        # -------------------------------------------------

        cursor.execute("""
            UPDATE bookings

            SET received_at = %s

            WHERE received_at IS NULL
            OR received_at = ''
        """, (
            get_india_time(),
        ))


        connection.commit()


        print("======================================")
        print("Neon PostgreSQL bookings table ready!")
        print("======================================")


    except Exception as error:

        if connection:

            connection.rollback()

        print(
            "DATABASE INITIALIZATION ERROR:"
        )

        print(
            error
        )

        raise


    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()


# =========================================================
# INITIALIZE DATABASE
# =========================================================

create_table()


# =========================================================
# MAIN WEBSITE
# =========================================================

@app.route("/")
def home():

    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


# =========================================================
# WEBSITE FILES
# =========================================================

@app.route(
    "/<path:filename>"
)
def website_files(filename):

    # -----------------------------------------------------
    # SECURITY
    # Sensitive files ko public access se block karo
    # -----------------------------------------------------

    normalized_path = os.path.normpath(
        filename
    ).replace("\\", "/")


    blocked_files = [

        ".env",

        ".git",

        "requirements.txt",

        "app.py",

        "backend",

        "__pycache__"

    ]


    first_part = normalized_path.split("/")[0]


    if (
        normalized_path.startswith(".")
        or
        first_part in blocked_files
    ):

        return jsonify({
            "success": False,
            "message": "Not found."
        }), 404


    return send_from_directory(
        BASE_DIR,
        filename
    )


# =========================================================
# ADMIN LOGIN PAGE
# =========================================================

@app.route(
    "/admin/login",
    methods=["GET"]
)
def admin_login_page():

    if session.get(
        "admin_logged_in"
    ) is True:

        return redirect(
            "/admin"
        )


    return send_from_directory(
        os.path.join(
            BASE_DIR,
            "admin"
        ),
        "login.html"
    )


# =========================================================
# ADMIN LOGIN API
# =========================================================

@app.route(
    "/admin/login",
    methods=["POST"]
)
def admin_login():

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({
            "success": False,
            "message":
                "Invalid login request."
        }), 400


    username = str(
        data.get(
            "username",
            ""
        )
    ).strip()


    password = str(
        data.get(
            "password",
            ""
        )
    )


    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if (
        username == ADMIN_USERNAME
        and
        password == ADMIN_PASSWORD
    ):

        # Purani session data clear
        session.clear()


        # Session ko permanent banao
        session.permanent = True


        # Admin login state
        session[
            "admin_logged_in"
        ] = True


        return jsonify({
            "success": True,
            "message":
                "Login successful."
        })


    return jsonify({
        "success": False,
        "message":
            "Invalid username or password."
    }), 401


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route(
    "/admin/logout",
    methods=["POST"]
)
def admin_logout():

    session.clear()


    return jsonify({
        "success": True,
        "message":
            "Logged out successfully."
    })


# =========================================================
# ADMIN PAGE
# =========================================================

@app.route(
    "/admin"
)
def admin_page():

    if not admin_required():

        return redirect(
            "/admin/login"
        )


    return send_from_directory(
        os.path.join(
            BASE_DIR,
            "admin"
        ),
        "index.html"
    )


# =========================================================
# ADMIN AUTH CHECK
# =========================================================

def admin_required():

    return (
        session.get(
            "admin_logged_in"
        ) is True
    )


# =========================================================
# ADMIN JAVASCRIPT
# =========================================================

@app.route(
    "/admin.js"
)
def admin_javascript():

    if not admin_required():

        return "", 401


    return send_from_directory(
        os.path.join(
            BASE_DIR,
            "admin"
        ),
        "admin.js"
    )


# =========================================================
# NEW BOOKING
# =========================================================

@app.route(
    "/booking",
    methods=["POST"]
)
def booking():

    data = request.get_json(
        silent=True
    )


    # -----------------------------------------------------
    # CHECK JSON
    # -----------------------------------------------------

    if not data:

        return jsonify({
            "success": False,
            "message":
                "Invalid booking data."
        }), 400


    # -----------------------------------------------------
    # GET DATA
    # -----------------------------------------------------

    name = str(
        data.get(
            "name",
            ""
        )
    ).strip()


    mobile = str(
        data.get(
            "mobile",
            ""
        )
    ).strip()


    service = str(
        data.get(
            "service",
            ""
        )
    ).strip()


    date = str(
        data.get(
            "date",
            ""
        )
    ).strip()


    time = str(
        data.get(
            "time",
            ""
        )
    ).strip()


    message = str(
        data.get(
            "message",
            ""
        )
    ).strip()


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if (
        not name
        or
        not mobile
        or
        not service
        or
        not date
        or
        not time
    ):

        return jsonify({
            "success": False,
            "message":
                "Please fill all required fields."
        }), 400


    # -----------------------------------------------------
    # INDIA RECEIVED TIME
    # -----------------------------------------------------

    received_at = get_india_time()


    connection = None
    cursor = None


    try:

        connection = get_database()

        cursor = connection.cursor()


        # -------------------------------------------------
        # INSERT BOOKING
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO bookings
            (
                name,
                mobile,
                service,
                date,
                time,
                message,
                status,
                received_at
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )

            RETURNING id
        """, (
            name,
            mobile,
            service,
            date,
            time,
            message,
            "Pending",
            received_at
        ))


        result = cursor.fetchone()


        booking_id = result[
            "id"
        ]


        connection.commit()


        print(
            f"New booking #{booking_id} "
            f"received at {received_at}"
        )


        return jsonify({
            "success": True,
            "message":
                "Booking saved successfully!",
            "booking_id":
                booking_id,
            "received_at":
                received_at
        })


    except Exception as error:

        if connection:

            connection.rollback()


        print(
            "BOOKING SAVE ERROR:"
        )

        print(
            error
        )


        return jsonify({
            "success": False,
            "message":
                "Unable to save booking."
        }), 500


    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()


# =========================================================
# ADMIN - GET BOOKINGS
# =========================================================

@app.route(
    "/admin/bookings",
    methods=["GET"]
)
def admin_bookings():

    if not admin_required():

        return jsonify({
            "success": False,
            "message":
                "Unauthorized."
        }), 401


    connection = None
    cursor = None


    try:

        connection = get_database()

        cursor = connection.cursor()


        cursor.execute("""
            SELECT

                id,

                name,

                mobile,

                service,

                date,

                time,

                received_at,

                message,

                status

            FROM bookings

            ORDER BY id DESC
        """)


        bookings = cursor.fetchall()


        return jsonify([
            dict(booking)
            for booking in bookings
        ])


    except Exception as error:

        print(
            "ADMIN BOOKINGS ERROR:"
        )

        print(
            error
        )


        return jsonify({
            "success": False,
            "message":
                "Unable to load bookings."
        }), 500


    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()


# =========================================================
# ADMIN - UPDATE BOOKING STATUS
# =========================================================

@app.route(
    "/admin/bookings/<int:booking_id>/status",
    methods=["PUT"]
)
def update_booking_status(
    booking_id
):

    if not admin_required():

        return jsonify({
            "success": False,
            "message":
                "Unauthorized."
        }), 401


    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({
            "success": False,
            "message":
                "Invalid request."
        }), 400


    status = data.get(
        "status"
    )


    # -----------------------------------------------------
    # ALLOWED STATUS
    # -----------------------------------------------------

    allowed_statuses = [

        "Pending",

        "Confirmed",

        "Completed",

        "Cancelled"

    ]


    if status not in allowed_statuses:

        return jsonify({
            "success": False,
            "message":
                "Invalid booking status."
        }), 400


    connection = None
    cursor = None


    try:

        connection = get_database()

        cursor = connection.cursor()


        cursor.execute("""
            UPDATE bookings

            SET status = %s

            WHERE id = %s
        """, (
            status,
            booking_id
        ))


        if cursor.rowcount == 0:

            connection.rollback()

            return jsonify({
                "success": False,
                "message":
                    "Booking not found."
            }), 404


        connection.commit()


        print(
            f"Booking {booking_id} "
            f"status changed to {status}"
        )


        return jsonify({
            "success": True,
            "message":
                "Booking status updated successfully."
        })


    except Exception as error:

        if connection:

            connection.rollback()


        print(
            "STATUS UPDATE ERROR:"
        )

        print(
            error
        )


        return jsonify({
            "success": False,
            "message":
                "Unable to update booking status."
        }), 500


    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()


# =========================================================
# ADMIN - DELETE BOOKING
# =========================================================

@app.route(
    "/admin/bookings/<int:booking_id>",
    methods=["DELETE"]
)
def delete_booking(
    booking_id
):

    if not admin_required():

        return jsonify({
            "success": False,
            "message":
                "Unauthorized."
        }), 401


    connection = None
    cursor = None


    try:

        connection = get_database()

        cursor = connection.cursor()


        cursor.execute("""
            DELETE FROM bookings

            WHERE id = %s
        """, (
            booking_id,
        ))


        if cursor.rowcount == 0:

            connection.rollback()

            return jsonify({
                "success": False,
                "message":
                    "Booking not found."
            }), 404


        connection.commit()


        print(
            f"Booking {booking_id} deleted!"
        )


        return jsonify({
            "success": True,
            "message":
                "Booking deleted successfully."
        })


    except Exception as error:

        if connection:

            connection.rollback()


        print(
            "DELETE BOOKING ERROR:"
        )

        print(
            error
        )


        return jsonify({
            "success": False,
            "message":
                "Unable to delete booking."
        }), 500


    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/health"
)
def health():

    connection = None
    cursor = None


    try:

        connection = get_database()

        cursor = connection.cursor()


        cursor.execute(
            "SELECT 1"
        )


        cursor.fetchone()


        return jsonify({
            "success": True,
            "database":
                "connected"
        })


    except Exception as error:

        print(
            "HEALTH CHECK ERROR:"
        )

        print(
            error
        )


        return jsonify({
            "success": False,
            "database":
                "error",
            "message":
                str(error)
        }), 500


    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )


    app.run(
        debug=False,
        host="0.0.0.0",
        port=port
    )