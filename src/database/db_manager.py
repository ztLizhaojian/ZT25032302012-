#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器模块
负责数据库的初始化、连接管理、查询执行和备份恢复等功能
"""

# 导入模块
import os
import sqlite3
import json
import shutil
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple

# 默认数据库路径（避免循环导入问题）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, './data/finance_system.db')
DB_PATH = os.path.abspath(DB_PATH)

# 导入配置管理模块
from src.utils.config_manager import get_config

# 导入日志和错误处理模块
from src.utils.logger import (
    get_logger, log_error, log_info, log_debug,
    handle_errors, DatabaseError, DataValidationError,
    NotFoundError, AccessDeniedError, OperationLogger
)

# 导入备份管理模块
from src.utils.backup_manager import BackupManager, create_backup, restore_backup, list_all_backups, cleanup_backups

class DatabaseManager:
    """
    数据库管理器类
    负责数据库的初始化、连接管理、查询执行和备份恢复等功能
    """
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径（优先级高于配置文件）
        """
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 确定数据库路径（参数优先级高于配置文件）
        if db_path is None:
            # 从配置文件获取路径
            config_db_path = get_config('database.path', './data/finance_system.db')
            
            # 确保路径是绝对路径或相对于项目根目录
            if not os.path.isabs(config_db_path):
                db_path = os.path.join(project_root, config_db_path)
            else:
                db_path = config_db_path
        
        self.db_path = os.path.abspath(db_path)
        
        # 确保数据库目录存在
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        # 初始化日志记录器
        self.logger = get_logger('database_manager')
        self.logger.info(f"数据库管理器初始化成功: {self.db_path}")
        
        # 从配置获取备份设置
        backup_enabled = get_config('database.backup.enabled', True)
        backup_folder = get_config('database.backup.folder', './data/backups')
        
        # 解析备份文件夹路径
        if not os.path.isabs(backup_folder):
            backup_folder = os.path.join(project_root, backup_folder)
        
        # 初始化备份管理器
        self.backup_manager = BackupManager(self.db_path, backup_dir=backup_folder)
        
        # 如果配置启用了自动备份，启动自动备份
        if backup_enabled:
            interval_hours = get_config('database.backup.interval_hours', 24)
            try:
                self.start_auto_backup(interval_hours)
                self.logger.info(f"自动备份已根据配置启动，间隔: {interval_hours} 小时")
            except Exception as e:
                self.logger.error(f"启动自动备份失败: {str(e)}")
        
        # 创建数据库连接
        self._conn = None
    
    def execute(self, query: str, params: Optional[Tuple] = None, 
                fetch: bool = False, fetch_all: bool = False, 
                return_lastrowid: bool = False) -> Any:
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            fetch: 是否返回单条记录
            fetch_all: 是否返回所有记录
            return_lastrowid: 是否返回最后插入的行ID
            
        Returns:
            查询结果、影响的行数或最后插入的行ID
        """
        try:
            # 自动为SELECT查询设置fetch_all=True，与测试期望保持一致
            query_upper = query.strip().upper()
            # 识别SELECT查询和WITH开头的SELECT查询
            is_select_query = query_upper.startswith('SELECT') or (query_upper.startswith('WITH') and 'SELECT' in query_upper)
            if is_select_query and not fetch and not fetch_all:
                fetch_all = True
            
            # 直接创建数据库连接
            import sqlite3
            if not hasattr(self, '_conn') or self._conn is None:
                self._conn = sqlite3.connect(self.db_path)
                # 默认启用外键约束和字典模式
                self._conn.execute('PRAGMA foreign_keys = ON')
                self._conn.row_factory = sqlite3.Row
            
            cursor = self._conn.cursor()
            
            # 执行查询
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 处理返回值
            if is_select_query:
                if fetch:
                    result = cursor.fetchone()
                    # 将sqlite3.Row转换为字典
                    if result:
                        result = dict(result)
                else:
                    result = cursor.fetchall()
                    # 将sqlite3.Row列表转换为字典列表
                    result = [dict(row) for row in result]
            else:
                # 对于非SELECT语句
                if return_lastrowid:
                    result = cursor.lastrowid
                else:
                    result = cursor.rowcount
            
            # 只有在非事务模式下才提交
            is_transaction_mode = getattr(self._conn, 'isolation_level', '') == ''
            if not is_transaction_mode:
                self._conn.commit()
            
            cursor.close()
            return result
            
        except sqlite3.IntegrityError as e:
            # 特殊处理完整性错误，如唯一约束冲突
            error_message = str(e)
            self.logger.error(f"数据库完整性错误: {error_message}")
            # 保持原始错误信息，以便测试能够识别具体的约束错误
            raise DatabaseError(error_message) from e
        except Exception as e:
            self.logger.error(f"执行SQL查询失败: {str(e)}")
            raise DatabaseError(f"执行SQL查询失败: {str(e)}") from e
    
    @handle_errors(logger_name='database_manager', fallback_return=None)
    def close(self):
        """
        关闭数据库连接
        """
        if self._conn is not None:
            try:
                self._conn.close()
                self._conn = None
                self.logger.info("数据库连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭数据库连接失败: {str(e)}")
                raise DatabaseError(f"关闭数据库连接失败: {str(e)}")
    
    def rollback(self):
        """
        回滚事务
        """
        try:
            if hasattr(self, '_conn') and self._conn is not None:
                self._conn.rollback()
                # 恢复默认隔离级别
                self._conn.isolation_level = None
                self.logger.info("事务已回滚")
        except Exception as e:
            self.logger.error(f"回滚事务失败: {str(e)}")
            # 即使回滚失败，也要尝试重置隔离级别
            if hasattr(self, '_conn') and self._conn is not None:
                try:
                    self._conn.isolation_level = None
                except:
                    pass
            raise DatabaseError(f"回滚事务失败: {str(e)}") from e
    
    def begin_transaction(self):
        """
        开始事务
        """
        try:
            # 确保连接存在
            if not hasattr(self, '_conn') or self._conn is None:
                import sqlite3
                self._conn = sqlite3.connect(self.db_path)
                self._conn.execute('PRAGMA foreign_keys = ON')
                self._conn.row_factory = sqlite3.Row
            
            # 先回滚可能存在的未提交事务
            try:
                self._conn.rollback()
            except:
                pass
            
            # SQLite事务处理：设置isolation_level为''会启用显式事务
            self._conn.isolation_level = ''
            # 显式开始事务
            self._conn.execute('BEGIN TRANSACTION')
            self.logger.info("事务已开始")
        except Exception as e:
            self.logger.error(f"开始事务失败: {str(e)}")
            # 发生错误时确保隔离级别被重置
            if hasattr(self, '_conn') and self._conn is not None:
                try:
                    self._conn.isolation_level = None
                    self._conn.rollback()
                except:
                    pass
            raise DatabaseError(f"开始事务失败: {str(e)}") from e
    
    def commit(self):
        """
        提交事务
        """
        try:
            if hasattr(self, '_conn') and self._conn is not None:
                self._conn.commit()
                # 恢复默认隔离级别
                self._conn.isolation_level = None
                self.logger.info("事务已提交")
        except Exception as e:
            self.logger.error(f"提交事务失败: {str(e)}")
            raise DatabaseError(f"提交事务失败: {str(e)}") from e

# 配置日志
logger = get_logger("DBManager")

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                      'data', 'finance_system.db')

# 确保数据目录存在
def ensure_data_directory():
    """确保数据目录存在"""
    data_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            logger.info(f"创建数据目录: {data_dir}")
        except Exception as e:
            logger.error(f"创建数据目录失败: {str(e)}")
            raise

def init_db():
    """
    初始化数据库
    创建必要的表结构和初始数据
    """
    try:
        # 确保数据目录存在
        ensure_data_directory()
        
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            fullname TEXT,
            email TEXT,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT
        )
        ''')
        
        # 创建账户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            description TEXT,
            user_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 创建分类表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,  -- income 或 expense
            icon TEXT,
            color TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建交易表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            category_id INTEGER,
            amount REAL NOT NULL,
            type TEXT NOT NULL,  -- income 或 expense
            date TEXT NOT NULL,
            description TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id),
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        ''')
        
        # 创建预算表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            amount REAL NOT NULL,
            period TEXT NOT NULL,  -- monthly, yearly
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        ''')
        
        # 创建附件表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER,
            filename TEXT,
            filepath TEXT,
            filetype TEXT,
            filesize INTEGER,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (transaction_id) REFERENCES transactions (id)
        )
        ''')
        
        # 创建交易草稿表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            draft_data JSON,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 创建系统配置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            config_value TEXT,
            config_type TEXT DEFAULT 'string',
            description TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建操作日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            operation_type TEXT,
            operation_desc TEXT,
            operation_table TEXT,
            operation_data TEXT,
            ip_address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 创建对账日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reconciliation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            actual_balance REAL,
            theoretical_balance REAL,
            difference REAL,
            is_balanced INTEGER,
            reconciled_by INTEGER,
            reconciled_at TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts (id),
            FOREIGN KEY (reconciled_by) REFERENCES users (id)
        )
        ''')
        
        # 创建索引以提高查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions (account_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions (category_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions (type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_status ON users (status)')
        
        # 创建默认管理员账户（如果不存在）
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            # 使用密码 'admin123' 创建管理员账户
            password_hash = hash_password('admin123')
            cursor.execute('''
            INSERT INTO users (username, password_hash, fullname, email, role, status)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', ('admin', password_hash, '系统管理员', 'admin@example.com', 'admin', 'active'))
            logger.info("创建默认管理员账户成功")
        
        # 创建默认账户
        cursor.execute("SELECT COUNT(*) FROM accounts")
        if cursor.fetchone()[0] == 0:
            default_accounts = [
                ('现金账户', 'cash', 0.0, '日常现金支出'),
                ('银行存款', 'bank', 0.0, '主要银行账户'),
                ('信用卡', 'credit_card', 0.0, '信用卡账户'),
                ('支付宝', 'alipay', 0.0, '支付宝账户'),
                ('微信钱包', 'wechat', 0.0, '微信钱包账户')
            ]
            for name, acc_type, balance, desc in default_accounts:
                cursor.execute('''
                INSERT INTO accounts (name, account_type, balance, description)
                VALUES (?, ?, ?, ?)
                ''', (name, acc_type, balance, desc))
            logger.info("创建默认账户成功")
        
        # 创建默认分类
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            # 收入分类
            income_categories = [
                ('工资', 'income', '💰', '#4CAF50', '工作收入'),
                ('奖金', 'income', '🎁', '#8BC34A', '奖金收入'),
                ('投资收益', 'income', '📈', '#03A9F4', '投资收入'),
                ('其他收入', 'income', '💵', '#FF9800', '其他收入来源')
            ]
            
            # 支出分类
            expense_categories = [
                ('餐饮', 'expense', '🍽️', '#F44336', '日常餐饮支出'),
                ('交通', 'expense', '🚗', '#E91E63', '交通出行支出'),
                ('购物', 'expense', '🛍️', '#9C27B0', '购物支出'),
                ('娱乐', 'expense', '🎬', '#673AB7', '娱乐支出'),
                ('住房', 'expense', '🏠', '#3F51B5', '房租或房贷')
            ]
            
            for name, cat_type, icon, color, desc in income_categories + expense_categories:
                cursor.execute('''
                INSERT INTO categories (name, type, icon, color, description)
                VALUES (?, ?, ?, ?, ?)
                ''', (name, cat_type, icon, color, desc))
            logger.info("创建默认分类成功")
        
        # 创建默认系统配置
        cursor.execute("SELECT COUNT(*) FROM system_configs")
        if cursor.fetchone()[0] == 0:
            default_configs = [
                ('company_name', '个人财务管理系统', 'string', '公司或个人名称'),
                ('currency', '¥', 'string', '货币符号'),
                ('currency_code', 'CNY', 'string', '货币代码'),
                ('decimal_places', '2', 'integer', '小数位数'),
                ('date_format', 'YYYY-MM-DD', 'string', '日期格式'),
                ('time_format', '24h', 'string', '时间格式'),
                ('theme', 'light', 'string', '系统主题'),
                ('auto_backup', 'true', 'boolean', '是否自动备份'),
                ('backup_interval', '7', 'integer', '备份间隔（天）'),
                ('last_backup', '', 'string', '最后备份时间')
            ]
            for config_key, config_value, config_type, description in default_configs:
                cursor.execute('''
                INSERT INTO system_configs (config_key, config_value, config_type, description)
                VALUES (?, ?, ?, ?)
                ''', (config_key, config_value, config_type, description))
            logger.info("创建默认系统配置成功")
        
        # 提交并关闭连接
        conn.commit()
        conn.close()
        logger.info("数据库初始化成功")
        return True
    
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        return False

@handle_errors('DBManager', fallback_return=None)
def execute_query(query: str, params: Optional[Tuple] = None, 
                 fetch_all: bool = False, fetch: bool = False) -> Any:
    """
    执行SQL查询
    
    Args:
        query: SQL查询语句
        params: 查询参数
        fetch_all: 是否返回所有记录
        fetch: 是否返回单条记录（兼容旧代码）
        
    Returns:
        查询结果或影响的行数
    """
    # 兼容旧代码：如果fetch=True，则自动设置fetch_all=False
    if fetch:
        fetch_all = False
    conn = None
    try:
        conn = sqlite3.connect(
            DB_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row  # 返回字典形式的结果
        cursor = conn.cursor()
        
        # 记录SQL查询日志
        if query.strip().upper().startswith('SELECT'):
            log_debug('DBManager', f"执行查询: {query} 参数: {params}")
        else:
            log_info('DBManager', f"执行SQL: {query} 参数: {params}")
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        
        if fetch_all:
            results = cursor.fetchall()
            return [dict(row) for row in results]
        elif fetch:
            # 兼容旧代码，当fetch=True时返回单条记录
            result = cursor.fetchone()
            return dict(result) if result else None
        else:
            return cursor.rowcount
            
    except sqlite3.Error as e:
        # 回滚事务
        if conn:
            conn.rollback()
        
        error_msg = f"数据库操作失败: {str(e)}"
        log_error('DBManager', error_msg)
        log_error('DBManager', f"失败的查询: {query}")
        log_error('DBManager', f"参数: {params}")
        
        # 抛出更具描述性的异常
        raise DatabaseError(error_msg, original_exception=e)
        
    finally:
        # 关闭连接
        if conn:
            conn.close()

@handle_errors('DBManager')
def log_operation(user_id: Optional[int], action: str, details: str, 
                 ip_address: Optional[str] = None, success: bool = True) -> None:
    """
    记录操作日志
    
    Args:
        user_id: 用户ID
        action: 操作类型
        details: 操作详情
        ip_address: IP地址
        success: 操作是否成功
    """
    try:
        log_data = {
            'user_id': user_id,
            'operation_type': action,
            'operation_desc': details,
            'ip_address': ip_address,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 过滤掉None值
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # 构建SQL语句
        columns = ', '.join(log_data.keys())
        placeholders = ', '.join(['?' for _ in log_data.keys()])
        query = f"INSERT INTO operation_logs ({columns}) VALUES ({placeholders})"
        
        execute_query(query, tuple(log_data.values()))
        log_info('DBManager', f"记录操作日志: 用户 {user_id} - {action}")
    except Exception as e:
        log_error('DBManager', f"记录操作日志失败: {str(e)}")

@handle_errors('DBManager', fallback_return=None)
def backup_database(backup_path: Optional[str] = None) -> str:
    """
    备份数据库
    
    Args:
        backup_path: 备份路径，如果不提供则使用默认路径
        
    Returns:
        备份文件路径
    """
    try:
        # 确保备份目录存在
        if not backup_path:
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # 生成带时间戳的备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'finance_system_backup_{timestamp}.db')
        
        # 关闭所有可能的连接
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("VACUUM")
            conn.close()
        except:
            if conn:
                conn.close()
        
        # 复制数据库文件
        shutil.copy2(DB_PATH, backup_path)
        
        # 更新最后备份时间
        update_system_config('last_backup', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        log_info('DBManager', f"数据库备份成功: {backup_path}")
        return backup_path
        
    except Exception as e:
        log_error('DBManager', f"数据库备份失败: {str(e)}")
        raise DatabaseError(f"数据库备份失败: {str(e)}", original_exception=e)

@handle_errors('DBManager', fallback_return=False)
def restore_database(backup_file: str) -> bool:
    """
    恢复数据库
    
    Args:
        backup_file: 备份文件路径
        
    Returns:
        是否恢复成功
    """
    try:
        # 验证备份文件是否存在
        if not os.path.exists(backup_file):
            error_msg = f"备份文件不存在: {backup_file}"
            log_error('DBManager', error_msg)
            return False
        
        # 创建临时备份，以防恢复失败
        temp_backup = DB_PATH + '.temp'
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, temp_backup)
        
        # 关闭所有可能的连接
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.close()
        except:
            pass
        
        # 复制备份文件到数据库路径
        shutil.copy2(backup_file, DB_PATH)
        
        # 验证数据库是否可用
        try:
            test_conn = sqlite3.connect(DB_PATH)
            test_conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            test_conn.close()
            log_info('DBManager', f"数据库恢复成功: {backup_file}")
            
            # 删除临时备份
            if os.path.exists(temp_backup):
                os.remove(temp_backup)
                
            return True
            
        except Exception as e:
            log_error('DBManager', f"数据库验证失败，恢复原数据库: {str(e)}")
            # 恢复原数据库
            if os.path.exists(temp_backup):
                shutil.copy2(temp_backup, DB_PATH)
                os.remove(temp_backup)
            raise DatabaseError(f"数据库恢复失败: {str(e)}", original_exception=e)
            
    except Exception as e:
        log_error('DBManager', f"数据库恢复失败: {str(e)}")
        # 清理临时文件
        if 'temp_backup' in locals() and os.path.exists(temp_backup):
            os.remove(temp_backup)
        raise DatabaseError(f"数据库恢复失败: {str(e)}", original_exception=e)

def get_database_path() -> str:
    """
    获取数据库文件路径
    
    Returns:
        数据库文件路径
    """
    return DB_PATH

def close_database_connections():
    """
    关闭所有数据库连接（清理资源）
    """
    try:
        # SQLite自动管理连接，这里主要是做一些资源清理
        logger.info("数据库连接已清理")
    except Exception as e:
        logger.error(f"清理数据库连接失败: {str(e)}")

def get_system_config(config_key: str) -> Any:
    """
    获取系统配置
    
    Args:
        config_key: 配置键
        
    Returns:
        配置值
    """
    try:
        query = "SELECT config_value, config_type FROM system_configs WHERE config_key = ?"
        result = execute_query(query, (config_key,), fetch_all=False)
        
        if result:
            value = result['config_value']
            config_type = result['config_type']
            
            # 根据类型转换值
            if config_type == 'integer':
                return int(value)
            elif config_type == 'boolean':
                return value.lower() == 'true'
            elif config_type == 'json':
                return json.loads(value)
            else:
                return value
        
        return None
        
    except Exception as e:
        logger.error(f"获取系统配置失败: {str(e)}")
        return None

def update_system_config(config_key: str, config_value: Any) -> bool:
    """
    更新系统配置
    
    Args:
        config_key: 配置键
        config_value: 配置值
        
    Returns:
        是否更新成功
    """
    try:
        # 检查配置是否存在
        query = "SELECT id FROM system_configs WHERE config_key = ?"
        result = execute_query(query, (config_key,), fetch_all=False)
        
        # 确定值的类型
        config_type = 'string'
        if isinstance(config_value, bool):
            config_value = str(config_value).lower()
            config_type = 'boolean'
        elif isinstance(config_value, int):
            config_value = str(config_value)
            config_type = 'integer'
        elif isinstance(config_value, (dict, list)):
            config_value = json.dumps(config_value)
            config_type = 'json'
        else:
            config_value = str(config_value)
        
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if result:
            # 更新现有配置
            query = """
            UPDATE system_configs 
            SET config_value = ?, config_type = ?, updated_at = ? 
            WHERE config_key = ?
            """
            execute_query(query, (config_value, config_type, updated_at, config_key))
        else:
            # 添加新配置
            query = """
            INSERT INTO system_configs (config_key, config_value, config_type, updated_at)
            VALUES (?, ?, ?, ?)
            """
            execute_query(query, (config_key, config_value, config_type, updated_at))
        
        logger.info(f"系统配置更新成功: {config_key}")
        return True
        
    except Exception as e:
        logger.error(f"更新系统配置失败: {str(e)}")
        return False

def hash_password(password: str) -> str:
    """
    对密码进行哈希处理
    
    Args:
        password: 原始密码
        
    Returns:
        哈希后的密码
    """
    # 使用SHA-256进行哈希
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return hashed

def verify_password(stored_hash: str, provided_password: str) -> bool:
    """
    验证密码
    
    Args:
        stored_hash: 存储的哈希值
        provided_password: 提供的密码
        
    Returns:
        密码是否匹配
    """
    # 对提供的密码进行哈希并比较
    return stored_hash == hash_password(provided_password)

    @handle_errors(error_types=[DatabaseError])
    def close(self):
        """
        关闭数据库连接
        """
        if self._conn is not None:
            try:
                self._conn.close()
                self._conn = None
                self.logger.info("数据库连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭数据库连接失败: {str(e)}")
                raise DatabaseError(f"关闭数据库连接失败: {str(e)}")
    
    @handle_errors(error_types=[DatabaseError])
    def create_backup(self, description: str = "manual_backup") -> str:
        """
        创建数据库备份
        
        Args:
            description: 备份描述
            
        Returns:
            str: 备份文件路径
            
        Raises:
            DatabaseError: 备份失败时抛出
        """
        # 确保数据库连接已关闭，避免文件锁定
        was_open = self._conn is not None
        if was_open:
            self.close()
        
        try:
            backup_path = self.backup_manager.create_backup(description)
            self.logger.info(f"数据库备份成功: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"数据库备份失败: {str(e)}")
            raise DatabaseError(f"数据库备份失败: {str(e)}")
        finally:
            # 如果之前连接是打开的，重新打开连接
            if was_open:
                self._get_connection()
    
    @handle_errors(error_types=[DatabaseError])
    def restore_from_backup(self, backup_path: str, overwrite: bool = True) -> bool:
        """
        从备份恢复数据库
        
        Args:
            backup_path: 备份文件路径
            overwrite: 是否覆盖现有数据库
            
        Returns:
            bool: 恢复是否成功
            
        Raises:
            DatabaseError: 恢复失败时抛出
        """
        # 确保数据库连接已关闭，避免文件锁定
        was_open = self._conn is not None
        if was_open:
            self.close()
        
        try:
            success = self.backup_manager.restore_from_backup(backup_path, overwrite)
            self.logger.info(f"数据库恢复{'成功' if success else '失败'}: 从 {backup_path} 恢复到 {self.db_path}")
            return success
        except Exception as e:
            self.logger.error(f"数据库恢复失败: {str(e)}")
            raise DatabaseError(f"数据库恢复失败: {str(e)}")
        finally:
            # 如果之前连接是打开的，重新打开连接
            if was_open:
                self._get_connection()
    
    @handle_errors(error_types=[DatabaseError])
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的备份文件
        
        Returns:
            List[Dict]: 备份文件信息列表
        """
        try:
            backups = self.backup_manager.list_backups()
            self.logger.info(f"找到 {len(backups)} 个备份文件")
            return backups
        except Exception as e:
            self.logger.error(f"列出备份文件失败: {str(e)}")
            raise DatabaseError(f"列出备份文件失败: {str(e)}")
    
    @handle_errors(error_types=[DatabaseError])
    def delete_backup(self, backup_path: str) -> bool:
        """
        删除指定的备份文件
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            success = self.backup_manager.delete_backup(backup_path)
            self.logger.info(f"备份文件{'已删除' if success else '删除失败'}: {backup_path}")
            return success
        except Exception as e:
            self.logger.error(f"删除备份文件失败: {str(e)}")
            raise DatabaseError(f"删除备份文件失败: {str(e)}")
    
    @handle_errors(error_types=[DatabaseError])
    def cleanup_old_backups(self, days: int = 7, keep_min: int = 5) -> int:
        """
        清理过期的备份文件
        
        Args:
            days: 保留最近多少天的备份
            keep_min: 至少保留多少个备份文件
            
        Returns:
            int: 删除的备份文件数量
        """
        try:
            deleted_count = self.backup_manager.cleanup_old_backups(days, keep_min)
            self.logger.info(f"备份清理完成，删除了 {deleted_count} 个过期备份文件")
            return deleted_count
        except Exception as e:
            self.logger.error(f"清理备份文件失败: {str(e)}")
            raise DatabaseError(f"清理备份文件失败: {str(e)}")
    
    @handle_errors(error_types=[DatabaseError])
    def start_auto_backup(self, interval_hours: float = 24, description: str = "auto_backup"):
        """
        启动自动备份
        
        Args:
            interval_hours: 备份间隔（小时）
            description: 备份描述
        """
        try:
            self.backup_manager.start_auto_backup(interval_hours, description)
            self.logger.info(f"自动备份已启动: 间隔 {interval_hours} 小时")
        except Exception as e:
            self.logger.error(f"启动自动备份失败: {str(e)}")
            raise DatabaseError(f"启动自动备份失败: {str(e)}")
    
    @handle_errors(error_types=[DatabaseError])
    def stop_auto_backup(self):
        """
        停止自动备份
        """
        try:
            self.backup_manager.stop_auto_backup()
            self.logger.info("自动备份已停止")
        except Exception as e:
            self.logger.error(f"停止自动备份失败: {str(e)}")
            raise DatabaseError(f"停止自动备份失败: {str(e)}")
    
    def is_auto_backup_running(self) -> bool:
        """
        检查自动备份是否正在运行
        
        Returns:
            bool: 自动备份是否运行中
        """
        return self.backup_manager.is_auto_backup_running()
    
    def _get_connection(self):
        """获取数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self._conn.row_factory = sqlite3.Row
        return self._conn

