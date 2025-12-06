import sqlite3
import os
import hashlib

def hash_password(password):
    """哈希密码（简单实现，实际应使用更安全的哈希算法）"""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_admin_user():
    print("=====================================")
    print("🔧 设置唯一的admin用户账号")
    print("=====================================")
    
    # 检查所有可能的数据库路径
    db_paths = [
        os.path.join(os.getcwd(), "src", "data", "finance_system.db"),
        os.path.join(os.getcwd(), "data", "finance_system.db"),
        os.path.join(os.getcwd(), "finance_system.db")
    ]
    
    # 确保admin用户信息
    admin_username = "admin"
    admin_password = "admin123"
    admin_password_hash = hash_password(admin_password)
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\n📊 处理数据库: {db_path}")
            try:
                # 连接数据库
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 检查users表是否存在
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    print("✅ users表存在")
                    
                    # 先查询是否已存在admin用户
                    cursor.execute("SELECT id FROM users WHERE username=?", (admin_username,))
                    existing_admin = cursor.fetchone()
                    
                    if existing_admin:
                        # 更新admin用户
                        print(f"🔄 更新admin用户密码和状态")
                        update_sql = """
                        UPDATE users 
                        SET password=?, role='admin', status='active' 
                        WHERE username=?
                        """
                        cursor.execute(update_sql, (admin_password_hash, admin_username))
                        conn.commit()
                        print(f"✅ 成功更新admin用户，影响行数: {cursor.rowcount}")
                    else:
                        # 插入新的admin用户
                        print(f"➕ 插入新的admin用户")
                        insert_sql = """
                        INSERT INTO users (username, password, fullname, email, role, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                        """
                        cursor.execute(insert_sql, (
                            admin_username,
                            admin_password_hash,
                            "系统管理员",
                            "admin@example.com",
                            "admin",
                            "active"
                        ))
                        conn.commit()
                        print(f"✅ 成功创建admin用户，ID: {cursor.lastrowid}")
                    
                    # 确保只有admin用户处于active状态
                    print("🔒 设置只有admin用户可登录")
                    disable_sql = """
                    UPDATE users 
                    SET status='inactive' 
                    WHERE username!=?
                    """
                    cursor.execute(disable_sql, (admin_username,))
                    conn.commit()
                    print(f"✅ 已禁用其他用户，影响行数: {cursor.rowcount}")
                    
                    # 验证结果
                    print("\n📋 验证设置结果:")
                    cursor.execute("SELECT username, role, status FROM users WHERE status='active'")
                    active_users = cursor.fetchall()
                    
                    if active_users:
                        print(f"活跃用户列表 ({len(active_users)}):")
                        for user in active_users:
                            print(f"  - 用户名: {user[0]}, 角色: {user[1]}, 状态: {user[2]}")
                    else:
                        print("警告: 没有活跃用户")
                    
                else:
                    print("❌ users表不存在")
                    
                conn.close()
            except Exception as e:
                print(f"❌ 数据库操作错误: {e}")
        else:
            print(f"⚠️  数据库不存在: {db_path}")
    
    print("\n=====================================")
    print("设置完成！")
    print(f"现在只有账号: {admin_username}, 密码: {admin_password} 可以登录系统")
    print("请重启应用程序以应用更改")
    print("=====================================")

if __name__ == "__main__":
    setup_admin_user()