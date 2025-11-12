#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试模块
实现单元测试和集成测试功能，测试系统各个模块的功能正确性和性能
"""

import os
import sys
import time
import logging
import unittest
import json
import tempfile
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入测试所需模块
try:
    # 数据库相关
    from src.database.db_manager import execute_query, get_db_connection, init_database
    from src.database.db_access import db_access
    from src.database.db_migration import db_migration
    
    # 模型相关
    from src.models.user import user_model
    from src.models.transaction import transaction_model
    from src.models.account import account_model
    from src.models.category import category_model
    from src.models.report import report_model
    
    # 控制器相关
    from src.controllers.auth_controller import auth_controller
    from src.controllers.settings_controller import settings_controller
    from src.controllers.visualization_controller import visualization_controller
    
    # 确保测试所需的依赖都已导入
    MODULES_AVAILABLE = True
except ImportError as e:
    logging.error(f"导入测试模块失败: {str(e)}")
    MODULES_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs', 'test.log'),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("SystemTester")


class SystemTester:
    """
    系统测试器
    提供系统功能测试和性能测试功能
    """
    
    def __init__(self):
        """
        初始化系统测试器
        """
        self.test_results = {
            "start_time": None,
            "end_time": None,
            "duration": None,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_cases": []
        }
        
        # 测试数据
        self.test_user_data = {
            "username": "test_user",
            "password": "test_password123",
            "role": "user",
            "email": "test@example.com"
        }
        
        self.test_account_data = {
            "name": "测试账户",
            "type": "bank",
            "initial_balance": 10000.00,
            "description": "测试用银行账户"
        }
        
        self.test_category_data = {
            "name": "测试收入",
            "type": "income",
            "parent_id": None,
            "description": "测试收入分类"
        }
        
        # 确保测试目录存在
        self.app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_dir = os.path.join(self.app_root, 'tests', 'results')
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
    
    def run_all_tests(self):
        """
        运行所有测试
        
        Returns:
            dict: 测试结果
        """
        logger.info("开始运行所有系统测试...")
        
        # 记录开始时间
        self.test_results["start_time"] = datetime.now().isoformat()
        
        try:
            # 运行各个模块的测试
            self._test_database_connection()
            self._test_user_management()
            self._test_account_management()
            self._test_category_management()
            self._test_transaction_management()
            self._test_report_generation()
            self._test_settings_management()
            self._test_performance()
            
        except Exception as e:
            logger.error(f"测试过程中发生错误: {str(e)}")
            self._add_test_result("系统测试", "failed", f"测试过程中发生错误: {str(e)}")
        finally:
            # 记录结束时间和持续时间
            self.test_results["end_time"] = datetime.now().isoformat()
            start_time = datetime.fromisoformat(self.test_results["start_time"])
            end_time = datetime.fromisoformat(self.test_results["end_time"])
            self.test_results["duration"] = (end_time - start_time).total_seconds()
            
            # 保存测试结果
            self._save_test_results()
            
            logger.info(f"系统测试完成. 总计: {self.test_results['total_tests']}, 通过: {self.test_results['passed_tests']}, 失败: {self.test_results['failed_tests']}")
            logger.info(f"测试持续时间: {self.test_results['duration']:.2f} 秒")
        
        return self.test_results
    
    def _add_test_result(self, test_name, status, message=None):
        """
        添加测试结果
        
        Args:
            test_name: 测试名称
            status: 测试状态 (passed/failed)
            message: 测试消息
        """
        self.test_results["total_tests"] += 1
        
        if status == "passed":
            self.test_results["passed_tests"] += 1
        else:
            self.test_results["failed_tests"] += 1
        
        self.test_results["test_cases"].append({
            "name": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def _save_test_results(self):
        """
        保存测试结果到文件
        """
        try:
            # 生成测试结果文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result_file = os.path.join(self.test_dir, f'test_results_{timestamp}.json')
            
            # 保存测试结果
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"测试结果已保存到: {result_file}")
            
        except Exception as e:
            logger.error(f"保存测试结果失败: {str(e)}")
    
    def _test_database_connection(self):
        """
        测试数据库连接
        """
        test_name = "数据库连接测试"
        logger.info(f"开始测试: {test_name}")
        
        try:
            # 测试数据库连接
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 执行简单查询
            cursor.execute("SELECT COUNT(*) FROM users")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            logger.info(f"数据库连接测试通过，当前用户数: {result[0]}")
            self._add_test_result(test_name, "passed", f"数据库连接成功，当前用户数: {result[0]}")
            
        except Exception as e:
            logger.error(f"数据库连接测试失败: {str(e)}")
            self._add_test_result(test_name, "failed", f"数据库连接失败: {str(e)}")
    
    def _test_user_management(self):
        """
        测试用户管理功能
        """
        test_name = "用户管理测试"
        logger.info(f"开始测试: {test_name}")
        
        try:
            # 测试创建用户
            create_result = user_model.create_user(
                username=self.test_user_data["username"],
                password=self.test_user_data["password"],
                role=self.test_user_data["role"],
                email=self.test_user_data["email"]
            )
            
            if not create_result["success"]:
                # 如果用户已存在，尝试删除后再创建
                if "已存在" in create_result["message"]:
                    # 查找测试用户ID
                    users = user_model.get_all_users()
                    test_user_id = None
                    for user in users:
                        if user["username"] == self.test_user_data["username"]:
                            test_user_id = user["id"]
                            break
                    
                    # 删除测试用户
                    if test_user_id:
                        user_model.delete_user(test_user_id)
                        logger.info(f"已删除已存在的测试用户: {test_user_id}")
                        
                        # 重新创建用户
                        create_result = user_model.create_user(
                            username=self.test_user_data["username"],
                            password=self.test_user_data["password"],
                            role=self.test_user_data["role"],
                            email=self.test_user_data["email"]
                        )
            
            if not create_result["success"]:
                raise Exception(f"创建测试用户失败: {create_result['message']}")
            
            # 测试用户认证
            auth_result = auth_controller.login(
                username=self.test_user_data["username"],
                password=self.test_user_data["password"]
            )
            
            if not auth_result["success"]:
                raise Exception(f"用户认证失败: {auth_result['message']}")
            
            # 记录测试用户ID，用于后续清理
            self.test_user_id = auth_result["user_id"]
            
            # 测试获取用户信息
            user_info = user_model.get_user_by_id(self.test_user_id)
            if not user_info:
                raise Exception("获取用户信息失败")
            
            logger.info(f"用户管理测试通过，创建的测试用户ID: {self.test_user_id}")
            self._add_test_result(test_name, "passed", f"用户创建和认证成功，用户ID: {self.test_user_id}")
            
        except Exception as e:
            logger.error(f"用户管理测试失败: {str(e)}")
            self._add_test_result(test_name, "failed", f"用户管理测试失败: {str(e)}")
    
    def _test_account_management(self):
        """
        测试账户管理功能
        """
        test_name = "账户管理测试"
        logger.info(f"开始测试: {test_name}")
        
        try:
            # 测试创建账户
            create_result = account_model.create_account(
                name=self.test_account_data["name"],
                type=self.test_account_data["type"],
                initial_balance=self.test_account_data["initial_balance"],
                description=self.test_account_data["description"]
            )
            
            if not create_result["success"]:
                # 如果账户已存在，尝试删除后再创建
                if "已存在" in create_result["message"]:
                    # 查找测试账户ID
                    accounts = account_model.get_all_accounts()
                    test_account_id = None
                    for account in accounts:
                        if account["name"] == self.test_account_data["name"]:
                            test_account_id = account["id"]
                            break
                    
                    # 删除测试账户
                    if test_account_id:
                        account_model.delete_account(test_account_id)
                        logger.info(f"已删除已存在的测试账户: {test_account_id}")
                        
                        # 重新创建账户
                        create_result = account_model.create_account(
                            name=self.test_account_data["name"],
                            type=self.test_account_data["type"],
                            initial_balance=self.test_account_data["initial_balance"],
                            description=self.test_account_data["description"]
                        )
            
            if not create_result["success"]:
                raise Exception(f"创建测试账户失败: {create_result['message']}")
            
            # 记录测试账户ID
            self.test_account_id = create_result["account_id"]
            
            # 测试获取账户信息
            account_info = account_model.get_account_by_id(self.test_account_id)
            if not account_info:
                raise Exception("获取账户信息失败")
            
            # 测试更新账户
            update_result = account_model.update_account(
                account_id=self.test_account_id,
                name="更新后的测试账户",
                type="cash",
                description="更新后的测试描述"
            )
            
            if not update_result["success"]:
                raise Exception(f"更新账户失败: {update_result['message']}")
            
            logger.info(f"账户管理测试通过，创建的测试账户ID: {self.test_account_id}")
            self._add_test_result(test_name, "passed", f"账户创建、查询和更新成功，账户ID: {self.test_account_id}")
            
        except Exception as e:
            logger.error(f"账户管理测试失败: {str(e)}")
            self._add_test_result(test_name, "failed", f"账户管理测试失败: {str(e)}")
    
    def _test_category_management(self):
        """
        测试分类管理功能
        """
        test_name = "分类管理测试"
        logger.info(f"开始测试: {test_name}")
        
        try:
            # 测试创建分类
            create_result = category_model.create_category(
                name=self.test_category_data["name"],
                type=self.test_category_data["type"],
                parent_id=self.test_category_data["parent_id"],
                description=self.test_category_data["description"]
            )
            
            if not create_result["success"]:
                # 如果分类已存在，尝试删除后再创建
                if "已存在" in create_result["message"]:
                    # 查找测试分类ID
                    categories = category_model.get_all_categories()
                    test_category_id = None
                    for category in categories:
                        if category["name"] == self.test_category_data["name"]:
                            test_category_id = category["id"]
                            break
                    
                    # 删除测试分类
                    if test_category_id:
                        category_model.delete_category(test_category_id)
                        logger.info(f"已删除已存在的测试分类: {test_category_id}")
                        
                        # 重新创建分类
                        create_result = category_model.create_category(
                            name=self.test_category_data["name"],
                            type=self.test_category_data["type"],
                            parent_id=self.test_category_data["parent_id"],
                            description=self.test_category_data["description"]
                        )
            
            if not create_result["success"]:
                raise Exception(f"创建测试分类失败: {create_result['message']}")
            
            # 记录测试分类ID
            self.test_category_id = create_result["category_id"]
            
            # 测试获取分类信息
            category_info = category_model.get_category_by_id(self.test_category_id)
            if not category_info:
                raise Exception("获取分类信息失败")
            
            # 测试获取分类树
            category_tree = category_model.get_category_tree()
            if not isinstance(category_tree, list):
                raise Exception("获取分类树失败")
            
            logger.info(f"分类管理测试通过，创建的测试分类ID: {self.test_category_id}")
            self._add_test_result(test_name, "passed", f"分类创建、查询成功，分类ID: {self.test_category_id}")
            
        except Exception as e:
            logger.error(f"分类管理测试失败: {str(e)}")
            self._add_test_result(test_name, "failed", f"分类管理测试失败: {str(e)}")
    
    def _test_transaction_management(self):
        """
        测试交易管理功能
        """
        test_name = "交易管理测试"
        logger.info(f"开始测试: {test_name}")
        
        try:
            # 确保有测试账户和分类
            if not hasattr(self, 'test_account_id') or not hasattr(self, 'test_category_id'):
                raise Exception("缺少测试账户或分类，请先运行账户和分类测试")
            
            # 测试交易数据
            transaction_data = {
                "amount": 1000.00,
                "type": "income",
                "account_id": self.test_account_id,
                "category_id": self.test_category_id,
                "transaction_date": datetime.now().strftime("%Y-%m-%d"),
                "description": "测试收入交易",
                "created_by": self.test_user_id if hasattr(self, 'test_user_id') else 1
            }
            
            # 测试创建交易
            create_result = transaction_model.create_transaction(**transaction_data)
            
            if not create_result["success"]:
                raise Exception(f"创建测试交易失败: {create_result['message']}")
            
            # 记录测试交易ID
            self.test_transaction_id = create_result["transaction_id"]
            
            # 测试获取交易信息
            transaction_info = transaction_model.get_transaction_by_id(self.test_transaction_id)
            if not transaction_info:
                raise Exception("获取交易信息失败")
            
            # 测试获取交易列表
            transactions = transaction_model.get_transactions(
                start_date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                end_date=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            )
            
            if not isinstance(transactions, list):
                raise Exception("获取交易列表失败")
            
            # 验证交易是否在列表中
            found = any(t["id"] == self.test_transaction_id for t in transactions)
            if not found:
                raise Exception("创建的交易不在列表中")
            
            logger.info(f"交易管理测试通过，创建的测试交易ID: {self.test_transaction_id}")
            self._add_test_result(test_name, "passed", f"交易创建、查询成功，交易ID: {self.test_transaction_id}")
            
        except Exception as e:
            logger.error(f"交易管理测试失败: {str(e)}")
            self._add_test_result(test_name, "failed", f"交易管理测试失败: {str(e)}")
    
    def _test_report_generation(self):
        """
        测试报表生成功能
        """
        test_name = "报表生成测试"
        logger.info(f"开始测试: {test_name}")
        
        try:
            # 测试获取月度汇总数据
            current_month = datetime.now().strftime("%Y-%m")
            monthly_summary = report_model.get_monthly_summary(current_month)
            
            if not isinstance(monthly_summary, dict):
                raise Exception("获取月度汇总数据失败")
            
            # 测试生成利润表
            income_statement = report_model.generate_income_statement(
                start_date=(datetime.now().replace(day=1) - timedelta(days=30)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            if not isinstance(income_statement, dict):
                raise Exception("生成利润表失败")
            
            # 测试生成资产负债表
            balance_sheet = report_model.generate_balance_sheet(
                as_of_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            if not isinstance(balance_sheet, dict):
                raise Exception("生成资产负债表失败")
            
            logger.info("报表生成测试通过")
            self._add_test_result(test_name, "passed", "月度汇总、利润表、资产负债表生成成功")
            
        except Exception as e:
            logger.error(f"报表生成测试失败: {str(e)}")
            self._add_test_result(test_name, "failed", f"报表生成测试失败: {str(e)}")
    
    def _test_settings_management(self):
        """
        测试设置管理功能
        """
        test_name = "设置管理测试"
        logger.info(f"开始测试: {test_name}")
        
        try:
            # 测试获取设置
            theme_setting = settings_controller.get_setting("app.theme", "light")
            
            # 测试更新设置
            test_value = "dark" if theme_setting == "light" else "light"
            update_result = settings_controller.set_setting("app.theme", test_value)
            
            if not update_result:
                raise Exception("更新设置失败")
            
            # 验证设置已更新
            updated_theme = settings_controller.get_setting("app.theme")
            if updated_theme != test_value:
                raise Exception(f"设置更新验证失败，期望: {test_value}, 实际: {updated_theme}")
            
            # 恢复原始设置
            settings_controller.set_setting("app.theme", theme_setting)
            
            logger.info("设置管理测试通过")
            self._add_test_result(test_name, "passed", "设置获取和更新功能正常")
            
        except Exception as e:
            logger.error(f"设置管理测试失败: {str(e)}")
            self._add_test_result(test_name, "failed", f"设置管理测试失败: {str(e)}")
    
    def _test_performance(self):
        """
        测试系统性能
        """
        test_name = "系统性能测试"
        logger.info(f"开始测试: {test_name}")
        
        try:
            performance_results = []
            
            # 测试数据库查询性能
            start_time = time.time()
            for _ in range(10):
                execute_query("SELECT COUNT(*) FROM transactions")
            db_query_time = time.time() - start_time
            performance_results.append(f"数据库查询(10次): {db_query_time:.3f}秒")
            
            # 测试数据加载性能
            start_time = time.time()
            transaction_model.get_transactions(limit=100)
            data_load_time = time.time() - start_time
            performance_results.append(f"数据加载(100条): {data_load_time:.3f}秒")
            
            # 测试报表生成性能
            start_time = time.time()
            report_model.get_monthly_summary(datetime.now().strftime("%Y-%m"))
            report_time = time.time() - start_time
            performance_results.append(f"报表生成: {report_time:.3f}秒")
            
            # 性能评估
            is_performance_good = (
                db_query_time < 0.5 and 
                data_load_time < 1.0 and 
                report_time < 2.0
            )
            
            performance_message = "; ".join(performance_results)
            logger.info(f"性能测试结果: {performance_message}")
            
            self._add_test_result(
                test_name,
                "passed" if is_performance_good else "failed",
                performance_message
            )
            
        except Exception as e:
            logger.error(f"性能测试失败: {str(e)}")
            self._add_test_result(test_name, "failed", f"性能测试失败: {str(e)}")
    
    def cleanup_test_data(self):
        """
        清理测试数据
        """
        logger.info("开始清理测试数据...")
        
        try:
            # 删除测试交易
            if hasattr(self, 'test_transaction_id'):
                transaction_model.delete_transaction(self.test_transaction_id)
                logger.info(f"已删除测试交易: {self.test_transaction_id}")
            
            # 删除测试分类
            if hasattr(self, 'test_category_id'):
                category_model.delete_category(self.test_category_id)
                logger.info(f"已删除测试分类: {self.test_category_id}")
            
            # 删除测试账户
            if hasattr(self, 'test_account_id'):
                account_model.delete_account(self.test_account_id)
                logger.info(f"已删除测试账户: {self.test_account_id}")
            
            # 删除测试用户
            if hasattr(self, 'test_user_id'):
                user_model.delete_user(self.test_user_id)
                logger.info(f"已删除测试用户: {self.test_user_id}")
            
            logger.info("测试数据清理完成")
            
        except Exception as e:
            logger.error(f"清理测试数据失败: {str(e)}")
    
    def generate_performance_report(self):
        """
        生成性能报告
        
        Returns:
            dict: 性能报告
        """
        performance_report = {
            "timestamp": datetime.now().isoformat(),
            "test_environment": {
                "python_version": sys.version,
                "operating_system": os.name,
            },
            "performance_metrics": []
        }
        
        try:
            # 测试数据库连接时间
            start_time = time.time()
            conn = get_db_connection()
            conn.close()
            db_connect_time = time.time() - start_time
            performance_report["performance_metrics"].append({
                "metric": "数据库连接时间",
                "value": f"{db_connect_time:.4f}秒",
                "unit": "秒",
                "raw_value": db_connect_time
            })
            
            # 测试批量插入性能
            batch_size = 100
            start_time = time.time()
            
            # 创建临时分类和账户用于测试
            category_result = category_model.create_category(
                name="性能测试分类",
                type="expense",
                description="用于性能测试的临时分类"
            )
            
            account_result = account_model.create_account(
                name="性能测试账户",
                type="bank",
                initial_balance=0,
                description="用于性能测试的临时账户"
            )
            
            if category_result["success"] and account_result["success"]:
                # 批量插入交易记录
                conn = get_db_connection()
                cursor = conn.cursor()
                
                try:
                    for i in range(batch_size):
                        cursor.execute(
                            """
                            INSERT INTO transactions (amount, type, account_id, category_id, 
                                                  transaction_date, description, created_at, updated_at, created_by)
                            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
                            """,
                            (100.0 + i, "expense", account_result["account_id"], 
                             category_result["category_id"], datetime.now().strftime("%Y-%m-%d"),
                             f"性能测试交易 {i}", 1)
                        )
                    
                    conn.commit()
                    
                finally:
                    cursor.close()
                    conn.close()
                    
                    # 删除临时数据
                    category_model.delete_category(category_result["category_id"])
                    account_model.delete_account(account_result["account_id"])
            
            batch_insert_time = time.time() - start_time
            performance_report["performance_metrics"].append({
                "metric": f"批量插入{batch_size}条记录",
                "value": f"{batch_insert_time:.4f}秒",
                "unit": "秒",
                "raw_value": batch_insert_time
            })
            
            # 测试复杂查询性能
            start_time = time.time()
            complex_query = """
            SELECT c.name as category_name, SUM(t.amount) as total_amount 
            FROM transactions t 
            JOIN categories c ON t.category_id = c.id 
            WHERE t.transaction_date >= date('now', '-30 days') 
            GROUP BY c.id, c.name 
            ORDER BY total_amount DESC
            """
            
            result = execute_query(complex_query)
            complex_query_time = time.time() - start_time
            performance_report["performance_metrics"].append({
                "metric": "复杂查询(30天分类汇总)",
                "value": f"{complex_query_time:.4f}秒",
                "unit": "秒",
                "raw_value": complex_query_time,
                "result_count": len(result)
            })
            
            # 保存性能报告
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = os.path.join(self.test_dir, f'performance_report_{timestamp}.json')
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(performance_report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"性能报告已生成: {report_file}")
            
        except Exception as e:
            logger.error(f"生成性能报告失败: {str(e)}")
            performance_report["error"] = str(e)
        
        return performance_report


# 性能优化建议生成器
class PerformanceOptimizer:
    """
    性能优化建议生成器
    基于系统检测结果提供优化建议
    """
    
    def __init__(self):
        """
        初始化性能优化器
        """
        self.optimization_suggestions = []
        self.app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def analyze_system(self):
        """
        分析系统性能并生成优化建议
        
        Returns:
            list: 优化建议列表
        """
        logger.info("开始系统性能分析...")
        
        try:
            # 分析数据库索引
            self._analyze_database_indexes()
            
            # 分析数据库表大小
            self._analyze_database_size()
            
            # 分析代码结构
            self._analyze_code_structure()
            
            # 分析内存使用
            self._analyze_memory_usage()
            
            # 保存优化建议
            self._save_optimization_report()
            
            logger.info(f"性能优化分析完成，发现 {len(self.optimization_suggestions)} 项优化建议")
            
        except Exception as e:
            logger.error(f"系统性能分析失败: {str(e)}")
            self.optimization_suggestions.append({
                "severity": "error",
                "category": "analysis",
                "title": "性能分析失败",
                "description": f"系统性能分析过程中发生错误: {str(e)}",
                "recommendation": "请检查系统日志获取详细信息"
            })
        
        return self.optimization_suggestions
    
    def _analyze_database_indexes(self):
        """
        分析数据库索引使用情况
        """
        try:
            # 检查索引使用情况
            queries = [
                "SELECT name FROM sqlite_master WHERE type='index'",
                "SELECT * FROM sqlite_stat1"
            ]
            
            index_info = execute_query(queries[0])
            stat_info = execute_query(queries[1])
            
            # 检查是否缺少关键索引
            if not any("idx_transactions_date" in str(info) for info in index_info):
                self.optimization_suggestions.append({
                    "severity": "high",
                    "category": "database",
                    "title": "缺少交易日期索引",
                    "description": "在transactions表上缺少transaction_date字段的索引，这会导致日期范围查询性能下降",
                    "recommendation": "CREATE INDEX idx_transactions_date ON transactions(transaction_date)"
                })
            
            if not any("idx_transactions_account" in str(info) for info in index_info):
                self.optimization_suggestions.append({
                    "severity": "medium",
                    "category": "database",
                    "title": "缺少账户外键索引",
                    "description": "在transactions表上缺少account_id字段的索引，这会影响按账户查询的性能",
                    "recommendation": "CREATE INDEX idx_transactions_account ON transactions(account_id)"
                })
            
            if not any("idx_transactions_category" in str(info) for info in index_info):
                self.optimization_suggestions.append({
                    "severity": "medium",
                    "category": "database",
                    "title": "缺少分类外键索引",
                    "description": "在transactions表上缺少category_id字段的索引，这会影响按分类查询的性能",
                    "recommendation": "CREATE INDEX idx_transactions_category ON transactions(category_id)"
                })
            
        except Exception as e:
            logger.error(f"分析数据库索引失败: {str(e)}")
    
    def _analyze_database_size(self):
        """
        分析数据库大小
        """
        try:
            # 获取数据库文件大小
            db_path = os.path.join(self.app_root, 'data', 'finance.db')
            if os.path.exists(db_path):
                db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
                
                if db_size_mb > 100:
                    self.optimization_suggestions.append({
                        "severity": "high",
                        "category": "database",
                        "title": "数据库文件过大",
                        "description": f"数据库文件大小为 {db_size_mb:.2f} MB，可能影响性能",
                        "recommendation": "考虑进行数据归档，将历史数据移至归档表或备份后删除不需要的历史数据"
                    })
                elif db_size_mb > 50:
                    self.optimization_suggestions.append({
                        "severity": "medium",
                        "category": "database",
                        "title": "数据库文件较大",
                        "description": f"数据库文件大小为 {db_size_mb:.2f} MB",
                        "recommendation": "定期运行VACUUM命令优化数据库文件大小和性能"
                    })
            
        except Exception as e:
            logger.error(f"分析数据库大小失败: {str(e)}")
    
    def _analyze_code_structure(self):
        """
        分析代码结构
        """
        try:
            # 检查是否有需要优化的代码结构
            # 这里可以添加更复杂的代码分析逻辑
            self.optimization_suggestions.append({
                "severity": "low",
                "category": "code",
                "title": "代码结构优化",
                "description": "检查到可能需要优化的代码结构",
                "recommendation": "1. 确保所有数据库连接在使用后正确关闭\n2. 使用参数化查询防止SQL注入\n3. 大型循环中避免频繁的数据库操作\n4. 考虑使用连接池管理数据库连接"
            })
            
        except Exception as e:
            logger.error(f"分析代码结构失败: {str(e)}")
    
    def _analyze_memory_usage(self):
        """
        分析内存使用情况
        """
        try:
            # 这里可以添加更复杂的内存分析逻辑
            self.optimization_suggestions.append({
                "severity": "low",
                "category": "memory",
                "title": "内存使用优化",
                "description": "应用程序可能存在内存使用优化空间",
                "recommendation": "1. 大型数据集查询时使用分页加载\n2. 避免在内存中缓存大量数据\n3. 及时释放不再使用的大对象\n4. 使用生成器替代大型列表操作"
            })
            
        except Exception as e:
            logger.error(f"分析内存使用失败: {str(e)}")
    
    def _save_optimization_report(self):
        """
        保存优化建议报告
        """
        try:
            # 生成报告文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_dir = os.path.join(self.app_root, 'tests', 'results')
            
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            report_file = os.path.join(report_dir, f'optimization_report_{timestamp}.json')
            
            # 构建报告内容
            report = {
                "generated_at": datetime.now().isoformat(),
                "total_suggestions": len(self.optimization_suggestions),
                "severity_counts": {
                    "high": sum(1 for s in self.optimization_suggestions if s["severity"] == "high"),
                    "medium": sum(1 for s in self.optimization_suggestions if s["severity"] == "medium"),
                    "low": sum(1 for s in self.optimization_suggestions if s["severity"] == "low")
                },
                "suggestions": self.optimization_suggestions
            }
            
            # 保存报告
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"优化建议报告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"保存优化建议报告失败: {str(e)}")


if __name__ == "__main__":
    # 运行系统测试
    print("=== 企业财务账目录入与利润核算系统 - 系统测试 ===")
    
    # 检查模块是否可用
    if not MODULES_AVAILABLE:
        print("错误: 无法加载测试所需的模块，请确保所有依赖已正确安装。")
        sys.exit(1)
    
    # 创建并运行测试器
    tester = SystemTester()
    
    try:
        # 运行所有测试
        results = tester.run_all_tests()
        
        # 打印测试摘要
        print(f"\n=== 测试摘要 ===")
        print(f"测试总数: {results['total_tests']}")
        print(f"通过测试: {results['passed_tests']}")
        print(f"失败测试: {results['failed_tests']}")
        print(f"测试时间: {results['duration']:.2f} 秒")
        
        # 运行性能分析
        print("\n=== 性能分析 ===")
        optimizer = PerformanceOptimizer()
        suggestions = optimizer.analyze_system()
        
        print(f"发现 {len(suggestions)} 项优化建议:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. [{suggestion['severity'].upper()}] {suggestion['title']}")
            print(f"   {suggestion['description']}")
            print(f"   建议: {suggestion['recommendation']}")
            print()
    
    finally:
        # 清理测试数据
        tester.cleanup_test_data()
        print("测试完成，已清理测试数据。")