import os

# ==============================================================================
# 【系统发件人配置】(必须配置，否则无法发送验证邮件)
# 请去 QQ 邮箱 (或其他服务商) 获取 SMTP 授权码
# ==============================================================================
os.environ["SMTP_HOST"] = "smtp.qq.com"        # SMTP 服务器地址
os.environ["SMTP_PORT"] = "465"                # SSL 端口
os.environ["SMTP_USER"] = "12345678@qq.com"    # 【请替换】你的发件人邮箱账号
os.environ["SMTP_PASS"] = "abcdefghijklmn"     # 【请替换】你的邮箱授权码
os.environ["SMTP_SENDER"] = "泥邮工具人 <12345678@qq.com>" # 发件人显示名称
# ==============================================================================

from flask import Flask, jsonify, request
from flask_cors import CORS
import db as db_module
import bcrypt
import secrets
import mailer
import threading

app = Flask(__name__)
# 允许跨域请求
CORS(app)

APP_NAME = "泥邮工具人"
BACKEND_URL = "http://localhost:5000"
FRONTEND_URL = "http://localhost:5173"

@app.route("/")
def hello():
    """根路由，测试后端是否存活"""
    return jsonify({"message": "Backend is running!"})


@app.route("/labels", methods=["GET"])
def get_labels():
    """获取所有标签"""
    return jsonify(db_module.get_all_labels())


@app.route("/user/register", methods=["POST"])
def create_user():
    """
    用户注册接口
    1. 接收数据 -> 2. 加密密码 -> 3. 生成Token -> 4. 存库 -> 5. 异步发邮件
    """
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

    # 密码加密
    pswd_hash = bcrypt.hashpw(pswd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    # 生成验证 Token
    confirmation_token = secrets.token_urlsafe(32)

    try:
        # 写入数据库，默认为未验证状态
        user = db_module.create_user(name, email, pswd_hash, verified=False, confirmation_token=confirmation_token)
        
        # 生成验证链接
        confirmation_url = f"{FRONTEND_URL}/confirm?token={confirmation_token}"
        
        # 渲染邮件模板
        html = mailer.render_template(
            'register.html',
            user_name=name,
            confirmation_url=confirmation_url,
            app_name=APP_NAME,
            support_email='support@example.com',
            current_year=2025
        )
        
        # 定义异步发送任务
        def send_async_email():
            try:
                mailer.send_email(
                    to_email=email,
                    to_name=name,
                    subject="完成注册 - 泥邮工具人",
                    content="请点击链接完成注册。",
                    html=html
                )
            except Exception as e:
                print(f"邮件发送失败: {e}")

        # 启动线程发送邮件
        threading.Thread(target=send_async_email).start()
        
        return jsonify({"message": "User created, confirmation email sent", "user_id": user['id']}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/user/login", methods=["POST"])
def login():
    """
    用户登录接口 (新增)
    验证账号密码，成功则返回用户信息
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data"}), 400
    
    # 兼容 studentId 或 email 登录
    identifier = data.get("studentId") or data.get("email")
    password = data.get("password")

    if not identifier or not password:
        return jsonify({"error": "请输入账号和密码"}), 400

    try:
        conn = db_module._get_conn()
        # 在数据库查找用户
        user = conn.execute("SELECT * FROM users WHERE name = ? OR email = ?", (identifier, identifier)).fetchone()
        conn.close()

        if user:
            # 获取数据库中的 Hash 密码
            stored_hash = user['pswd_hash']
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            
            # 验证密码
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                # 登录成功，返回数据
                return jsonify({
                    "message": "Login successful",
                    "user": {
                        "id": user['id'],
                        "name": user['name'],
                        "email": user['email'],
                        "avatar": f"https://picsum.photos/seed/{user['id']}/150/150", # 模拟头像
                        "balance": 0.00,
                        "creditScore": 100
                    }
                })
        
        return jsonify({"error": "账号或密码错误"}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Server error"}), 500


@app.route("/user/confirm", methods=["GET"])
def confirm_user():
    """
    邮箱验证回调接口
    """
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
    """
    更新用户偏好标签
    """
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
    """
    发布商品接口 (已修复数据类型转换问题)
    """
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # 1. 安全地提取并转换数据
    try:
        name = data.get("name")
        description = data.get("description")
        
        # 强制转换为正确类型，防止数据库报错
        seller_id = int(data.get("seller_id"))
        num = int(data.get("num", 1))
        value = float(data.get("value"))
        
        # 处理 labels
        labels_raw = data.get("labels")
        labels = []
        if isinstance(labels_raw, str) and labels_raw.strip():
            # "1, 2, 3" -> [1, 2, 3]
            labels = [int(x.strip()) for x in labels_raw.split(",") if x.strip().isdigit()]
        elif isinstance(labels_raw, list):
            # [1, 2, "3"] -> [1, 2, 3]
            labels = [int(x) for x in labels_raw if str(x).isdigit()]

    except (ValueError, TypeError) as e:
        print(f"数据类型转换错误: {e}")
        return jsonify({"error": f"Invalid data types: {str(e)}"}), 400

    if not name:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # 2. 写入数据库
        good = db_module.create_good(name, seller_id, num, value, description, labels=labels)
        
        # 3. 异步发送通知邮件给感兴趣的用户
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
                                product_url=f"{FRONTEND_URL}/goods/{good['id']}", 
                                app_name=APP_NAME,
                                current_year=2025
                            )
                            mailer.send_email(
                                to_email=user.get('email'),
                                to_name=user.get('name'),
                                subject=f"新品上架通知：{name}",
                                content=f"新品 {name} 上架了，快来看看！",
                                html=html
                            )
                except Exception as e:
                    print(f"Failed to send notifications: {e}")
            
            threading.Thread(target=send_prefer_notifications).start()
                
        return jsonify(good), 201
    except Exception as e:
        print(f"创建商品数据库错误: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/goods/random", methods=["GET"])
def get_random_goods():
    """获取随机商品"""
    try:
        num = request.args.get("num", default=10, type=int)
        goods = db_module.get_random_goods(num)
        return jsonify(goods)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/goods/<int:good_id>", methods=["GET"])
def get_good(good_id):
    """获取单个商品详情"""
    good = db_module.get_good(good_id)
    if not good:
        return jsonify({"error": "Good not found"}), 404
    return jsonify(good)


@app.route("/goods/<int:good_id>/status", methods=["PUT"])
def update_good_status(good_id):
    """修改商品状态 (available/sold/removed)"""
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
    """创建订单"""
    data = request.get_json(silent=True) or request.form
    
    # 获取参数并尝试转换
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
    """获取订单详情"""
    order = db_module.get_order(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order)


@app.route("/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    """修改订单状态"""
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
    try:
        # 启动时自动初始化数据库表结构
        db_module.init_db()
    except Exception:
        pass
    # 启动 Flask
    app.run(debug=True, host="0.0.0.0", port=5000)