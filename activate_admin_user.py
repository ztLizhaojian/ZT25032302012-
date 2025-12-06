import sqlite3
import os
from datetime import datetime

def activate_admin_user():
    """激活admin用户并设置管理员权限"""
    print("开始激活admin用户...")
    db_path = os.path.join('src', 'data', 'finance_system.db')
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在 - {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 首先检查表结构
        print("\n检查表结构...")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("Users表列信息:")
        column_names = [col[1].lower() for col in columns]  # 转换为小写以便比较
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
        
        # 查询所有用户
        print("\n查询所有用户信息:")
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        if users:
            print(f"找到 {len(users)} 个用户")
            for user in users:
                print(f"用户数据: {user}")
        else:
            print("未找到用户数据")
        
        # 查找admin用户
        print("\n查找admin用户...")
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            print(f"找到admin用户: {admin_user}")
            user_id = admin_user[0]
            
            # 根据表结构更新 - 尝试多种可能的字段名
            update_fields = []
            update_values = []
            
            # 检查激活相关字段 - 尝试多种可能的字段名
            activation_fields = ['is_active', 'active', 'status', 'is_activated', 'activated', 'enabled', 'active_status']
            for field in activation_fields:
                if field in column_names:
                    update_fields.append(f'{field} = ?')
                    # 根据字段类型使用合适的值
                    if field == 'status':
                        update_values.append('active')  # 文本类型
                    else:
                        update_values.append(1)  # 数值类型
                    print(f"将更新激活字段: {field}")
            
            # 检查管理员权限字段
            admin_fields = ['role', 'is_admin', 'admin', 'permission_level', 'access_level']
            for field in admin_fields:
                if field in column_names:
                    update_fields.append(f'{field} = ?')
                    if field == 'role':
                        update_values.append('admin')  # 文本类型
                    else:
                        update_values.append(1)  # 数值类型
                    print(f"将更新管理员字段: {field}")
            
            # 添加用户ID到参数列表
            update_values.append(user_id)
            
            if update_fields:
                update_sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
                print(f"执行更新: {update_sql}")
                print(f"参数: {update_values}")
                cursor.execute(update_sql, update_values)
                conn.commit()
                print(f"成功更新admin用户")
            else:
                print("未找到可用于激活或设置管理员权限的字段")
            
            # 执行一个额外的直接更新，强制将status设为active（无论是否已存在）
            print("\n执行强制更新status字段为'active'")
            try:
                cursor.execute("UPDATE users SET status = 'active' WHERE username = 'admin'")
                conn.commit()
                print("强制更新status字段成功")
            except Exception as e:
                print(f"强制更新status字段失败: {e}")
                
            # 再次尝试更新active字段（如果存在）
            print("\n执行强制更新active字段为1")
            try:
                cursor.execute("UPDATE users SET active = 1 WHERE username = 'admin'")
                conn.commit()
                print("强制更新active字段成功")
            except Exception as e:
                print(f"强制更新active字段失败: {e}")
                
            # 验证更新
            print("\n验证更新后的admin用户:")
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            updated_admin = cursor.fetchone()
            if updated_admin:
                print(f"更新后的admin用户: {updated_admin}")
                # 显示每个字段的值，方便调试
                for i, col in enumerate(columns):
                    print(f"  {col[1]}: {updated_admin[i]}")
            
            return True
        else:
            print("admin用户不存在，尝试创建...")
            # 尝试创建admin用户
            admin_password = 'admin123'  # 示例密码
            
            # 构建INSERT语句
            insert_fields = ['username', 'password']
            insert_values = ['admin', admin_password]
            
            if 'fullname' in column_names:
                insert_fields.append('fullname')
                insert_values.append('系统管理员')
            if 'email' in column_names:
                insert_fields.append('email')
                insert_values.append('admin@example.com')
            if 'status' in column_names:
                insert_fields.append('status')
                insert_values.append('active')
            if 'active' in column_names or 'is_active' in column_names:
                field_name = 'active' if 'active' in column_names else 'is_active'
                insert_fields.append(field_name)
                insert_values.append(1)
            if 'role' in column_names:
                insert_fields.append('role')
                insert_values.append('admin')
            if 'is_admin' in column_names:
                insert_fields.append('is_admin')
                insert_values.append(1)
            if 'created_at' in column_names:
                insert_fields.append('created_at')
                insert_values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            try:
                placeholders = ['?'] * len(insert_fields)
                insert_sql = f"INSERT INTO users ({', '.join(insert_fields)}) VALUES ({', '.join(placeholders)})"
                print(f"执行插入: {insert_sql}")
                print(f"参数: {insert_values}")
                cursor.execute(insert_sql, insert_values)
                conn.commit()
                print("成功创建admin用户")
                return True
            except Exception as e:
                print(f"创建admin用户失败: {e}")
                return False
            
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = activate_admin_user()
    if success:
        print("激活admin用户完成!")
    else:
        print("激活admin用户失败!")