#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
填充示例数据到数据库
"""

import sqlite3
import os
from datetime import datetime, timedelta

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'finance_system.db')

def populate_sample_data():
    """填充示例数据"""
    print("开始填充示例数据...")
    
    # 检查数据库文件是否存在
    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在: {DB_PATH}")
        return
    
    print(f"数据库文件路径: {DB_PATH}")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查是否已有交易数据
        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print("数据库中已有交易数据，跳过填充")
            conn.close()
            return
        
        # 插入示例交易数据
        sample_transactions = [
            # 收入交易
            ('收入', 5000.00, 1, 1, '2025-11-01', '销售收入', 'INV-001', '银行转账', 1),
            ('收入', 3000.00, 2, 1, '2025-11-05', '服务费收入', 'INV-002', '现金', 1),
            ('收入', 2000.00, 1, 3, '2025-11-10', '投资收益', 'INV-003', '银行转账', 1),
            ('收入', 1500.00, 2, 2, '2025-11-15', '其他业务收入', 'INV-004', '支付宝', 1),
            ('收入', 4000.00, 1, 1, '2025-11-20', '销售收入', 'INV-005', '银行转账', 1),
            
            # 支出交易
            ('支出', 2000.00, 1, 4, '2025-11-02', '采购原材料', 'EXP-001', '银行转账', 1),
            ('支出', 1500.00, 2, 6, '2025-11-08', '办公用品采购', 'EXP-002', '现金', 1),
            ('支出', 3000.00, 1, 5, '2025-11-12', '员工工资', 'EXP-003', '银行转账', 1),
            ('支出', 800.00, 2, 7, '2025-11-18', '水电费', 'EXP-004', '支付宝', 1),
            ('支出', 1200.00, 1, 8, '2025-11-25', '差旅费', 'EXP-005', '银行转账', 1),
            
            # 更多交易数据
            ('收入', 6000.00, 1, 1, '2025-12-01', '销售收入', 'INV-006', '银行转账', 1),
            ('支出', 2500.00, 2, 4, '2025-12-03', '设备采购', 'EXP-006', '银行转账', 1),
            ('收入', 3500.00, 1, 3, '2025-12-05', '投资收益', 'INV-007', '银行转账', 1),
            ('支出', 1000.00, 1, 6, '2025-12-10', '培训费用', 'EXP-007', '银行转账', 1),
            ('收入', 4500.00, 2, 2, '2025-12-15', '服务费收入', 'INV-008', '微信支付', 1),
        ]
        
        # 插入交易数据
        for transaction in sample_transactions:
            cursor.execute("""
                INSERT INTO transactions 
                (transaction_type, amount, account_id, category_id, transaction_date, 
                 description, receipt_number, payment_method, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, transaction)
        
        # 更新账户余额
        # 现金账户 (account_id=1)
        cursor.execute("""
            UPDATE accounts 
            SET balance = (
                SELECT COALESCE(SUM(CASE WHEN transaction_type = '收入' THEN amount ELSE -amount END), 0)
                FROM transactions 
                WHERE account_id = 1
            ),
            updated_at = ?
            WHERE id = 1
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        
        # 银行存款账户 (account_id=2)
        cursor.execute("""
            UPDATE accounts 
            SET balance = (
                SELECT COALESCE(SUM(CASE WHEN transaction_type = '收入' THEN amount ELSE -amount END), 0)
                FROM transactions 
                WHERE account_id = 2
            ),
            updated_at = ?
            WHERE id = 2
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        
        # 提交事务
        conn.commit()
        print(f"成功插入 {len(sample_transactions)} 条示例交易记录")
        
        # 显示更新后的账户余额
        cursor.execute("SELECT id, name, balance FROM accounts")
        accounts = cursor.fetchall()
        print("\n更新后的账户余额:")
        for account in accounts:
            print(f"  {account[1]}: ¥{account[2]:.2f}")
        
        conn.close()
        print("\n示例数据填充完成!")
        
    except Exception as e:
        print(f"填充示例数据时出错: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    populate_sample_data()