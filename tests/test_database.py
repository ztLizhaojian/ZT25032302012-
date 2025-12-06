#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库功能测试脚本
验证数据库管理系统的各项功能
"""
import os
import sys
import time
import json
import unittest
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.db_manager import DatabaseManager, DatabaseError
from src.database.db_migration import MigrationManager, MigrationError
from src.utils.backup_manager import BackupManager
from src.utils.config_manager import config_manager, get_config, set_config
from src.utils.logger import LoggerManager
from src.models.system_config import init_system_config_table, get_system_config, update_system_config


class TestDatabaseFunctionality(unittest.TestCase):
    """
    数据库功能测试类
    """
    
    @classmethod
    def setUpClass(cls):
        """
        测试类初始化，设置日志和测试环境
        """
        # 设置测试配置
        cls.test_db_path = "./test_finance_system.db"
        cls.test_backup_dir = "./test_backups"
        
        # 设置测试配置
        set_config('database.path', cls.test_db_path, source='file')
        set_config('database.backup.folder', cls.test_backup_dir, source='file')
        set_config('database.backup.enabled', True, source='file')
        
        # 设置日志
        LoggerManager.init_logging()
        cls.logger = LoggerManager.get_logger('database_tests')
        cls.logger.info("开始数据库功能测试")
        
        # 清理测试文件
        cls._cleanup_test_files()
    
    @classmethod
    def tearDownClass(cls):
        """
        测试类清理，删除测试文件
        """
        cls._cleanup_test_files()
        cls.logger.info("数据库功能测试完成")
    
    @classmethod
    def _cleanup_test_files(cls):
        """
        清理测试文件
        """
        # 删除测试数据库文件
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
                cls.logger.info(f"已删除测试数据库文件: {cls.test_db_path}")
            except Exception as e:
                cls.logger.warning(f"删除测试数据库文件失败: {str(e)}")
        
        # 删除测试备份文件夹
        if os.path.exists(cls.test_backup_dir):
            try:
                import shutil
                shutil.rmtree(cls.test_backup_dir)
                cls.logger.info(f"已删除测试备份文件夹: {cls.test_backup_dir}")
            except Exception as e:
                cls.logger.warning(f"删除测试备份文件夹失败: {str(e)}")
    
    def setUp(self):
        """
        每个测试方法执行前的设置
        """
        # 初始化数据库管理器
        self.db_manager = DatabaseManager()
        # 初始化迁移管理器
        self.migration_manager = MigrationManager(self.db_manager)
        
        # 创建测试表
        self._create_test_tables()
    
    def tearDown(self):
        """
        每个测试方法执行后的清理
        """
        try:
            # 清理测试数据（先删除依赖表，再删除主表）
            self.db_manager.execute("DELETE FROM transactions")
            self.db_manager.execute("DELETE FROM users")
            # 重置自增ID
            self.db_manager.execute("DELETE FROM sqlite_sequence WHERE name='users'")
            self.db_manager.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
        except Exception as e:
            self.logger.warning(f"清理测试数据时出错: {str(e)}")
        finally:
            # 关闭数据库连接
            self.db_manager.close()
    
    def _create_test_tables(self):
        """
        创建测试表
        """
        # 先删除已存在的表（注意删除顺序，避免外键约束错误）
        try:
            self.db_manager.execute("DROP TABLE IF EXISTS transactions")
            self.db_manager.execute("DROP TABLE IF EXISTS users")
        except Exception as e:
            self.logger.warning(f"删除测试表时出错: {str(e)}")
        
        # 创建用户表
        self.db_manager.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        # 创建交易表
        self.db_manager.execute(
            """
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        
        # 初始化系统配置表
        init_system_config_table(self.db_manager)
    
    def test_database_connection(self):
        """
        测试数据库连接功能
        """
        self.logger.info("测试数据库连接功能")
        
        # 测试连接是否成功
        result = self.db_manager.execute("SELECT 'test' as connection_test")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['connection_test'], 'test')
        self.logger.info("✓ 数据库连接测试通过")
    
    def test_basic_crud_operations(self):
        """
        测试基本的CRUD操作
        """
        self.logger.info("测试基本的CRUD操作")
        
        # 测试插入（Create）
        user_id = self.db_manager.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)", 
            ('测试用户', 'test@example.com'),
            return_lastrowid=True
        )
        self.assertGreater(user_id, 0)
        
        # 测试查询（Read）
        user = self.db_manager.execute(
            "SELECT * FROM users WHERE id = ?", 
            (user_id,)
        )[0]
        self.assertEqual(user['name'], '测试用户')
        self.assertEqual(user['email'], 'test@example.com')
        
        # 测试更新（Update）
        self.db_manager.execute(
            "UPDATE users SET name = ? WHERE id = ?", 
            ('更新后的用户', user_id)
        )
        updated_user = self.db_manager.execute(
            "SELECT * FROM users WHERE id = ?", 
            (user_id,)
        )[0]
        self.assertEqual(updated_user['name'], '更新后的用户')
        
        # 测试删除（Delete）
        self.db_manager.execute(
            "DELETE FROM users WHERE id = ?", 
            (user_id,)
        )
        remaining_users = self.db_manager.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        self.assertEqual(len(remaining_users), 0)
        
        self.logger.info("✓ CRUD操作测试通过")
    
    def test_transaction_handling(self):
        """
        测试事务处理机制
        """
        self.logger.info("测试事务处理机制")
        
        try:
            # 开始事务
            self.db_manager.begin_transaction()
            
            # 插入用户
            user_id = self.db_manager.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)", 
                ('事务测试用户', 'transaction@example.com'),
                return_lastrowid=True
            )
            
            # 插入交易记录
            self.db_manager.execute(
                "INSERT INTO transactions (user_id, amount, description) VALUES (?, ?, ?)", 
                (user_id, 100.0, '测试交易')
            )
            
            # 提交事务
            self.db_manager.commit()
            
            # 验证数据已保存
            user_count = len(self.db_manager.execute("SELECT * FROM users WHERE id = ?", (user_id,)))
            transaction_count = len(self.db_manager.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,)))
            
            self.assertEqual(user_count, 1)
            self.assertEqual(transaction_count, 1)
            
            # 测试回滚
            self.db_manager.begin_transaction()
            self.db_manager.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)", 
                ('回滚测试用户', 'rollback@example.com')
            )
            self.db_manager.rollback()
            
            # 验证回滚成功
            rollback_count = len(self.db_manager.execute("SELECT * FROM users WHERE email = ?", ('rollback@example.com',)))
            self.assertEqual(rollback_count, 0)
            
            self.logger.info("✓ 事务处理测试通过")
            
        except Exception as e:
            self.db_manager.rollback()
            self.fail(f"事务处理测试失败: {str(e)}")
    
    def test_error_handling(self):
        """
        测试错误处理机制
        """
        self.logger.info("测试错误处理机制")
        
        # 测试SQL语法错误
        with self.assertRaises(DatabaseError):
            self.db_manager.execute("SELECT * FROM non_existent_table")
        
        # 测试唯一约束错误
        self.db_manager.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)", 
            ('唯一约束测试', 'unique@example.com')
        )
        
        with self.assertRaises(DatabaseError):
            self.db_manager.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)", 
                ('重复邮箱测试', 'unique@example.com')
            )
        
        self.logger.info("✓ 错误处理测试通过")
    
    def test_migration_functionality(self):
        """
        测试数据库迁移功能
        """
        self.logger.info("测试数据库迁移功能")
        
        # 模拟迁移脚本
        migrations = [
            {
                'version': '1.0.1',
                'description': '添加备注字段到用户表',
                'upgrade': 'ALTER TABLE users ADD COLUMN notes TEXT',
                'downgrade': 'ALTER TABLE users DROP COLUMN notes'
            },
            {
                'version': '1.0.2',
                'description': '添加状态字段到交易表',
                'upgrade': 'ALTER TABLE transactions ADD COLUMN status TEXT DEFAULT "pending"',
                'downgrade': 'ALTER TABLE transactions DROP COLUMN status'
            }
        ]
        
        # 执行迁移
        for migration in migrations:
            self.migration_manager._execute_migration(migration)
        
        # 验证迁移结果
        user_columns = [col[1] for col in self.db_manager.execute("PRAGMA table_info(users)")]
        transaction_columns = [col[1] for col in self.db_manager.execute("PRAGMA table_info(transactions)")]
        
        self.assertIn('notes', user_columns)
        self.assertIn('status', transaction_columns)
        
        # 执行回滚
        self.migration_manager.downgrade('1.0.0')
        
        # 验证回滚结果
        user_columns_after = [col[1] for col in self.db_manager.execute("PRAGMA table_info(users)")]
        transaction_columns_after = [col[1] for col in self.db_manager.execute("PRAGMA table_info(transactions)")]
        
        self.assertNotIn('notes', user_columns_after)
        self.assertNotIn('status', transaction_columns_after)
        
        self.logger.info("✓ 数据库迁移测试通过")
    
    def test_backup_and_restore(self):
        """
        测试数据备份和恢复功能
        """
        self.logger.info("测试数据备份和恢复功能")
        
        # 插入测试数据
        user_id = self.db_manager.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)", 
            ('备份测试用户', 'backup@example.com'),
            return_lastrowid=True
        )
        
        self.db_manager.execute(
            "INSERT INTO transactions (user_id, amount, description) VALUES (?, ?, ?)", 
            (user_id, 500.0, '备份测试交易')
        )
        
        # 创建备份
        backup_file = self.db_manager.create_backup()
        self.assertTrue(os.path.exists(backup_file))
        self.logger.info(f"创建备份文件: {backup_file}")
        
        # 清空数据
        self.db_manager.execute("DELETE FROM transactions")
        self.db_manager.execute("DELETE FROM users")
        
        # 验证数据已清空
        user_count = len(self.db_manager.execute("SELECT * FROM users"))
        self.assertEqual(user_count, 0)
        
        # 恢复备份
        self.db_manager.restore_from_backup(backup_file)
        
        # 验证数据已恢复
        restored_users = self.db_manager.execute("SELECT * FROM users WHERE email = ?", ('backup@example.com',))
        restored_transactions = self.db_manager.execute("SELECT * FROM transactions")
        
        self.assertEqual(len(restored_users), 1)
        self.assertEqual(len(restored_transactions), 1)
        self.assertEqual(restored_transactions[0]['amount'], 500.0)
        
        self.logger.info("✓ 备份恢复测试通过")
    
    def test_auto_backup(self):
        """
        测试自动备份功能
        """
        self.logger.info("测试自动备份功能")
        
        # 启用自动备份（间隔设为1分钟）
        set_config('database.backup.interval_hours', 1/60, source='file')
        self.db_manager.stop_auto_backup()
        self.db_manager.start_auto_backup()
        
        # 等待一段时间让自动备份执行
        self.logger.info("等待自动备份执行...")
        time.sleep(65)  # 稍等超过1分钟
        
        # 获取备份列表
        backups = self.db_manager.list_backups()
        self.logger.info(f"自动备份数量: {len(backups)}")
        
        # 至少应该有一个备份
        self.assertGreaterEqual(len(backups), 1)
        
        # 停止自动备份
        self.db_manager.stop_auto_backup()
        self.assertFalse(self.db_manager.is_auto_backup_running())
        
        self.logger.info("✓ 自动备份测试通过")
    
    def test_system_config(self):
        """
        测试系统配置管理功能
        """
        self.logger.info("测试系统配置管理功能")
        
        # 设置数据库配置
        update_system_config('test.setting', json.dumps({'value': 'test_value'}))
        
        # 获取配置
        configs = get_system_config()
        test_config = next((c for c in configs if c['key'] == 'test.setting'), None)
        
        self.assertIsNotNone(test_config)
        self.assertEqual(json.loads(test_config['value']), {'value': 'test_value'})
        
        # 使用配置管理器获取
        config_value = get_config('test.setting')
        self.assertEqual(config_value, {'value': 'test_value'})
        
        # 测试配置优先级（数据库 > 文件）
        set_config('app.name', 'File Config Name', source='file')
        file_name = get_config('app.name')
        
        set_config('app.name', 'Database Config Name', source='database')
        db_name = get_config('app.name')
        
        self.assertEqual(file_name, 'File Config Name')
        self.assertEqual(db_name, 'Database Config Name')
        
        self.logger.info("✓ 系统配置管理测试通过")
    
    def test_cleanup_old_backups(self):
        """
        测试清理过期备份功能
        """
        self.logger.info("测试清理过期备份功能")
        
        # 创建多个测试备份文件
        backup_manager = BackupManager(self.db_manager.db_path, self.test_backup_dir)
        
        # 创建5个备份
        backup_files = []
        for i in range(5):
            backup_file = backup_manager.create_backup()
            backup_files.append(backup_file)
            self.logger.info(f"创建测试备份 {i+1}: {backup_file}")
            time.sleep(1)  # 确保文件名不同
        
        # 清理备份，只保留最新的3个
        deleted_count = backup_manager.cleanup_old_backups(keep_days=0, min_keep=3)
        
        # 验证清理结果
        remaining_backups = backup_manager.list_backups()
        self.assertEqual(len(remaining_backups), 3)
        self.assertEqual(deleted_count, 2)
        
        self.logger.info("✓ 备份清理测试通过")


def run_all_tests():
    """
    运行所有测试
    """
    print("=" * 60)
    print("数据库功能测试套件")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDatabaseFunctionality)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print(f"测试结果: 运行 {result.testsRun} 个测试, "
          f"失败 {len(result.failures)} 个, "
          f"错误 {len(result.errors)} 个")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
