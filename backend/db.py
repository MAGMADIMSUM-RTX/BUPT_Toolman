"""
数据库原子操作模块。
- 用户, 商品, 订单 : 创建，查询，修改(受限)
"""

import os
import sqlite3
import json
from typing import Optional, Dict, List

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "database.db")
LABELS_PATH = os.path.join(BASE_DIR, "labels.json")


def _get_conn() -> sqlite3.Connection:
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	conn.execute("PRAGMA foreign_keys = ON")
	return conn


def get_all_labels() -> List[Dict]:
	"""Load all available labels from the JSON file."""
	if not os.path.exists(LABELS_PATH):
		return []
	try:
		with open(LABELS_PATH, "r", encoding="utf-8") as f:
			return json.load(f)
	except Exception:
		return []


def init_db() -> None:
	"""Create tables if they do not exist."""
	conn = _get_conn()
	cur = conn.cursor()
	cur.executescript(
		"""
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL,
			email TEXT,
			pswd_hash TEXT,
			prefer TEXT NOT NULL DEFAULT '[]',
			verified BOOLEAN DEFAULT FALSE,
			confirmation_token TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);

		CREATE TABLE IF NOT EXISTS goods (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			seller_id INTEGER NOT NULL,
			type BOOLEAN DEFAULT FALSE,
			name TEXT NOT NULL,
			num INTEGER NOT NULL,
			sold_num INTEGER NOT NULL,
			labels TEXT NOT NULL DEFAULT '[]',
			value FLOAT NOT NULL,
			description TEXT,
			status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available','sold','removed')),
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY(seller_id) REFERENCES users(id)
		);

		CREATE TABLE IF NOT EXISTS orders (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			goods_id INTEGER NOT NULL,
			num INTEGER NOT NULL,
			buyer_id INTEGER NOT NULL,
			status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('processing','completed','cancelled')),
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY(goods_id) REFERENCES goods(id),
			FOREIGN KEY(buyer_id) REFERENCES users(id)
		);
		"""
	)
	conn.commit()
	conn.close()


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict]:
	if row is None:
		return None
	return {k: row[k] for k in row.keys()}


def _serialize_labels(labels: Optional[List[int]]) -> str:
	if labels is None:
		return json.dumps([])
	# ensure all are ints
	if not isinstance(labels, list) or not all(isinstance(i, int) for i in labels):
		raise ValueError("labels must be a list of integers")
	return json.dumps(labels)


def _deserialize_labels(s: Optional[str]) -> List[int]:
	if not s:
		return []
	try:
		obj = json.loads(s)
		if not isinstance(obj, list) or not all(isinstance(i, int) for i in obj):
			raise ValueError
		return obj
	except Exception:
		# if DB contains invalid data, return empty list rather than crash
		return []


def get_user(user_id: int) -> Optional[Dict]:
	conn = _get_conn()
	row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
	conn.close()
	data = _row_to_dict(row)
	if data is not None and "prefer" in data:
		data["prefer"] = _deserialize_labels(data.get("prefer"))
	return data


def get_goods_by_seller(seller_id: int, is_good: bool) -> List[Dict]:
	conn = _get_conn()
	type_filter = 0 if is_good else 1
	rows = conn.execute("SELECT * FROM goods WHERE seller_id = ? AND type = ?", (seller_id, type_filter)).fetchall()
	conn.close()
	results = []
	for row in rows:
		data = _row_to_dict(row)
		if data is not None:
			if "labels" in data:
				data["labels"] = _deserialize_labels(data.get("labels"))
			results.append(data)
	return results


def create_user(name: str, email: Optional[str] = None, pswd_hash: Optional[str] = None, verified: bool = False, confirmation_token: Optional[str] = None) -> Optional[Dict]:
	conn = _get_conn()
	cur = conn.cursor()
	cur.execute(
		"INSERT INTO users (name, email, pswd_hash, verified, confirmation_token) VALUES (?, ?, ?, ?, ?)",
		(name, email, pswd_hash, verified, confirmation_token),
	)
	conn.commit()
	user_id = cur.lastrowid
	row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
	conn.close()
	return _row_to_dict(row)


def create_good(name: str, seller_id: int,  num: int, value: float, description: str, status: str = "available", labels: Optional[List[int]] = None, type: bool = False) -> Optional[Dict]:
	"""Create a good. `labels` should be a list of ints (category/tag ids).
	Returns the created row as a dict.
	"""
	conn = _get_conn()
	cur = conn.cursor()
	labels_json = _serialize_labels(labels)
	cur.execute(
		"INSERT INTO goods (seller_id, name, num, sold_num, labels, value, description, status, type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
		(seller_id, name, num, 0, labels_json, value, description, status, type),
	)
	conn.commit()
	good_id = cur.lastrowid
	row = conn.execute("SELECT * FROM goods WHERE id = ?", (good_id,)).fetchone()
	conn.close()
	print(row)
	if row is None:
		return None
	data = _row_to_dict(row)
	if data is not None and "labels" in data:
		data["labels"] = _deserialize_labels(data.get("labels"))
	return data


