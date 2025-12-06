import sqlite3
import os

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'data', 'finance_system.db')

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询users表中的所有数据
cursor.execute("SELECT * FROM users;")
users = cursor.fetchall()
print("Users Data:")
print("ID | Username | Password | Fullname | Email | Role | Status | Created At")
print("-" * 80)
for user in users:
    print(f"{user[0]} | {user[1]} | {user[2]} | {user[3]} | {user[4]} | {user[5]} | {user[6]} | {user[7]}")

# 关闭连接
conn.close()