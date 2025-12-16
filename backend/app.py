from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import db as db_module
import bcrypt
import secrets
import mailer
import threading
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
# 允许跨域请求
CORS(app)

# 配置静态文件服务
app.static_folder = os.path.join(os.path.dirname(__file__), '..', 'media')
app.static_url_path = '/media'

APP_NAME = "泥邮工具人"
BACKEND_URL = "http://localhost:5000"
FRONTEND_URL = "http://localhost:5173"
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    # print(f"name:{name},")
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
            mailer.send_email(
                to_email=email,
                to_name=name,
                subject="完成注册 - 泥邮工具人",
                content="请点击链接完成注册。",
                html=html
            )

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
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"error": "No data"}), 400
    
    identifier = data.get("username")
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
                # 在允许登录前，检查邮箱是否已验证
                try:
                    verified = user['verified']
                except Exception:
                    # 如果 Row 不支持直接索引（极少见），尝试通过 get
                    try:
                        verified = user.get('verified')
                    except Exception:
                        verified = None

                # 归一化可能的字符串/数字表示
                if isinstance(verified, str):
                    if verified.isdigit():
                        verified = int(verified)
                    else:
                        verified = verified.lower() in ("true", "1", "yes")

                if not verified:
                    return jsonify({"error": "请先验证邮箱后再登录"}), 403

                # 登录成功，返回数据
                return jsonify({
                    "message": "Login successful",
                    "user": {
                        "id": user['id'],
                        "name": user['name'],
                        "email": user['email'],
                        "avatar": f"https://picsum.photos/seed/{user['id']}/150/150",
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
    
@app.route("/user/<int:user_id>")
def get_user_info(user_id):
    """获取用户信息"""
    user = db_module.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # 移除敏感信息
    user.pop("pswd_hash", None)
    user.pop("confirmation_token", None)
    
    # 添加头像链接
    user["avatar"] = f"https://picsum.photos/seed/{user['id']}/150/150"
    user["balance"] = 0.00
    user["creditScore"] = 100
    
    return jsonify(user)


@app.route("/user/<int:user_id>/goods")
def get_user_goods(user_id):
    """获取用户发布的商品"""
    goods = db_module.get_goods_by_seller(user_id, True)
    return jsonify(goods)


@app.route("/user/<int:user_id>/orders")
def get_user_orders(user_id):
    """获取用户的订单（作为买家）"""
    orders = db_module.get_orders_by_buyer(user_id)
    # 丰富订单信息，加入商品详情
    for order in orders:
        good = db_module.get_good(order['goods_id'])
        if good:
            order['good_name'] = good['name']
            order['good_value'] = good['value']
            order['good_description'] = good['description']
    return jsonify(orders)


@app.route("/orders/mine", methods=["GET"])
def get_my_orders():
    """获取当前用户的订单"""
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "User ID required"}), 401
    
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid User ID"}), 400

    orders = db_module.get_orders_by_buyer(user_id)
    # 丰富订单信息，加入商品详情
    for order in orders:
        good = db_module.get_good(order['goods_id'])
        if good:
            order['good_name'] = good['name']
            order['good_value'] = good['value']
            order['good_description'] = good['description']
            # 尝试获取一张图片
            good_dir = os.path.join(UPLOAD_FOLDER, f"good_{good['id']}")
            if os.path.exists(good_dir):
                for file in os.listdir(good_dir):
                    if file.startswith(f"good_{good['id']}_") and file.split('.')[-1].lower() in ALLOWED_EXTENSIONS:
                        order['good_image'] = f"/media/good_{good['id']}/{file}"
                        break
            if 'good_image' not in order:
                 order['good_image'] = ""

    return jsonify(orders)


@app.route("/good/<int:good_id>/orders")
def get_good_orders(good_id):
    """获取某商品的订单（供卖家查看）"""
    orders = db_module.get_orders_by_good(good_id)
    # 丰富订单信息，加入买家详情
    for order in orders:
        buyer = db_module.get_user(order['buyer_id'])
        if buyer:
            order['buyer_name'] = buyer['name']
            order['buyer_email'] = buyer['email']
    return jsonify(orders)

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
        is_task = bool(data.get("is_task"))
        
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
        good = db_module.create_good(name, seller_id, num, value, description, labels=labels, type=is_task)
        
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
        is_task = request.args.get("is_task", "false").lower() == "true"
        goods = db_module.get_random_goods(num, is_task)
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


@app.route("/goods/<int:good_id>/update", methods=["POST"])
def update_good_and_create_order(good_id):
    """
    更新商品状态并创建订单 (原子操作)
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No data"}), 400
    
    status = data.get("status")
    buyer_id = data.get("buyer_id")
    
    if status == "sold":
        if not buyer_id:
             return jsonify({"error": "Buyer ID required for purchase"}), 400
        
        conn = db_module._get_conn()
        try:
            # 1. Check if good is available
            good_row = conn.execute("SELECT * FROM goods WHERE id = ?", (good_id,)).fetchone()
            if not good_row:
                conn.close()
                return jsonify({"error": "Good not found"}), 404
            if good_row['status'] != 'available':
                conn.close()
                return jsonify({"error": "Good is not available"}), 400
                
            # 2. Update status and create order in transaction
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("UPDATE goods SET status = ? WHERE id = ?", ("sold", good_id))
            conn.execute("INSERT INTO orders (goods_id, num, buyer_id, status) VALUES (?, ?, ?, ?)", (good_id, 1, buyer_id, "processing"))
            conn.commit()
            conn.close()
            
            return jsonify({"message": "Purchase successful"}), 200
        except Exception as e:
            try:
                conn.rollback()
            except:
                pass
            conn.close()
            return jsonify({"error": f"Purchase failed: {str(e)}"}), 500
             
    return jsonify({"error": "Invalid status or action"}), 400


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


@app.route("/upload", methods=["POST"])
def upload_media():
    """
    上传图片/视频接口
    参数:
    - type: 'avatar' | 'good'
    - id: user_id | good_id
    - files: 文件列表
    """
    if 'files' not in request.files:
        return jsonify({"error": "No files part"}), 400
    
    files = request.files.getlist('files')
    upload_type = request.form.get('type')
    target_id = request.form.get('id')

    if not files or not files[0].filename:
        return jsonify({"error": "No selected file"}), 400
    if not upload_type or not target_id:
        return jsonify({"error": "Missing type or id"}), 400
    
    try:
        target_id = int(target_id)
    except ValueError:
        return jsonify({"error": "Invalid id"}), 400

    saved_files = []

    if upload_type == 'avatar':
        if len(files) > 1:
            return jsonify({"error": "Avatar limit is 1"}), 400
        
        file = files[0]
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"avatar_{target_id}.{ext}"
            # 删除旧头像
            for old_ext in ALLOWED_EXTENSIONS:
                old_path = os.path.join(UPLOAD_FOLDER+"/user", f"avatar_{target_id}.{old_ext}")
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            # 确保目录存在
            user_dir = os.path.join(UPLOAD_FOLDER, "user")
            os.makedirs(user_dir, exist_ok=True)
            
            file.save(os.path.join(user_dir, filename))
            saved_files.append(filename)
        else:
             return jsonify({"error": "Invalid file type"}), 400

    elif upload_type == 'good':
        if len(files) > 9:
            return jsonify({"error": "Goods media limit is 9"}), 400
        
        # 确保目录存在
        good_dir = os.path.join(UPLOAD_FOLDER, f"good_{target_id}")
        os.makedirs(good_dir, exist_ok=True)
        
        for i, file in enumerate(files):
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"good_{target_id}_{i}.{ext}"
                file.save(os.path.join(good_dir, filename))
                saved_files.append(filename)
            else:
                return jsonify({"error": f"File {file.filename} invalid"}), 400
    else:
        return jsonify({"error": "Invalid upload type"}), 400

    return jsonify({"message": "Upload successful"}), 201

@app.route("/user/<int:user_id>/avatar")
def get_user_avatar(user_id):
    """获取用户头像"""
    user_dir = os.path.join(UPLOAD_FOLDER, "user")
    for ext in ALLOWED_EXTENSIONS:
        path = os.path.join(user_dir, f"avatar_{user_id}.{ext}")
        if os.path.exists(path):
            return jsonify({"avatar_url": f"/media/user/avatar_{user_id}.{ext}"})
    return jsonify({"error": "Avatar not found"}), 404

@app.route('/media/<path:filename>')
def serve_media(filename):
    """Serve media files"""
    return send_from_directory(app.static_folder, filename)

@app.route("/good/<int:good_id>/images")
def get_good_images(good_id):
    """获取商品图像，支持选择第一个或全部"""
    good_dir = os.path.join(UPLOAD_FOLDER, f"good_{good_id}")
    if not os.path.exists(good_dir):
        return jsonify({"error": "No images found"}), 404
    
    first = request.args.get("first", "false").lower() == "true"
    images = []
    for file in os.listdir(good_dir):
        if file.startswith(f"good_{good_id}_") and file.split('.')[-1].lower() in ALLOWED_EXTENSIONS:
            images.append(f"/media/good_{good_id}/{file}")
    
    if not images:
        return jsonify({"error": "No images found"}), 404
    
    if first:
        return jsonify({"image_url": images[0]})
    else:
        return jsonify({"image_urls": images})


@app.route("/messages", methods=["POST"])
def send_message():
    """
    发送消息接口
    POST 数据: { "receiver_id": int, "text": string }
    """
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # 实际项目中应从 JWT token 或 session 中获取发送者ID
    # 这里为了演示，从 headers 中获取 X-User-ID
    sender_id_header = request.headers.get("X-User-ID")
    if not sender_id_header:
        return jsonify({"error": "Sender ID required in X-User-ID header"}), 400
    
    try:
        sender_id = int(sender_id_header)
    except ValueError:
        return jsonify({"error": "Invalid sender ID"}), 400
    
    try:
        receiver_id = int(data.get("receiver_id"))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid receiver_id"}), 400
    
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Message text cannot be empty"}), 400
    
    try:
        message = db_module.create_message(sender_id, receiver_id, text)
        return jsonify({
            "id": message['id'],
            "senderId": message['sender_id'],
            "receiverId": message['receiver_id'],
            "text": message['text'],
            "createdAt": message['created_at']
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/messages/<int:user_id>", methods=["GET"])
def get_messages_with_user(user_id):
    """
    获取与某个用户的所有消息
    需要在 X-User-ID header 中提供当前用户ID
    """
    current_user_id_header = request.headers.get("X-User-ID")
    if not current_user_id_header:
        return jsonify({"error": "Current user ID required in X-User-ID header"}), 400
    
    try:
        current_user_id = int(current_user_id_header)
    except ValueError:
        return jsonify({"error": "Invalid current user ID"}), 400
    
    try:
        messages = db_module.get_messages_between(current_user_id, user_id)
        return jsonify([{
            "id": m['id'],
            "senderId": m['sender_id'],
            "receiverId": m['receiver_id'],
            "text": m['text'],
            "createdAt": m['created_at']
        } for m in messages])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/messages/list", methods=["GET"])
def get_message_list():
    """
    获取当前用户的消息列表（最新对话列表）
    需要在 X-User-ID header 中提供当前用户ID
    """
    current_user_id_header = request.headers.get("X-User-ID")
    if not current_user_id_header:
        return jsonify({"error": "Current user ID required in X-User-ID header"}), 400
    
    try:
        current_user_id = int(current_user_id_header)
    except ValueError:
        return jsonify({"error": "Invalid current user ID"}), 400
    
    try:
        # 获取所有对话者的ID
        conn = db_module._get_conn()
        rows = conn.execute(
            "SELECT DISTINCT CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END as other_id FROM messages WHERE sender_id = ? OR receiver_id = ?",
            (current_user_id, current_user_id, current_user_id)
        ).fetchall()
        conn.close()
        
        result = []
        for row in rows:
            other_user_id = row['other_id']
            user = db_module.get_user(other_user_id)
            if user:
                # 移除敏感信息
                user.pop("pswd_hash", None)
                user.pop("confirmation_token", None)
                user["avatar"] = f"https://picsum.photos/seed/{user['id']}/150/150"
                result.append(user)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    try:
        # 启动时自动初始化数据库表结构
        db_module.init_db()
    except Exception:
        pass
    # 启动 Flask
    app.run(debug=True, host="0.0.0.0", port=5000)