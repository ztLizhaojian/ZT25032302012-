import sqlite3
import os

def inspect_db():
    """检查数据库内容"""
    # 构建数据库路径
    db_path = os.path.join(os.path.dirname(__file__), 'src', 'data', 'finance_system.db')
    print(f"数据库路径: {db_path}")
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在!")
        return
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查询所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\n数据库中的表:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 查询用户表结构
    cursor.execute("PRAGMA table_info(users);")
    columns = cursor.fetchall()
    print(f"\nusers表结构:")
    for column in columns:
        print(f"  - {column[1]} ({column[2]})")
    
    # 查询用户数据
    cursor.execute("SELECT id, username, password, fullname, email, role FROM users;")
    users = cursor.fetchall()
    print(f"\n用户数据:")
    for user in users:
        user_id, username, password, fullname, email, role = user
        print(f"  ID: {user_id}, 用户名: {username}, 密码: {password}, 全名: {fullname}, 邮箱: {email}, 角色: {role}")
    
    # 查询transactions表结构
    cursor.execute("PRAGMA table_info(transactions);")
    columns = cursor.fetchall()
    print(f"\ntransactions表结构:")
    for column in columns:
        print(f"  - {column[1]} ({column[2]})")
    
    # 查询transactions表记录数量
    cursor.execute("SELECT COUNT(*) FROM transactions;")
    count = cursor.fetchone()[0]
    print(f"\ntransactions表记录数量: {count}")
    
    # 关闭连接
    conn.close()

if __name__ == "__main__":
    inspect_db()