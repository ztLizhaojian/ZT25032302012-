import sqlite3
import os
import json

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'data', 'finance_system.db')

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询users表中的所有数据
cursor.execute("SELECT * FROM users;")
users = cursor.fetchall()

# 将结果写入文件
with open('users_data.txt', 'w', encoding='utf-8') as f:
    f.write("Users Data:\n")
    f.write("ID | Username | Password | Fullname | Email | Role | Status | Created At\n")
    f.write("-" * 80 + "\n")
    for user in users:
        f.write(f"{user[0]} | {user[1]} | {user[2]} | {user[3]} | {user[4]} | {user[5]} | {user[6]} | {user[7]}\n")

print("用户数据已导出到 users_data.txt 文件")

# 关闭连接
conn.close()