#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码验证测试脚本
用于测试密码哈希和验证过程
"""

import sys
import os
import sqlite3

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.security import hash_password, verify_password
from src.database.db_manager import DB_PATH

def test_password_verification():
    """测试密码验证过程"""
    print("密码验证测试")
    print("=" * 50)
    
    # 从数据库中获取admin用户的密码哈希值
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 查询admin用户
            cursor.execute("SELECT password FROM users WHERE username = ?", ("admin",))
            result = cursor.fetchone()
            
            if result:
                stored_hash = result[0]
                print(f"数据库中存储的admin用户密码哈希值:")
                print(stored_hash)
                print()
                
                # 测试密码验证
                test_passwords = ["admin123", "Admin123", "admin", "wrongpassword"]
                
                for pwd in test_passwords:
                    # 使用security模块的verify_password函数
                    is_valid = verify_password(pwd, stored_hash)
                    print(f"密码 '{pwd}' 验证结果: {'✓' if is_valid else '✗'}")
                    
                    # 手动计算哈希值进行对比
                    manual_hash = hash_password(pwd)
                    print(f"  手动计算的哈希值: {manual_hash}")
                    print(f"  与存储值匹配: {'✓' if manual_hash == stored_hash else '✗'}")
                    print()
            else:
                print("未找到admin用户")
                
            conn.close()
        except Exception as e:
            print(f"数据库查询出错: {str(e)}")
    else:
        print("数据库文件不存在")

if __name__ == "__main__":
    test_password_verification()