#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试利润查询修复是否有效
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入数据库操作
from src.database.db_manager import execute_query

# 测试利润查询
def test_profit_query():
    """测试利润查询修复是否有效"""
    print("开始测试利润查询...")
    
    start_date = '2025-12-01'
    end_date = '2025-12-04'
    
    try:
        profit_data = execute_query(
            """
            WITH date_range AS (
                SELECT date(transaction_date) as day, transaction_type, amount
                FROM transactions
                WHERE transaction_date BETWEEN ? AND ?
            )
            SELECT 
                strftime('%Y-%W', day) as week,
                SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expense,
                SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE -amount END) as profit
            FROM date_range
            GROUP BY week
            ORDER BY week
            """,
            (start_date, end_date),
            fetch_all=True
        )
        
        print(f"查询结果类型: {type(profit_data)}")
        print(f"查询结果: {profit_data}")
        
        if isinstance(profit_data, list):
            print("✓ 修复成功！利润查询现在返回列表类型")
            if profit_data:
                print(f"  返回的记录数: {len(profit_data)}")
                print(f"  第一条记录: {profit_data[0]}")
                print(f"  记录类型: {type(profit_data[0])}")
        else:
            print(f"✗ 修复失败！利润查询返回了 {type(profit_data)} 类型")
            
    except Exception as e:
        print(f"✗ 查询执行失败: {e}")

if __name__ == "__main__":
    test_profit_query()