# 创建数据库管理器实例
db_manager = DatabaseManager()

# 本地备选数据库连接（当无法导入其他模块时使用）
class LocalDBConnection:
    """本地数据库连接类"""
    
    def __init__(self):
        self.db_path = DB_PATH
    


# 创建本地数据库连接实例
local_db = LocalDBConnection()

# 扩展DatabaseManager类的方法
DatabaseManager.start_auto_backup = lambda self, interval_hours=24: self._start_auto_backup(interval_hours)

def _start_auto_backup(self, interval_hours: int = 24):
    """
    启动自动备份任务
    
    Args:
        interval_hours: 备份间隔（小时）
    """
    if hasattr(self.backup_manager, 'start_auto_backup'):
        self.backup_manager.start_auto_backup(interval_hours)
    else:
        # 创建简单的自动备份支持
        import threading
        import time
        
        def auto_backup_task():
            while True:
                try:
                    time.sleep(interval_hours * 3600)
                    backup_file = self.backup_database()
                    self.logger.info(f"自动备份完成: {backup_file}")
                except Exception as e:
                    self.logger.error(f"自动备份失败: {str(e)}")
        
        thread = threading.Thread(target=auto_backup_task, daemon=True)
        thread.start()
        self._auto_backup_thread = thread

# 将_start_auto_backup函数绑定到DatabaseManager类
DatabaseManager._start_auto_backup = _start_auto_backup

