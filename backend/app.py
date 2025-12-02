from flask import Flask, jsonify, request
from flask_cors import CORS
import db as db_module
import bcrypt
import secrets
import mailer
import threading

app = Flask(__name__)
CORS(app)


@app.route("/")
def hello():
    return jsonify({"message": "Hello from Flask!"})


@app.route("/labels", methods=["GET"])
def get_labels():
    return jsonify(db_module.get_all_labels())


@app.route("/user/register", methods=["POST"])
def create_user():
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    name = data.get("name")
    email = data.get("email")
    pswd = data.get("pswd")

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not pswd:
        return jsonify({"error": "Password is required"}), 400
    if not email:
        return jsonify({"error": "Email is required"}), 400

    pswd_hash = bcrypt.hashpw(pswd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    confirmation_token = secrets.token_urlsafe(32)

    try:
        user = db_module.create_user(name, email, pswd_hash, verified=False, confirmation_token=confirmation_token)
        
        # Generate confirmation URL
        confirmation_url = f"http://localhost:5000/user/confirm?token={confirmation_token}"
        
        # Send email
        html = mailer.render_template(
            'register.html',
            user_name=name,
            confirmation_url=confirmation_url,
            app_name='我们的应用',
            support_email='support@example.com',
            current_year=2025
        )
        
        # Send email asynchronously
        threading.Thread(
            target=mailer.send_email,
            kwargs={
                'to_email': email,
                'subject': "完成注册 - 我们的应用",
                'content': "请点击链接完成注册。",
                'html': html
            }
        ).start()
        
        return jsonify({"message": "User created, confirmation email sent", "user_id": user['id']}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/user/confirm", methods=["GET"])
def confirm_user():
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "Token required"}), 400
    
    user = db_module.get_user_by_confirmation_token(token)
    if not user:
        return jsonify({"error": "Invalid or expired token"}), 400
    
    if user['verified']:
        return jsonify({"message": "User already verified"}), 200
    
    success = db_module.update_user_verified(user['id'], True)
    if success:
        return jsonify({"message": "User verified successfully"}), 200
    else:
        return jsonify({"error": "Verification failed"}), 500


@app.route("/user/<int:user_id>/preferences", methods=["PUT"])
def update_preferences(user_id):
    data = request.get_json(silent=True)
    if not data or "labels" not in data:
        return jsonify({"error": "Labels list required"}), 400
    
    labels = data.get("labels")
    if not isinstance(labels, list):
        return jsonify({"error": "Labels must be a list of integers"}), 400
        
    try:
        success = db_module.update_user_preferences(user_id, labels)
        if success:
            return jsonify({"message": "Preferences updated"}), 200
        else:
            return jsonify({"error": "User not found or update failed"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/goods", methods=["POST"])
def create_good():
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Extract fields
    name = data.get("name")
    seller_id = data.get("seller_id")
    num = data.get("num")
    value = data.get("value")
    description = data.get("description")
    labels = data.get("labels") # List of ints

    # Handle form data types (everything is string in form)
    if request.form:
        try:
            if seller_id: seller_id = int(seller_id)
            if num: num = int(num)
            if value: value = float(value)
            # labels might be tricky from a simple form, maybe skip or parse comma separated
            if labels and isinstance(labels, str):
                # assume comma separated for form
                labels = [int(x.strip()) for x in labels.split(",") if x.strip()]
        except ValueError:
            return jsonify({"error": "Invalid data types"}), 400

    if not all([name, seller_id, num is not None, value is not None]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        good = db_module.create_good(name, seller_id, num, value, description, labels=labels)
        
        # Notify interested users
        if labels:
            def send_prefer_notifications():
                try:
                    interested_users = db_module.get_users_interested_in(labels)
                    for user in interested_users:
                        if user.get('email'):
                            html = mailer.render_template(
                                'new_arrival.html',
                                user_name=user.get('name'),
                                product_name=name,
                                product_price=value,
                                product_description=description,
                                product_url=f"http://localhost:5173/goods/{good['id']}", # Assuming frontend URL
                                app_name='我们的应用',
                                current_year=2025
                            )
                            mailer.send_email(
                                to_email=user.get('email'),
                                subject=f"新品上架通知：{name}",
                                content=f"新品 {name} 上架了，快来看看！",
                                html=html
                            )
                except Exception as e:
                    print(f"Failed to send notifications: {e}")
            
            threading.Thread(target=send_prefer_notifications).start()
                
        return jsonify(good), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/goods/random", methods=["GET"])
def get_random_goods():
    num = request.args.get("num", default=10, type=int)
    goods = db_module.get_random_goods(num)
    return jsonify(goods)


@app.route("/goods/<int:good_id>", methods=["GET"])
def get_good(good_id):
    good = db_module.get_good(good_id)
    if not good:
        return jsonify({"error": "Good not found"}), 404
    return jsonify(good)


@app.route("/goods/<int:good_id>/status", methods=["PUT"])
def update_good_status(good_id):
    data = request.json
    status = data.get("status")
    if not status:
        return jsonify({"error": "Status required"}), 400
    try:
        success = db_module.update_good_status(good_id, status)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Update failed"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or request.form
    buyer_id = data.get("buyer_id")
    goods_id = data.get("goods_id")
    num = data.get("num")

    if request.form:
        try:
            if buyer_id: buyer_id = int(buyer_id)
            if goods_id: goods_id = int(goods_id)
            if num: num = int(num)
        except ValueError:
            return jsonify({"error": "Invalid data types"}), 400
    
    if not all([buyer_id, goods_id, num]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        order = db_module.create_order(buyer_id, goods_id, num)
        return jsonify(order), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = db_module.get_order(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order)


@app.route("/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    data = request.json
    status = data.get("status")
    if not status:
        return jsonify({"error": "Status required"}), 400
    try:
        success = db_module.update_order_status(order_id, status)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Update failed"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    # Ensure DB exists for quick local dev
    try:
        db_module.init_db()
    except Exception:
        pass
    app.run(debug=True)