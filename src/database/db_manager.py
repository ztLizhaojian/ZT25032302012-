#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块 - 作为数据访问层的统一接口
集成了数据库连接、初始化、查询执行等功能
"""

import os
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("db.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("DBManager")

# 导入数据访问层组件
try:
    from src.database.db_access import (
        get_db_access, close_db_access, execute_query as db_execute_query,
        insert_record, update_record, delete_record, select_records
    )
    from src.database.db_migration import init_database
    DATABASE_ACCESS_READY = True
except ImportError as e:
    logger.error(f"导入数据访问层组件失败: {str(e)}")
    logger.warning("将使用本地数据库访问实现作为备选")
    DATABASE_ACCESS_READY = False

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                      'data', 'finance_system.db')


def init_db(db_path=None):
    """
    初始化数据库
    
    Args:
        db_path: 数据库文件路径，如果不提供则使用默认路径
        
    Returns:
        bool: 初始化是否成功
    """
    global DB_PATH
    
    # 如果提供了自定义路径，则使用它
    if db_path:
        DB_PATH = db_path
    
    try:
        # 确保数据目录存在
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # 使用新的数据访问层进行初始化
        if DATABASE_ACCESS_READY:
            init_database(DB_PATH)
        else:
            # 备选方案：使用本地实现
            _local_init_database()
        
        logger.info(f"数据库初始化成功: {DB_PATH}")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        return False


def execute_query(query, params=None, fetch=False, fetchall=False):
    """
    执行SQL查询
    
    Args:
        query: SQL查询语句
        params: 查询参数
        fetch: 是否返回单条结果
        fetchall: 是否返回所有结果
        
    Returns:
        根据fetch和fetchall参数返回查询结果
    """
    try:
        # 使用新的数据访问层执行查询
        if DATABASE_ACCESS_READY:
            return db_execute_query(query, params, fetch, fetchall)
        else:
            # 备选方案：使用本地实现
            return _local_execute_query(query, params, fetch, fetchall)
            
    except Exception as e:
        logger.error(f"执行查询失败: {str(e)}")
        logger.error(f"查询: {query}")
        logger.error(f"参数: {params}")
        raise


def log_operation(user_id, action, details=None, ip_address=None):
    """
    记录操作日志
    
    Args:
        user_id: 用户ID
        action: 操作类型
        details: 操作详情
        ip_address: IP地址
    """
    try:
        # 使用新的数据访问层记录日志
        if DATABASE_ACCESS_READY:
            db_access = get_db_access()
            if db_access:
                db_access.log_operation(
                    user_id=user_id,
                    operation_type=action,
                    operation_desc=details,
                    ip_address=ip_address
                )
            else:
                # 备选方案：直接插入日志
                execute_query(
                    "INSERT INTO operation_logs (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)",
                    (user_id, action, details, ip_address)
                )
        else:
            # 备选方案：使用本地实现
            _local_execute_query(
                "INSERT INTO operation_logs (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)",
                (user_id, action, details, ip_address)
            )
            
    except Exception as e:
        logger.error(f"记录操作日志失败: {str(e)}")
        # 日志记录失败不应影响主流程


def backup_database(backup_path=None):
    """
    备份数据库
    
    Args:
        backup_path: 备份文件路径，如果不提供则自动生成
        
    Returns:
        备份文件的路径
    """
    # 生成备份路径
    if not backup_path:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成时间戳文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'finance_backup_{timestamp}.db')
    
    # 执行备份
    try:
        # 先关闭数据库连接以确保文件未被锁定
        if DATABASE_ACCESS_READY:
            close_db_access()
        
        # 等待一小段时间确保所有连接都已关闭
        import time
        time.sleep(0.5)
        
        # 使用shutil进行文件复制
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        
        logger.info(f"数据库备份成功: {backup_path}")
        
        # 重新打开数据库连接
        if DATABASE_ACCESS_READY:
            from src.database.db_access import get_db_access
            get_db_access(DB_PATH)
        
        return backup_path
        
    except Exception as e:
        logger.error(f"数据库备份失败: {str(e)}")
        if os.path.exists(backup_path):
            os.remove(backup_path)
        raise


def restore_database(backup_path):
    """
    从备份恢复数据库
    
    Args:
        backup_path: 备份文件路径
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"备份文件不存在: {backup_path}")
    
    # 先创建当前数据库的临时备份
    temp_backup = os.path.join(os.path.dirname(DB_PATH), 
                             f'finance_temp_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    
    try:
        # 先关闭数据库连接以确保文件未被锁定
        if DATABASE_ACCESS_READY:
            close_db_access()
        
        # 等待一小段时间确保所有连接都已关闭
        import time
        time.sleep(0.5)
        
        # 复制当前数据库作为临时备份
        import shutil
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, temp_backup)
        
        # 恢复数据库
        shutil.copy2(backup_path, DB_PATH)
        
        logger.info(f"数据库恢复成功: {backup_path}")
        
        # 重新打开数据库连接
        if DATABASE_ACCESS_READY:
            from src.database.db_access import get_db_access
            get_db_access(DB_PATH)
        
        # 恢复成功后删除临时备份
        if os.path.exists(temp_backup):
            os.remove(temp_backup)
            
    except Exception as e:
        logger.error(f"数据库恢复失败: {str(e)}")
        
        # 恢复失败，尝试恢复到原来的状态
        if os.path.exists(temp_backup):
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            shutil.copy2(temp_backup, DB_PATH)
            logger.info("已恢复到恢复前的数据库状态")
        
        # 重新打开数据库连接
        if DATABASE_ACCESS_READY:
            from src.database.db_access import get_db_access
            get_db_access(DB_PATH)
        
        raise


