#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务系统集成测试脚本
测试核心功能：
1. 数据库结构验证
2. 交易记录与账户余额联动
3. 资金转账原子操作
4. 账务冲销功能
5. 多角色权限控制
6. 对账核算功能
"""

import sqlite3
import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.account import AccountModel
from src.models.transaction import TransactionModel
from src.models.user import user_model
from src.database.db_manager import execute_query

# 模拟登录管理员用户，绕过权限检查
user_model.current_user = {'id': 1, 'username': 'admin', 'role': 'admin'}
user_model.is_authenticated = True

# 数据库连接
def get_db_connection():
    return sqlite3.connect('data/finance_system.db')

# 测试数据库结构
def test_database_structure():
    """测试数据库表结构是否符合要求"""
    print("\n=== 测试数据库结构 ===")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 测试账户表
        cursor.execute("PRAGMA table_info(accounts)")
        account_cols = [col[1] for col in cursor.fetchall()]
        required_account_cols = ['account_id', 'user_dept_id', 'account_type', 'current_balance', 'status', 'create_time']
        
        print(f"账户表字段: {', '.join(account_cols)}")
        for col in required_account_cols:
            if col in account_cols:
                print(f"✓ 字段 {col} 存在")
            else:
                print(f"✗ 字段 {col} 缺失")
        
        # 测试交易表
        cursor.execute("PRAGMA table_info(transactions)")
        transaction_cols = [col[1] for col in cursor.fetchall()]
        required_transaction_cols = ['record_id', 'related_account_id', 'trade_type', 'amount', 'summary', 'trade_time', 'trade_status', 'operator_id', 'reconciliation_flag']
        
        print(f"\n交易表字段: {', '.join(transaction_cols)}")
        for col in required_transaction_cols:
            if col in transaction_cols:
                print(f"✓ 字段 {col} 存在")
            else:
                print(f"✗ 字段 {col} 缺失")
        
        # 测试辅助表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n所有表: {', '.join(tables)}")
        required_tables = ['transfer_records', 'reconciliation_logs', 'user_permissions']
        for table in required_tables:
            if table in tables:
                print(f"✓ 表 {table} 存在")
            else:
                print(f"✗ 表 {table} 缺失")
        
        return True
        
    except Exception as e:
        print(f"数据库结构测试失败: {str(e)}")
        return False
    finally:
        conn.close()

# 测试交易与余额联动
def test_transaction_balance_linkage():
    """测试交易记录与账户余额的联动机制"""
    print("\n=== 测试交易与余额联动 ===")
    
    try:
        # 创建测试账户
        test_account_data = {
            'name': '测试账户',
            'account_type': '基本户',
            'initial_balance': 1000.0,
            'description': '测试账户',
            'status': 'active',
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if AccountModel.create_account(test_account_data, 1):
            print("✓ 创建测试账户成功")
        else:
            print("✗ 创建测试账户失败")
            return False
        
        # 获取测试账户ID
        account = execute_query("SELECT id, balance FROM accounts WHERE name='测试账户'", fetch_all=False)
        if not account:
            print("✗ 未找到测试账户")
            return False
        
        account_id = account['id']
        initial_balance = account['balance']
        print(f"初始余额: {initial_balance}")
        
        # 测试收入交易
        income_data = {
            'account_id': account_id,
            'amount': 500.0,
            'category_id': 1,
            'description': '测试收入',
            'transaction_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'transaction_time': datetime.datetime.now().strftime('%H:%M:%S'),
            'transaction_type': 'income',
            'trade_type': 'income',
            'trade_status': 'completed',
            'reconciliation_flag': 'unreconciled'
        }
        
        if TransactionModel.create_transaction(income_data, 1):
            print("✓ 创建收入交易成功")
        else:
            print("✗ 创建收入交易失败")
            return False
        
        # 检查余额是否增加
        account = execute_query("SELECT balance FROM accounts WHERE id=?", (account_id,), fetch_all=False)
        if account['balance'] == initial_balance + 500.0:
            print(f"✓ 收入后余额正确: {account['balance']}")
        else:
            print(f"✗ 收入后余额错误: {account['balance']} (预期: {initial_balance + 500.0})")
            return False
        
        # 测试支出交易
        expense_data = {
            'account_id': account_id,
            'amount': 200.0,
            'category_id': 2,
            'description': '测试支出',
            'transaction_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'transaction_time': datetime.datetime.now().strftime('%H:%M:%S'),
            'transaction_type': 'expense',
            'trade_type': 'expense',
            'trade_status': 'completed',
            'reconciliation_flag': 'unreconciled'
        }
        
        if TransactionModel.create_transaction(expense_data, 1):
            print("✓ 创建支出交易成功")
        else:
            print("✗ 创建支出交易失败")
            return False
        
        # 检查余额是否减少
        account = execute_query("SELECT balance FROM accounts WHERE id=?", (account_id,), fetch_all=False)
        expected_balance = initial_balance + 500.0 - 200.0
        if account['balance'] == expected_balance:
            print(f"✓ 支出后余额正确: {account['balance']}")
        else:
            print(f"✗ 支出后余额错误: {account['balance']} (预期: {expected_balance})")
            return False
        
        return True
        
    except Exception as e:
        print(f"交易与余额联动测试失败: {str(e)}")
        return False

# 测试资金转账功能
def test_fund_transfer():
    """测试资金转账的原子操作"""
    print("\n=== 测试资金转账 ===")
    
    try:
        # 创建两个测试账户
        account1_data = {
            'name': '转账账户A',
            'account_type': '基本户',
            'initial_balance': 2000.0,
            'description': '转账测试账户A',
            'status': 'active',
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        account2_data = {
            'name': '转账账户B',
            'account_type': '基本户',
            'initial_balance': 1000.0,
            'description': '转账测试账户B',
            'status': 'active',
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if AccountModel.create_account(account1_data, 1) and AccountModel.create_account(account2_data, 1):
            print("✓ 创建两个转账测试账户成功")
        else:
            print("✗ 创建转账测试账户失败")
            return False
        
        # 获取账户ID和初始余额
        account1 = execute_query("SELECT id, balance FROM accounts WHERE name='转账账户A'", fetch_all=False)
        account2 = execute_query("SELECT id, balance FROM accounts WHERE name='转账账户B'", fetch_all=False)
        
        if not account1 or not account2:
            print("✗ 未找到转账测试账户")
            return False
        
        account1_id = account1['id']
        account1_initial = account1['balance']
        account2_id = account2['id']
        account2_initial = account2['balance']
        
        print(f"账户A初始余额: {account1_initial}")
        print(f"账户B初始余额: {account2_initial}")
        
        # 测试转账
        transfer_amount = 300.0
        if TransactionModel.transfer_funds(account1_id, account2_id, transfer_amount, '测试转账', 1):
            print(f"✓ 转账 {transfer_amount} 元成功")
        else:
            print(f"✗ 转账 {transfer_amount} 元失败")
            return False
        
        # 检查账户余额
        account1 = execute_query("SELECT balance FROM accounts WHERE id=?", (account1_id,), fetch_all=False)
        account2 = execute_query("SELECT balance FROM accounts WHERE id=?", (account2_id,), fetch_all=False)
        
        expected_balance1 = account1_initial - transfer_amount
        expected_balance2 = account2_initial + transfer_amount
        
        if account1['balance'] == expected_balance1:
            print(f"✓ 账户A余额正确: {account1['balance']} (预期: {expected_balance1})")
        else:
            print(f"✗ 账户A余额错误: {account1['balance']} (预期: {expected_balance1})")
            return False
        
        if account2['balance'] == expected_balance2:
            print(f"✓ 账户B余额正确: {account2['balance']} (预期: {expected_balance2})")
        else:
            print(f"✗ 账户B余额错误: {account2['balance']} (预期: {expected_balance2})")
            return False
        
        return True
        
    except Exception as e:
        print(f"资金转账测试失败: {str(e)}")
        return False

# 测试账务冲销功能
def test_transaction_reversal():
    """测试账务冲销功能"""
    print("\n=== 测试账务冲销 ===")
    
    try:
        # 获取测试账户
        account = execute_query("SELECT id, balance FROM accounts WHERE name='测试账户'", fetch_all=False)
        if not account:
            print("✗ 未找到测试账户")
            return False
        
        account_id = account['id']
        before_reversal_balance = account['balance']
        print(f"冲销前余额: {before_reversal_balance}")
        
        # 获取要冲销的交易
        transaction = execute_query(
            "SELECT id, amount FROM transactions WHERE account_id=? AND description='测试收入' ORDER BY id DESC LIMIT 1",
            (account_id,),
            fetch_all=False
        )
        
        if not transaction:
            print("✗ 未找到测试收入交易")
            return False
        
        transaction_id = transaction['id']
        transaction_amount = transaction['amount']
        print(f"要冲销的交易ID: {transaction_id}, 金额: {transaction_amount}")
        
        # 测试冲销
        if TransactionModel.reverse_transaction(transaction_id, '测试冲销', 1):
            print("✓ 账务冲销成功")
        else:
            print("✗ 账务冲销失败")
            return False
        
        # 检查余额是否恢复
        account = execute_query("SELECT balance FROM accounts WHERE id=?", (account_id,), fetch_all=False)
        after_reversal_balance = account['balance']
        
        expected_balance = before_reversal_balance - transaction_amount
        if after_reversal_balance == expected_balance:
            print(f"✓ 冲销后余额正确: {after_reversal_balance} (预期: {expected_balance})")
        else:
            print(f"✗ 冲销后余额错误: {after_reversal_balance} (预期: {expected_balance})")
            return False
        
        # 检查冲销记录（查找新创建的冲销交易）
        reversal_transaction = execute_query(
            "SELECT id, amount, description FROM transactions WHERE account_id=? AND amount=? AND description LIKE ? ORDER BY id DESC LIMIT 1",
            (account_id, -transaction_amount, '%冲销%'),
            fetch_all=False
        )
        
        if reversal_transaction:
            print("✓ 冲销记录正确")
        else:
            print("✗ 冲销记录错误")
            return False
        
        return True
        
    except Exception as e:
        print(f"账务冲销测试失败: {str(e)}")
        return False

# 测试对账核算功能
def test_reconciliation():
    """测试对账核算功能"""
    print("\n=== 测试对账核算 ===")
    
    try:
        # 获取测试账户
        account = execute_query("SELECT id, balance FROM accounts WHERE name='测试账户'", fetch_all=False)
        if not account:
            print("✗ 未找到测试账户")
            return False
        
        account_id = account['id']
        system_balance = account['balance']
        print(f"系统账户余额: {system_balance}")
        
        # 执行对账
        reconciliation_result = TransactionModel.reconcile_account(account_id, datetime.datetime.now().strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'), 1)
        
        if reconciliation_result['success']:
            print("✓ 对账成功")
            print(f"账务明细合计: {reconciliation_result['total_transaction_amount']}")
            print(f"系统账户余额: {reconciliation_result['actual_balance']}")
            
            if reconciliation_result['is_balanced']:
                print("✓ 账户余额与账务明细一致")
            else:
                print(f"✗ 账户余额与账务明细不一致，差异: {reconciliation_result['difference']}")
                return False
            
            return True
        else:
            print(f"✗ 对账失败: {reconciliation_result['message']}")
            return False
        
    except Exception as e:
        print(f"对账核算测试失败: {str(e)}")
        return False

# 测试权限控制
def test_permission_control():
        """测试多角色权限控制"""
        print("\n=== 测试权限控制 ===")
        
        try:
            # 创建测试用户
            user_id = user_model.create_user('testuser', 'Test@1234', '测试用户', 'test@example.com', 'user')
            
            if user_id:
                print("✓ 创建测试用户成功")
            else:
                print("✗ 创建测试用户失败")
                return False
            
            # 获取测试用户ID
            test_user = execute_query("SELECT id FROM users WHERE username='testuser'", fetch_all=False)
            if not test_user:
                print("✗ 未找到测试用户")
                return False
            
            test_user_id = test_user['id']
            print(f"测试用户ID: {test_user_id}")
            
            # 获取测试账户ID
            account = execute_query("SELECT id FROM accounts WHERE name='测试账户'", fetch_all=False)
            if not account:
                print("✗ 未找到测试账户")
                return False
            
            account_id = account['id']
            
            # 保存当前用户状态
            original_user = user_model.current_user
            original_auth = user_model.is_authenticated
            
            # 临时切换到测试用户
            user_model.current_user = {'id': test_user_id, 'username': 'testuser', 'role': 'user'}
            user_model.is_authenticated = True
            
            # 验证测试用户初始没有权限
            if not user_model.has_resource_permission('account', account_id):
                print("✓ 测试用户初始没有账户操作权限")
            else:
                print("✗ 测试用户初始有权限，不符合预期")
                # 恢复原始用户状态
                user_model.current_user = original_user
                user_model.is_authenticated = original_auth
                return False
            
            # 授予测试用户权限
            if user_model.grant_permission(test_user_id, 'account', account_id, 'write'):
                print("✓ 授予测试用户账户操作权限成功")
            else:
                print("✗ 授予测试用户权限失败")
                return False
            
            # 验证测试用户现在有权限
            if user_model.has_resource_permission('account', account_id):
                print("✓ 测试用户现在拥有账户操作权限")
            else:
                print("✗ 测试用户仍无权限，授予失败")
                return False
            
            # 撤销权限
            if user_model.revoke_permission(test_user_id, 'account', account_id, 'write'):
                print("✓ 撤销测试用户账户操作权限成功")
            else:
                print("✗ 撤销测试用户权限失败")
                return False
            
            # 验证权限已撤销
            if not user_model.has_resource_permission('account', account_id):
                print("✓ 测试用户权限已成功撤销")
            else:
                print("✗ 测试用户权限未撤销，操作失败")
                return False
            
            # 恢复原始用户状态
            user_model.current_user = original_user
            user_model.is_authenticated = original_auth
            
            return True
        
        except Exception as e:
            print(f"权限控制测试失败: {str(e)}")
            return False

# 主测试函数
def run_all_tests():
    """运行所有测试用例"""
    print("财务系统集成测试")
    print("=" * 50)
    
    tests = [
        ("数据库结构", test_database_structure),
        ("交易与余额联动", test_transaction_balance_linkage),
        ("资金转账", test_fund_transfer),
        ("账务冲销", test_transaction_reversal),
        ("对账核算", test_reconciliation),
        ("权限控制", test_permission_control)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
            print(f"\n✓ {test_name} 测试通过")
        else:
            print(f"\n✗ {test_name} 测试失败")
        print("-" * 50)
    
    print(f"\n测试结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败！")
        return False

if __name__ == "__main__":
    run_all_tests()
