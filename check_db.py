import sqlite3

# 连接到数据库
conn = sqlite3.connect('finance_manager.db')
cursor = conn.cursor()

# 获取users表结构
print("Users表结构:")
cursor.execute('PRAGMA table_info(users)')
cols = cursor.fetchall()
for col in cols:
    print(f"  {col[1]} ({col[2]})")

# 获取accounts表结构
print("\nAccounts表结构:")
cursor.execute('PRAGMA table_info(accounts)')
cols = cursor.fetchall()
for col in cols:
    print(f"  {col[1]} ({col[2]})")

# 关闭连接
conn.close()