def get_db_path():
    """
    获取当前数据库路径
    
    Returns:
        str: 数据库文件路径
    """
    return DB_PATH


def close_db():
    """
    关闭数据库连接
    
    Returns:
        bool: 关闭是否成功
    """
    try:
        if DATABASE_ACCESS_READY:
            close_db_access()
        logger.info("数据库连接已关闭")
        return True
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {str(e)}")
        return False


def get_setting(key, default_value=None):
    """
    获取系统设置
    
    Args:
        key: 设置键名
        default_value: 默认值
        
    Returns:
        设置值或默认值
    """
    try:
        result = execute_query(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
            fetch=True
        )
        
        if result:
            return result['value']
        return default_value
        
    except Exception as e:
        logger.error(f"获取系统设置失败: {str(e)}")
        return default_value


def set_setting(key, value, description=None):
    """
    设置系统设置
    
    Args:
        key: 设置键名
        value: 设置值
        description: 设置描述
        
    Returns:
        bool: 设置是否成功
    """
    try:
        # 检查设置是否存在
        existing = execute_query(
            "SELECT id FROM settings WHERE key = ?",
            (key,),
            fetch=True
        )
        
        if existing:
            # 更新设置
            execute_query(
                "UPDATE settings SET value = ?, description = ?, updated_at = ? WHERE id = ?",
                (value, description, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), existing['id'])
            )
        else:
            # 插入新设置
            execute_query(
                "INSERT INTO settings (key, value, description) VALUES (?, ?, ?)",
                (key, value, description)
            )
        
        return True
        
    except Exception as e:
        logger.error(f"设置系统设置失败: {str(e)}")
        return False

# 以下是本地备选实现（当新的数据访问层不可用时）
def _local_get_db_connection():
    """[备选] 获取数据库连接"""
    import sqlite3
    
    # 确保数据目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    # 启用外键约束
    conn.execute("PRAGMA foreign_keys = ON")
    # 设置返回字典格式
    conn.row_factory = sqlite3.Row
    return conn