# 全局函数

def get_db_path():
    """
    获取数据库路径
    
    Returns:
        str: 数据库文件路径
    """
    global db_manager
    if db_manager:
        return db_manager.db_path
    return DB_PATH

def execute_query(query: str, params: Optional[Tuple] = None, 
                fetch_all: bool = True) -> List[Dict]:
    """
    执行SQL查询的便捷函数
    
    Args:
        query: SQL查询语句
        params: 查询参数
        fetch_all: 是否返回所有记录
    
    Returns:
        查询结果列表或单条记录
    """
    global db_manager
    # 根据fetch_all参数决定是返回单条记录还是所有记录
    return db_manager.execute(query, params, fetch=not fetch_all, fetch_all=fetch_all)

def backup_database():
    """
    备份数据库
    
    Returns:
        str: 备份文件路径
    """
    global db_manager
    if hasattr(db_manager, 'backup_database'):
        return db_manager.backup_database()
    else:
        # 使用备份管理器进行备份
        return db_manager.backup_manager.create_backup()

# 当直接运行此脚本时，进行数据库初始化
if __name__ == "__main__":
    print("开始初始化数据库...")
    if init_db():
        print("数据库初始化成功！")
    else:
        print("数据库初始化失败！")
        
    # 测试备份功能
    try:
        backup_file = backup_database()
        print(f"数据库备份成功: {backup_file}")
    except Exception as e:
        print(f"数据库备份失败: {str(e)}")