def get_good(id: int) -> Optional[Dict]:
	conn = _get_conn()
	row = conn.execute("SELECT * FROM goods WHERE id = ?", (id,)).fetchone()
	conn.close()
	data = _row_to_dict(row)
	if data is not None and "labels" in data:
		data["labels"] = _deserialize_labels(data.get("labels"))
	return data


def get_random_goods(num: int, is_task: bool) -> List[Dict]:
	conn = _get_conn()
	type_filter = 1 if is_task else 0
	rows = conn.execute(
		"SELECT * FROM goods WHERE status = 'available' AND type = ? ORDER BY RANDOM() LIMIT ?", (type_filter, num)
	).fetchall()
	conn.close()
	results = []
	for row in rows:
		data = _row_to_dict(row)
		if data is not None:
			if "labels" in data:
				data["labels"] = _deserialize_labels(data.get("labels"))
			results.append(data)
	return results


def update_good_status(good_id: int, status: str) -> bool:
	ALLOWED = ("available", "sold", "removed")
	if status not in ALLOWED:
		raise ValueError(f"invalid good status: {status}")
	conn = _get_conn()
	cur = conn.cursor()
	cur.execute("UPDATE goods SET status = ? WHERE id = ?", (status, good_id))
	conn.commit()
	updated = cur.rowcount
	conn.close()
	return updated > 0

def create_order(buyer_id: int, goods_id: int, num: int, status: str = "pending") -> Optional[Dict]:
	"""Create an order. Returns the created order dict.
	Note: this function does not perform inventory checks or transactions —
	consider wrapping higher-level business logic to ensure consistency."""
	conn = _get_conn()
	cur = conn.cursor()
	cur.execute(
		"INSERT INTO orders (goods_id, num, buyer_id, status) VALUES (?, ?, ?, ?)",
		(goods_id, num, buyer_id, status),
	)
	conn.commit()
	order_id = cur.lastrowid
	row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
	conn.close()
	return _row_to_dict(row)
	
def get_order(order_id: int) -> Optional[Dict]:
	conn = _get_conn()
	row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
	conn.close()
	data = _row_to_dict(row)
	return data


def get_orders_by_buyer(buyer_id: int) -> List[Dict]:
	conn = _get_conn()
	rows = conn.execute("SELECT * FROM orders WHERE buyer_id = ?", (buyer_id,)).fetchall()
	conn.close()
	return [_row_to_dict(row) for row in rows]


def get_orders_by_good(goods_id: int) -> List[Dict]:
	conn = _get_conn()
	rows = conn.execute("SELECT * FROM orders WHERE goods_id = ?", (goods_id,)).fetchall()
	conn.close()
	return [_row_to_dict(row) for row in rows]


def update_order_status(order_id: int, status: str) -> bool:
	ALLOWED = ("pending", "processing", "completed", "cancelled")
	if status not in ALLOWED:
		raise ValueError(f"invalid order status: {status}")
	conn = _get_conn()
	cur = conn.cursor()
	cur.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
	conn.commit()
	updated = cur.rowcount
	conn.close()
	return updated > 0


def get_user_by_confirmation_token(token: str) -> Optional[Dict]:
	conn = _get_conn()
	row = conn.execute("SELECT * FROM users WHERE confirmation_token = ?", (token,)).fetchone()
	conn.close()
	return _row_to_dict(row)

def update_user_verified(user_id: int, verified: bool = True) -> bool:
	conn = _get_conn()
	cur = conn.cursor()
	cur.execute("UPDATE users SET verified = ?, confirmation_token = NULL WHERE id = ?", (verified, user_id))
	conn.commit()
	updated = cur.rowcount
	conn.close()
	return updated > 0

def update_user_preferences(user_id: int, labels: List[int]) -> bool:
	# Validate that all labels are allowed to be preferred
	all_labels = get_all_labels()
	allowed_ids = {l['id'] for l in all_labels if l.get('prefered', False)}
	
	if not set(labels).issubset(allowed_ids):
		raise ValueError("包含不可订阅的标签")

	conn = _get_conn()
	cur = conn.cursor()
	labels_json = _serialize_labels(labels)
	cur.execute("UPDATE users SET prefer = ? WHERE id = ?", (labels_json, user_id))
	conn.commit()
	updated = cur.rowcount
	conn.close()
	return updated > 0

def get_users_interested_in(tag_ids: List[int]) -> List[Dict]:
	"""
	Find users who have any of the given tag_ids in their preferences.
	Returns a list of user dicts.
	"""
	if not tag_ids:
		return []
	
	conn = _get_conn()
	# Get all users with non-empty preferences who are verified
	rows = conn.execute("SELECT * FROM users WHERE prefer != '[]' AND verified = 1").fetchall()
	conn.close()
	
	interested_users = []
	target_set = set(tag_ids)
	
	for row in rows:
		try:
			user_prefs_str = row['prefer']
			user_prefs = set(_deserialize_labels(user_prefs_str))
			# If intersection is not empty, user is interested
			if not user_prefs.isdisjoint(target_set):
				interested_users.append(_row_to_dict(row))
		except Exception:
			continue
			
	return interested_users