def _local_init_database():
    """[备选] 初始化数据库"""
    import sqlite3
    
    conn = None
    try:
        conn = _local_get_db_connection()
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            fullname TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        # 创建账户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            currency TEXT DEFAULT 'CNY',
            initial_balance REAL DEFAULT 0.0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建分类表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            parent_id INTEGER,
            icon TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
        ''')
        
        # 创建交易记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'CNY',
            transaction_date TIMESTAMP NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
        ''')
        
        # 创建产品表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT,
            category TEXT,
            cost_price REAL,
            selling_price REAL,
            unit TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建客户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建系统设置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建操作日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # 创建索引以提高查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)')
        
        # 检查是否需要创建默认管理员账户
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            # 创建默认管理员账户 (密码: admin123)
            cursor.execute('''
            INSERT INTO users (username, password, fullname, email, role)
            VALUES (?, ?, ?, ?, ?)
            ''', ('admin', 'admin123', '系统管理员', 'admin@example.com', 'admin'))
        
        # 创建默认账户类型
        cursor.execute('SELECT COUNT(*) FROM accounts')
        if cursor.fetchone()[0] == 0:
            default_accounts = [
                ('现金账户', 'cash', 'CNY', 0.0, '企业现金账户'),
                ('银行存款', 'bank', 'CNY', 0.0, '企业银行存款账户'),
                ('应收账款', 'receivable', 'CNY', 0.0, '客户应收账款'),
                ('应付账款', 'payable', 'CNY', 0.0, '供应商应付账款')
            ]
            cursor.executemany('''
            INSERT INTO accounts (name, type, currency, initial_balance, description)
            VALUES (?, ?, ?, ?, ?)
            ''', default_accounts)
        
        # 创建默认分类
        cursor.execute('SELECT COUNT(*) FROM categories')
        if cursor.fetchone()[0] == 0:
            # 收入分类
            income_categories = [
                ('主营业务收入', 'income', None, '💰'),
                ('其他业务收入', 'income', None, '💵'),
                ('投资收益', 'income', None, '📈'),
                ('营业外收入', 'income', None, '🎁')
            ]
            cursor.executemany('''
            INSERT INTO categories (name, type, parent_id, icon)
            VALUES (?, ?, ?, ?)
            ''', income_categories)
            
            # 支出分类
            expense_categories = [
                ('主营业务成本', 'expense', None, '📦'),
                ('营业费用', 'expense', None, '🏢'),
                ('管理费用', 'expense', None, '⚙️'),
                ('财务费用', 'expense', None, '💸'),
                ('营业外支出', 'expense', None, '❌')
            ]
            cursor.executemany('''
            INSERT INTO categories (name, type, parent_id, icon)
            VALUES (?, ?, ?, ?)
            ''', expense_categories)
        
        # 创建默认系统设置
        cursor.execute('SELECT COUNT(*) FROM settings')
        if cursor.fetchone()[0] == 0:
            default_settings = [
                ('company_name', '示例企业', '企业名称'),
                ('default_currency', 'CNY', '默认货币'),
                ('decimal_places', '2', '小数位数'),
                ('fiscal_year_start', '01-01', '财年开始日期'),
                ('auto_backup', 'true', '自动备份'),
                ('backup_interval', '7', '备份间隔(天)'),
                ('theme', 'light', '系统主题')
            ]
            cursor.executemany('''
            INSERT INTO settings (key, value, description)
            VALUES (?, ?, ?)
            ''', default_settings)
        
        # 提交事务
        conn.commit()
        logger.info("本地数据库初始化成功")
        
    except Exception as e:
        logger.error(f"本地数据库初始化失败: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def _local_execute_query(query, params=None, fetch=False, fetchall=False):
    """[备选] 执行SQL查询"""
    import sqlite3
    
    conn = None
    try:
        conn = _local_get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # 对于INSERT/UPDATE/DELETE操作，返回受影响的行数
        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            conn.commit()
            return cursor.rowcount
        
        # 对于SELECT操作，根据参数返回结果
        elif query.strip().upper().startswith('SELECT'):
            if fetchall:
                return cursor.fetchall()
            elif fetch:
                return cursor.fetchone()
            else:
                return cursor
        
        conn.commit()
        return None
        
    except sqlite3.Error as e:
        logger.error(f"本地数据库查询执行失败: {str(e)}")
        logger.error(f"查询: {query}")
        logger.error(f"参数: {params}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # 直接运行时初始化数据库
    init_db()
    print(f"数据库已初始化: {DB_PATH}")