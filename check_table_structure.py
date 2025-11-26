import sqlite3
import os

# 连接到数据库
db_path = 'finance_manager.db'
if not os.path.exists(db_path):
    print(f"数据库文件 {db_path} 不存在")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询users表结构
cursor.execute("PRAGMA table_info(users)")
users_columns = cursor.fetchall()

print("Users表结构:")
print("cid | name | type | notnull | dflt_value | pk")
print("-" * 50)
for column in users_columns:
    print(f"{column[0]} | {column[1]} | {column[2]} | {column[3]} | {column[4]} | {column[5]}")

# 查询accounts表结构
cursor.execute("PRAGMA table_info(accounts)")
accounts_columns = cursor.fetchall()

print("\nAccounts表结构:")
print("cid | name | type | notnull | dflt_value | pk")
print("-" * 50)
for column in accounts_columns:
    print(f"{column[0]} | {column[1]} | {column[2]} | {column[3]} | {column[4]} | {column[5]}")

# 查询categories表结构
cursor.execute("PRAGMA table_info(categories)")
categories_columns = cursor.fetchall()

print("\nCategories表结构:")
print("cid | name | type | notnull | dflt_value | pk")
print("-" * 50)
for column in categories_columns:
    print(f"{column[0]} | {column[1]} | {column[2]} | {column[3]} | {column[4]} | {column[5]}")

# 关闭连接
conn.close()