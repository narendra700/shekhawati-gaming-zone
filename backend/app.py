from flask import Flask, request,jsonify, send_from_directory, session, redirect
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
    os.path.dirname(os.path.abspath(__file__))
)

ENV_FILE = os.path.join(
    BASE_DIR,
    ".env"
)

print("ENV FILE:", ENV_FILE)
print("ENV EXISTS:", os.path.exists(ENV_FILE))

load_dotenv(
    ENV_FILE,
    override=True
)

# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

CORS(app)


# =========================================================
# ADMIN LOGIN SETTINGS
# =========================================================

app.secret_key = os.getenv(
    "SECRET_KEY",
    "temporary-secret-key-change-this"
)

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "admin123"
)


# =========================================================
# NEON POSTGRESQL DATABASE
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")


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
        cursor_factory=RealDictCursor
    )

    return connection


# =========================================================
# INDIA TIME
# =========================================================

def get_india_time():

    india_timezone = timezone(
        timedelta(hours=5, minutes=30)
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

    connection = get_database()

    cursor = connection.cursor()

    try:

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
        # CHECK EXISTING COLUMNS
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
        # ADD MESSAGE COLUMN IF MISSING
        # -------------------------------------------------

        if "message" not in columns:

            cursor.execute("""
                ALTER TABLE bookings
                ADD COLUMN message TEXT
            """)

            print(
                "Message column added!"
            )


        # -------------------------------------------------
        # ADD STATUS COLUMN IF MISSING
        # -------------------------------------------------

        if "status" not in columns:

            cursor.execute("""
                ALTER TABLE bookings
                ADD COLUMN status TEXT DEFAULT 'Pending'
            """)

            print(
                "Status column added!"
            )


        # -------------------------------------------------
        # ADD RECEIVED_AT COLUMN IF MISSING
        # -------------------------------------------------

        if "received_at" not in columns:

            cursor.execute("""
                ALTER TABLE bookings
                ADD COLUMN received_at TEXT
            """)

            print(
                "Received At column added!"
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
        # FIX OLD BOOKINGS RECEIVED TIME
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

        print(
            "======================================"
        )

        print(
            "Neon PostgreSQL bookings table ready!"
        )

        print(
            "======================================"
        )

    except Exception as error:

        connection.rollback()

        print(
            "DATABASE INITIALIZATION ERROR:"
        )

        print(
            error
        )

        raise

    finally:

        cursor.close()
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

@app.route("/<path:filename>")
def website_files(filename):

    return send_from_directory(
        BASE_DIR,
        filename
    )


# =========================================================
# ADMIN LOGIN PAGE
# =========================================================

@app.route("/admin/login")
def admin_login_page():

    if session.get(
        "admin_logged_in"
    ):

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

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message":
                "Invalid login request."
        }), 400


    username = data.get(
        "username"
    )

    password = data.get(
        "password"
    )


    if (
        username == ADMIN_USERNAME
        and
        password == ADMIN_PASSWORD
    ):

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

    session.pop(
        "admin_logged_in",
        None
    )

    return jsonify({
        "success": True,
        "message":
            "Logged out successfully."
    })


# =========================================================
# ADMIN PAGE
# =========================================================

@app.route("/admin")
def admin_page():

    if not session.get(
        "admin_logged_in"
    ):

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
        )
        is True
    )


# =========================================================
# ADMIN JAVASCRIPT
# =========================================================

@app.route("/admin.js")
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

    data = request.get_json()

    # -----------------------------------------------------
    # CHECK JSON DATA
    # -----------------------------------------------------

    if not data:

        return jsonify({
            "success": False,
            "message":
                "Invalid booking data."
        }), 400


    # -----------------------------------------------------
    # GET BOOKING DATA
    # -----------------------------------------------------

    name = data.get(
        "name"
    )

    mobile = data.get(
        "mobile"
    )

    service = data.get(
        "service"
    )

    date = data.get(
        "date"
    )

    time = data.get(
        "time"
    )

    message = data.get(
        "message",
        ""
    )


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if (
        not name
        or not mobile
        or not service
        or not date
        or not time
    ):

        return jsonify({
            "success": False,
            "message":
                "Please fill all required fields."
        }), 400


    # -----------------------------------------------------
    # EXACT INDIA RECEIVED TIME
    # -----------------------------------------------------

    received_at = get_india_time()


    # -----------------------------------------------------
    # SAVE BOOKING
    # -----------------------------------------------------

    connection = get_database()

    cursor = connection.cursor()

    try:

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

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)

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

        booking_id = result["id"]

        connection.commit()

    except Exception as error:

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

        cursor.close()
        connection.close()


    # -----------------------------------------------------
    # SERVER LOG
    # -----------------------------------------------------

    print(
        f"New booking #{booking_id} "
        f"received at {received_at}"
    )


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return jsonify({
        "success": True,
        "message":
            "Booking saved successfully!",
        "booking_id":
            booking_id,
        "received_at":
            received_at
    })


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


    connection = get_database()

    cursor = connection.cursor()

    try:

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

    except Exception as error:

        print(
            "ADMIN BOOKINGS ERROR:"
        )

        print(
            error
        )

        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message":
                "Unable to load bookings."
        }), 500

    cursor.close()
    connection.close()


    return jsonify([
        dict(booking)
        for booking in bookings
    ])


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


    data = request.get_json()

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


    connection = get_database()

    cursor = connection.cursor()


    try:

        cursor.execute("""
            UPDATE bookings

            SET status = %s

            WHERE id = %s
        """, (
            status,
            booking_id
        ))

        connection.commit()


        # -------------------------------------------------
        # CHECK BOOKING
        # -------------------------------------------------

        if cursor.rowcount == 0:

            return jsonify({
                "success": False,
                "message":
                    "Booking not found."
            }), 404


    except Exception as error:

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

        cursor.close()
        connection.close()


    print(
        f"Booking {booking_id} "
        f"status changed to {status}"
    )


    return jsonify({
        "success": True,
        "message":
            "Booking status updated successfully."
    })


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


    connection = get_database()

    cursor = connection.cursor()


    try:

        cursor.execute("""
            DELETE FROM bookings

            WHERE id = %s
        """, (
            booking_id,
        ))

        connection.commit()


        # -------------------------------------------------
        # CHECK BOOKING
        # -------------------------------------------------

        if cursor.rowcount == 0:

            return jsonify({
                "success": False,
                "message":
                    "Booking not found."
            }), 404


    except Exception as error:

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

        cursor.close()
        connection.close()


    print(
        f"Booking {booking_id} deleted!"
    )


    return jsonify({
        "success": True,
        "message":
            "Booking deleted successfully."
    })


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    try:

        connection = get_database()

        cursor = connection.cursor()

        cursor.execute("SELECT 1")

        cursor.fetchone()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "database": "connected"
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "database": "error",
            "message": str(error)
        }), 500


# =========================================================
# START LOCAL SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=False,
        host="127.0.0.1",
        port=5000
    )