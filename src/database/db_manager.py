#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# 数据库管理模块 - 作为数据访问层的统一接口
集成了数据库连接、初始化、查询执行等功能
"""

import os
from datetime import datetime
import logging

# 添加项目根目录到Python路径
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.security import hash_password

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
        
        # 创建用户表（与db_migration.py保持一致）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            fullname TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT
        )
        ''')
        
        # 创建账户表（与db_migration.py保持一致）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            currency TEXT DEFAULT 'CNY',
            balance REAL DEFAULT 0.0,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建分类表（与db_migration.py保持一致）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_type TEXT NOT NULL,
            parent_id INTEGER,
            icon TEXT DEFAULT 'default',
            color TEXT DEFAULT '#007bff',
            description TEXT,
            is_system INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
        ''')
        
        # 创建交易记录表（与db_migration.py保持一致）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            account_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            transaction_date TEXT NOT NULL,
            description TEXT,
            receipt_number TEXT,
            payment_method TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
        ''')
        
        # 创建预算表（与db_migration.py保持一致）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            period TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
        ''')
        
        # 创建附件表（与db_migration.py保持一致）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_size INTEGER,
            file_type TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id)
        )
        ''')
        
        # 创建系统配置表（与db_migration.py保持一致）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT NOT NULL UNIQUE,
            config_value TEXT,
            config_type TEXT DEFAULT 'string',
            description TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建操作日志表（与db_migration.py保持一致）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            operation_type TEXT NOT NULL,
            operation_desc TEXT,
            operation_table TEXT,
            operation_data TEXT,
            ip_address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # 创建索引以提高查询性能（与db_migration.py保持一致）
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(category_type)")
        
        # 检查是否需要创建默认管理员账户（与db_migration.py保持一致）
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            # 创建默认管理员用户，使用哈希处理的密码
            admin_password = 'admin123'
            hashed_password = hash_password(admin_password)
            cursor.execute('''
            INSERT INTO users (username, password, fullname, email, role)
            VALUES (?, ?, ?, ?, ?)
            ''', ('admin', hashed_password, '系统管理员', 'admin@example.com', 'admin'))
        
        # 创建默认账户（与db_migration.py保持一致）
        cursor.execute('SELECT COUNT(*) FROM accounts')
        if cursor.fetchone()[0] == 0:
            default_accounts = [
                ('现金账户', 'asset', 0.0, '主要用于记录现金收支', 'active'),
                ('银行存款', 'asset', 0.0, '主要用于记录银行账户收支', 'active'),
                ('应收账款', 'asset', 0.0, '记录客户欠款', 'active'),
                ('应付账款', 'liability', 0.0, '记录欠供应商款项', 'active'),
                ('股本', 'equity', 0.0, '记录公司注册资本', 'active')
            ]
            
            cursor.executemany('''
            INSERT INTO accounts (name, account_type, balance, description, status)
            VALUES (?, ?, ?, ?, ?)
            ''', default_accounts)
        
        # 创建默认分类（与db_migration.py保持一致）
        cursor.execute('SELECT COUNT(*) FROM categories')
        if cursor.fetchone()[0] == 0:
            # 创建默认收入分类
            income_categories = [
                ('主营业务收入', 'income', None, '💰', '#28a745', 'default', '销售商品或提供服务的收入', 1),
                ('其他业务收入', 'income', None, '💵', '#20c997', 'default', '非主营业务的收入', 1),
                ('投资收益', 'income', None, '📈', '#6f42c1', 'default', '投资获得的收益', 1),
                ('营业外收入', 'income', None, '🎁', '#ffc107', 'default', '与生产经营无直接关系的收入', 1)
            ]
            
            for category in income_categories:
                cursor.execute('''
                INSERT INTO categories (name, category_type, parent_id, icon, color, description, is_system)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', category)
            
            # 创建默认支出分类
            expense_categories = [
                ('主营业务成本', 'expense', None, '📦', '#dc3545', 'default', '销售商品或提供服务的成本', 1),
                ('销售费用', 'expense', None, '🏢', '#fd7e14', 'default', '销售过程中发生的各项费用', 1),
                ('管理费用', 'expense', None, '⚙️', '#17a2b8', 'default', '企业管理部门发生的费用', 1),
                ('财务费用', 'expense', None, '💸', '#6c757d', 'default', '筹集生产经营所需资金等发生的费用', 1),
                ('营业外支出', 'expense', None, '❌', '#343a40', 'default', '与生产经营无直接关系的支出', 1)
            ]
            
            for category in expense_categories:
                cursor.execute('''
                INSERT INTO categories (name, category_type, parent_id, icon, color, description, is_system)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', category)
        
        # 创建默认系统配置（与db_migration.py保持一致）
        cursor.execute('SELECT COUNT(*) FROM system_configs')
        if cursor.fetchone()[0] == 0:
            default_configs = [
                ('company_name', '未设置公司名称', 'string', '公司名称'),
                ('currency', 'CNY', 'string', '默认货币'),
                ('decimal_places', '2', 'integer', '小数位数'),
                ('auto_backup', 'true', 'boolean', '自动备份'),
                ('backup_frequency', 'daily', 'string', '备份频率'),
                ('language', 'zh_CN', 'string', '系统语言'),
                ('theme', 'light', 'string', '系统主题'),
                ('default_period', 'month', 'string', '默认报表周期'),
                ('data_retention_days', '365', 'integer', '数据保留天数'),
                ('log_level', 'INFO', 'string', '日志级别')
            ]
            
            cursor.executemany('''
            INSERT INTO system_configs (config_key, config_value, config_type, description)
            VALUES (?, ?, ?, ?)
            ''', default_configs)
        
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