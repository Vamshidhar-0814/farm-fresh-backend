# set up basic flask app
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import psycopg2
import json  # Add this import at the top of the file
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from service import send_order_confirmation

load_dotenv()

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

app = Flask(__name__)

# Enable CORS for specific origins
CORS(app, resources={r"/*": {"origins": os.getenv("FRONTEND_ORIGIN_PROD", "*")}})



@app.route("/test-db")
def test_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT NOW()")
            return {"timestamp": cur.fetchone()[0]}

@app.route("/products", methods=["GET", "POST"])
def get_products():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM product_catalog")
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/place-order", methods=["POST"])
def place_order():
    try:
        data = request.json

        # Validate required fields
        required_fields = ["name", "address", "city", "zip", "state", "phone", "email", "orderdetails"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        print("Received data:", data)

        # Serialize orderdetails to JSON string
        orderdetails_json = json.dumps(data["orderdetails"])

        with get_connection() as conn:
            with conn.cursor() as cur:
                # Insert the order and return the generated order ID
                cur.execute(
                    """
                    INSERT INTO orders (name, address, city, zip, state, orderdate, phone, email, orderdetails)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        data["name"],
                        data["address"],
                        data["city"],
                        data["zip"],
                        data["state"],
                        data["phone"],
                        data["email"],
                        orderdetails_json,  # Use the serialized JSON string
                    ),
                )
                order_id = cur.fetchone()[0]  # Fetch the generated order ID
                conn.commit()
        
        whatsapp_status = send_order_confirmation(phone_number=data["phone"], order_id=order_id)
        print("WhatsApp status:", whatsapp_status)


        print("Order placed successfully. Order ID:", order_id)

        return jsonify({"status": "success", "order_id": order_id}), 201
    except KeyError as e:
        return jsonify({"error": f"Missing key in request data: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/orders", methods=["GET", "POST"])
def get_orders():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM orders")
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json

        print("Received login data:", data)

        # Validate required fields
        if "email" not in data or "password" not in data:
            return jsonify({"error": "Email and password are required"}), 400

        email = data["email"]
        password = data["password"]

        with get_connection() as conn:
            with conn.cursor() as cur:
                # Query to check if the user exists and the password matches
                cur.execute(
                    "SELECT id, name FROM users WHERE email = %s AND password = %s",
                    (email, password),
                )
                user = cur.fetchone()

                print("User found:", user)

                if user:
                    # If user is found, return success response
                    return jsonify({"status": "success", "user": {"id": user[0], "name": user[1]}}), 200
                else:
                    # If user is not found, return error response
                    return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
