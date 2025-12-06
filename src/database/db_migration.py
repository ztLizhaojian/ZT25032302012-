# 数据库迁移工具
import json
import os
import sqlite3
import logging
from datetime import datetime

from src.utils.logger import get_logger, log_error, handle_errors, DatabaseError

# 迁移相关的异常类
class MigrationError(DatabaseError):
    """数据库迁移异常"""
    def __init__(self, message: str, migration_id: str = None, original_exception: Exception = None):
        self.migration_id = migration_id
        if migration_id:
            message = f"迁移 {migration_id} 失败: {message}"
        super().__init__(message, error_code=500, original_exception=original_exception)
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.security import hash_password

# 定义迁移记录表名
MIGRATIONS_TABLE = "db_migrations"

# 定义版本化的迁移脚本
VERSION_MIGRATIONS = [
    # 版本 1 - 初始数据库结构
    {
        'version': 1,
        'description': 'Initial database structure',
        'upgrade': [
            # 这里是初始表结构，将在initialize_database中实现
        ],
        'downgrade': [
            # 删除所有表（按外键依赖关系倒序）
            'DROP TABLE IF EXISTS transaction_drafts',
            'DROP TABLE IF EXISTS attachments',
            'DROP TABLE IF EXISTS budgets',
            'DROP TABLE IF EXISTS transactions',
            'DROP TABLE IF EXISTS operation_logs',
            'DROP TABLE IF EXISTS system_configs',
            'DROP TABLE IF EXISTS categories',
            'DROP TABLE IF EXISTS accounts',
            'DROP TABLE IF EXISTS users',
            'DROP TABLE IF EXISTS db_migrations'
        ]
    },
    # 版本 2 - 添加账户余额字段的更新触发器
    {
        'version': 2,
        'description': 'Add account balance update triggers',
        'upgrade': [
            # 创建插入交易时更新账户余额的触发器
            '''
            CREATE TRIGGER IF NOT EXISTS update_account_balance_after_insert
            AFTER INSERT ON transactions
            BEGIN
                UPDATE accounts
                SET balance = CASE
                    WHEN NEW.transaction_type = 'income' THEN balance + NEW.amount
                    WHEN NEW.transaction_type = 'expense' THEN balance - NEW.amount
                    ELSE balance
                END,
                updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.account_id;
            END
            ''',
            # 创建更新交易时更新账户余额的触发器
            '''
            CREATE TRIGGER IF NOT EXISTS update_account_balance_after_update
            AFTER UPDATE ON transactions
            BEGIN
                -- 先恢复旧交易对账户余额的影响
                UPDATE accounts
                SET balance = CASE
                    WHEN OLD.transaction_type = 'income' THEN balance - OLD.amount
                    WHEN OLD.transaction_type = 'expense' THEN balance + OLD.amount
                    ELSE balance
                END
                WHERE id = OLD.account_id;
                
                -- 再应用新交易对账户余额的影响
                UPDATE accounts
                SET balance = CASE
                    WHEN NEW.transaction_type = 'income' THEN balance + NEW.amount
                    WHEN NEW.transaction_type = 'expense' THEN balance - NEW.amount
                    ELSE balance
                END,
                updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.account_id;
            END
            ''',
            # 创建删除交易时更新账户余额的触发器
            '''
            CREATE TRIGGER IF NOT EXISTS update_account_balance_after_delete
            AFTER DELETE ON transactions
            BEGIN
                UPDATE accounts
                SET balance = CASE
                    WHEN OLD.transaction_type = 'income' THEN balance - OLD.amount
                    WHEN OLD.transaction_type = 'expense' THEN balance + OLD.amount
                    ELSE balance
                END,
                updated_at = CURRENT_TIMESTAMP
                WHERE id = OLD.account_id;
            END
            '''
        ],
        'downgrade': [
            'DROP TRIGGER IF EXISTS update_account_balance_after_insert',
            'DROP TRIGGER IF EXISTS update_account_balance_after_update',
            'DROP TRIGGER IF EXISTS update_account_balance_after_delete'
        ]
    },
    # 版本 3 - 为交易表添加更多索引以提高查询性能
    {
        'version': 3,
        'description': 'Add more indexes for better performance',
        'upgrade': [
            'CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions (created_at)',
            'CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions (amount)',
            'CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets (period)',
            'CREATE INDEX IF NOT EXISTS idx_operation_logs_created_at ON operation_logs (created_at)',
            'CREATE INDEX IF NOT EXISTS idx_operation_logs_user_id ON operation_logs (user_id)'
        ],
        'downgrade': [
            'DROP INDEX IF EXISTS idx_transactions_created_at',
            'DROP INDEX IF EXISTS idx_transactions_amount',
            'DROP INDEX IF EXISTS idx_budgets_period',
            'DROP INDEX IF EXISTS idx_operation_logs_created_at',
            'DROP INDEX IF EXISTS idx_operation_logs_user_id'
        ]
    }
]

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("db_migration.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("DBMigration")




class DBMigration:
    """数据库迁移管理类"""
    
    def __init__(self, db_path):
        """
        初始化迁移管理器
        
        Args:
            db_path: 数据库文件路径
        """
        # 使用自定义日志函数
        self.logger = get_logger('db_migration')
        
        self.db_path = db_path
        self.migrations_dir = os.path.join(os.path.dirname(db_path), "migrations")
        self.migration_history = os.path.join(self.migrations_dir, "history.json")
        
        try:
            # 确保迁移目录存在
            if not os.path.exists(self.migrations_dir):
                os.makedirs(self.migrations_dir)
                self.logger.info(f"创建迁移目录: {self.migrations_dir}")
            
            # 确保迁移历史文件存在（兼容旧版本）
            if not os.path.exists(self.migration_history):
                with open(self.migration_history, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                    self.logger.info(f"创建迁移历史文件: {self.migration_history}")
        except Exception as e:
            raise DatabaseError(f"初始化迁移管理器失败: {str(e)}")
        
        # 确保数据库中的迁移记录表存在
        self._ensure_migrations_table()
    
    @handle_errors('db_migration')
    def get_connection(self):
        """
        获取数据库连接
        
        Returns:
            sqlite3.Connection: 数据库连接对象
            
        Raises:
            DatabaseError: 数据库连接失败时抛出
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            error_msg = f"获取数据库连接失败: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def _ensure_migrations_table(self):
        """
        确保迁移记录表存在
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 创建迁移记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS {} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL UNIQUE,
                description TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                migration_data TEXT
            )
            '''.format(MIGRATIONS_TABLE))
            
            conn.commit()
            conn.close()
            logger.info("迁移记录表检查完成")
            
        except Exception as e:
            logger.error(f"创建迁移记录表失败: {str(e)}")
            
    def _add_transaction_indexes(self, cursor):
        """
        为transactions表添加索引以提高查询性能
        
        Args:
            cursor: 数据库游标对象
        """
        try:
            # 为常用查询字段添加索引
            # 按日期范围查询的索引
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date 
            ON transactions(transaction_date)
            """)
            
            # 按账户查询的索引
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_account 
            ON transactions(account_id)
            """)
            
            # 按分类查询的索引
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_category 
            ON transactions(category_id)
            """)
            
            # 按交易类型查询的索引
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_type 
            ON transactions(transaction_type)
            """)
            
            # 复合索引：按日期和账户查询（常用于报表）
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date_account 
            ON transactions(transaction_date, account_id)
            """)
            
            # 复合索引：按日期和分类查询（常用于报表）
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date_category 
            ON transactions(transaction_date, category_id)
            """)
            
        except Exception as e:
            logger.error(f"添加交易表索引失败: {str(e)}")
    
    def get_current_version(self) -> int:
        """
        获取当前数据库版本
        
        Returns:
            当前数据库版本号
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查迁移记录表是否存在
            cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name=?
            ''', (MIGRATIONS_TABLE,))
            
            if not cursor.fetchone():
                conn.close()
                return 0
            
            # 获取最大版本号
            cursor.execute(f"SELECT MAX(version) FROM {MIGRATIONS_TABLE}")
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result[0] is not None else 0
            
        except Exception as e:
            logger.error(f"获取当前数据库版本失败: {str(e)}")
            return 0
    
    def get_latest_version(self) -> int:
        """
        获取最新的迁移版本
        
        Returns:
            最新的版本号
        """
        if not VERSION_MIGRATIONS:
            return 0
        return max(migration['version'] for migration in VERSION_MIGRATIONS)
    
    @handle_errors('db_migration', fallback_return=[])
    def get_migration_history(self):
        """
        获取已执行的迁移记录
        
        Returns:
            list: 迁移历史记录列表
        """
        try:
            with open(self.migration_history, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            error_msg = f"读取迁移历史失败: {str(e)}"
            self.logger.error(error_msg)
            return []
    
    @handle_errors('db_migration')
    def save_migration_history(self, history):
        """
        保存迁移历史
        
        Args:
            history: 迁移历史记录列表
            
        Raises:
            DatabaseError: 保存失败时抛出
        """
        try:
            with open(self.migration_history, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                self.logger.info(f"保存迁移历史成功")
        except IOError as e:
            error_msg = f"保存迁移历史失败: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def initialize_database(self):
        """初始化数据库，创建必要的表结构"""
        logger.info("开始初始化数据库...")
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 首先确保迁移表存在
            self._ensure_migrations_table()
            
            # 1. 创建用户表
            cursor.execute("""
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
            """)
            logger.info("创建users表成功")
            
            # 2. 创建账户表
            cursor.execute("""
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
            """)
            logger.info("创建accounts表成功")
            
            # 3. 创建分类表
            cursor.execute("""
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
            """)
            logger.info("创建categories表成功")
            
            # 4. 创建交易记录表
            cursor.execute("""
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
                reconciliation_flag INTEGER DEFAULT 0,
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """)
            logger.info("创建transactions表成功")
            
            # 为transactions表添加索引以提高查询性能
            self._add_transaction_indexes(cursor)
            logger.info("为transactions表添加索引成功")
            
            # 5. 创建预算表
            cursor.execute("""
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
            """)
            logger.info("创建budgets表成功")
            
            # 6. 创建附件表
            cursor.execute("""
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
            """)
            logger.info("创建attachments表成功")
            
            # 7. 创建系统配置表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT NOT NULL UNIQUE,
                config_value TEXT,
                config_type TEXT DEFAULT 'string',
                description TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)
            logger.info("创建system_configs表成功")
            
            # 8. 创建操作日志表
            cursor.execute("""
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
            """)
            logger.info("创建operation_logs表成功")
            
            # 9. 创建交易草稿表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaction_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_type TEXT,
                account_id INTEGER,
                category_id INTEGER,
                amount REAL,
                transaction_date TEXT,
                description TEXT,
                reference_number TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
            """)
            logger.info("创建transaction_drafts表成功")
            
            # 10. 创建对账日志表
            cursor.execute("""
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
            """)
            logger.info("创建reconciliation_logs表成功")
            
            # 11. 创建转账记录表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transfer_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_transaction_id INTEGER,
                to_transaction_id INTEGER,
                amount REAL,
                transfer_date TEXT,
                FOREIGN KEY (from_transaction_id) REFERENCES transactions (id),
                FOREIGN KEY (to_transaction_id) REFERENCES transactions (id)
            )
            """)
            logger.info("创建transfer_records表成功")
            
            # 12. 创建用户权限表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                resource_type TEXT,
                resource_id INTEGER,
                permission TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """)
            logger.info("创建user_permissions表成功")
            
            # 创建索引以提高查询性能
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(category_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_user ON transaction_drafts(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_created ON transaction_drafts(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_updated ON transaction_drafts(updated_at)")
            logger.info("创建索引成功")
            
            # 提交事务
            conn.commit()
            
            # 记录初始版本
            self._record_version(1, 'Initial database structure')
            
            logger.info("数据库初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _record_version(self, version: int, description: str):
        """
        记录版本信息到迁移表
        
        Args:
            version: 版本号
            description: 描述
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            migration_info = {
                'version': version,
                'description': description,
                'applied_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'migration_data': json.dumps({
                    'type': 'upgrade',
                    'timestamp': datetime.now().isoformat()
                })
            }
            
            # 检查版本是否已存在
            cursor.execute(f"SELECT id FROM {MIGRATIONS_TABLE} WHERE version = ?", (version,))
            if not cursor.fetchone():
                cursor.execute(
                    f"INSERT INTO {MIGRATIONS_TABLE} (version, description, applied_at, migration_data) VALUES (?, ?, ?, ?)",
                    (migration_info['version'], migration_info['description'], 
                     migration_info['applied_at'], migration_info['migration_data'])
                )
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"记录版本信息失败: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
    
    def insert_initial_data(self):
        """插入初始数据"""
        logger.info("开始插入初始数据...")
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 1. 检查是否已有管理员用户
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cursor.fetchone()[0] == 0:
                # 创建默认管理员用户，使用哈希处理的密码
                admin_password = 'admin123'
                hashed_password = hash_password(admin_password)
                cursor.execute(
                    "INSERT INTO users (username, password, fullname, email, role) VALUES (?, ?, ?, ?, ?)",
                    ('admin', hashed_password, '系统管理员', 'admin@example.com', 'admin')
                )
                logger.info("创建默认管理员用户成功")
            
            # 2. 检查是否已有默认账户
            cursor.execute("SELECT COUNT(*) FROM accounts")
            if cursor.fetchone()[0] == 0:
                # 创建默认账户
                default_accounts = [
                    ('现金账户', 'asset', 'CNY', 0.0, '主要用于记录现金收支', 'active'),
                    ('银行存款', 'asset', 'CNY', 0.0, '主要用于记录银行账户收支', 'active'),
                    ('应收账款', 'asset', 'CNY', 0.0, '记录客户欠款', 'active'),
                    ('应付账款', 'liability', 'CNY', 0.0, '记录欠供应商款项', 'active'),
                    ('股本', 'equity', 'CNY', 0.0, '记录公司注册资本', 'active')
                ]
                
                for account in default_accounts:
                    cursor.execute(
                        "INSERT INTO accounts (name, account_type, currency, balance, description, status) VALUES (?, ?, ?, ?, ?, ?)",
                        account
                    )
                logger.info("创建默认账户成功")
            
            # 3. 检查是否已有默认分类
            cursor.execute("SELECT COUNT(*) FROM categories")
            if cursor.fetchone()[0] == 0:
                # 创建默认收入分类
                income_categories = [
                    ('主营业务收入', 'income', None, '💰', '#28a745', 'default', '销售商品或提供服务的收入', 1),
                    ('其他业务收入', 'income', None, '💵', '#20c997', 'default', '非主营业务的收入', 1),
                    ('投资收益', 'income', None, '📈', '#6f42c1', 'default', '投资获得的收益', 1),
                    ('营业外收入', 'income', None, '🎁', '#ffc107', 'default', '与生产经营无直接关系的收入', 1)
                ]
                
                for category in income_categories:
                    cursor.execute(
                        "INSERT INTO categories (name, category_type, parent_id, icon, color, description, is_system) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        category[:-1]  # 去掉最后一个元素，因为我们不需要'default'字段
                    )
                
                # 创建默认支出分类
                expense_categories = [
                    ('主营业务成本', 'expense', None, '📦', '#dc3545', 'default', '销售商品或提供服务的成本', 1),
                    ('销售费用', 'expense', None, '🏢', '#fd7e14', 'default', '销售过程中发生的各项费用', 1),
                    ('管理费用', 'expense', None, '⚙️', '#17a2b8', 'default', '企业管理部门发生的费用', 1),
                    ('财务费用', 'expense', None, '💸', '#6c757d', 'default', '筹集生产经营所需资金等发生的费用', 1),
                    ('营业外支出', 'expense', None, '❌', '#343a40', 'default', '与生产经营无直接关系的支出', 1)
                ]
                
                for category in expense_categories:
                    cursor.execute(
                        "INSERT INTO categories (name, category_type, parent_id, icon, color, description, is_system) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        category[:-1]  # 去掉最后一个元素，因为我们不需要'default'字段
                    )
                
                logger.info("创建默认分类成功")
            
            # 4. 检查是否已有系统配置
            cursor.execute("SELECT COUNT(*) FROM system_configs")
            if cursor.fetchone()[0] == 0:
                # 插入默认系统配置
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
                
                for config in default_configs:
                    cursor.execute(
                        "INSERT INTO system_configs (config_key, config_value, config_type, description) VALUES (?, ?, ?, ?)",
                        config
                    )
                
                logger.info("创建默认系统配置成功")
            
            # 提交事务
            conn.commit()
            logger.info("初始数据插入完成")
            
        except Exception as e:
            logger.error(f"插入初始数据失败: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def create_migration(self, migration_name):
        """
        创建新的迁移文件
        
        Args:
            migration_name: 迁移名称
            
        Returns:
            str: 迁移文件路径
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            migration_file = f"{timestamp}_{migration_name}.sql"
            migration_path = os.path.join(self.migrations_dir, migration_file)
            
            # 创建空的迁移文件
            with open(migration_path, 'w', encoding='utf-8') as f:
                f.write(f"-- 迁移文件: {migration_name}\n")
                f.write(f"-- 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("-- 在此处编写SQL语句\n")
            
            logger.info(f"创建迁移文件成功: {migration_file}")
            return migration_path
            
        except Exception as e:
            logger.error(f"创建迁移文件失败: {str(e)}")
            raise
    
    @handle_errors('db_migration')
    def execute_migration(self, migration_file):
        """
        执行指定的迁移文件
        
        Args:
            migration_file: 迁移文件名称
            
        Returns:
            bool: 迁移是否成功执行
            
        Raises:
            MigrationError: 迁移执行失败时抛出
            DatabaseError: 数据库操作失败时抛出
        """
        try:
            # 检查迁移是否已执行
            history = self.get_migration_history()
            if migration_file in [m['file'] for m in history]:
                self.logger.warning(f"迁移文件已执行: {migration_file}")
                return False
            
            # 读取迁移文件
            migration_path = os.path.join(self.migrations_dir, migration_file)
            if not os.path.exists(migration_path):
                self.logger.error(f"迁移文件不存在: {migration_file}")
                raise MigrationError(f"迁移文件不存在: {migration_file}")
            
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql_statements = f.read()
            
            # 执行SQL语句
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 分割并执行多个SQL语句
            for statement in sql_statements.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    cursor.execute(statement)
            
            # 提交事务
            conn.commit()
            
            # 更新迁移历史
            migration_record = {
                'file': migration_file,
                'executed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            history.append(migration_record)
            self.save_migration_history(history)
            
            self.logger.info(f"迁移文件执行成功: {migration_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"执行迁移文件失败: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
            if isinstance(e, (MigrationError, DatabaseError)):
                raise
            raise MigrationError(f"迁移执行失败: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    @handle_errors
    def migrate_all(self):
        """执行所有未执行的迁移文件和版本升级
        
        Raises:
            MigrationError: 迁移执行失败时抛出
            DatabaseError: 数据库操作失败时抛出
        """
        self.logger.info("开始执行所有未执行的迁移...")
        
        # 首先执行版本化迁移
        current_version = self.get_current_version()
        latest_version = self.get_latest_version()
        
        if current_version < latest_version:
            self.logger.info(f"执行版本升级: {current_version} -> {latest_version}")
            self.upgrade(current_version, latest_version)
        
        # 兼容旧版本：继续执行文件系统中的迁移文件
        history = self.get_migration_history()
        executed_migrations = [m['file'] for m in history]
        
        migration_files = [f for f in os.listdir(self.migrations_dir) 
                         if f.endswith('.sql') and f != 'init.sql']
        
        migration_files.sort()
        
        executed_count = 0
        for migration_file in migration_files:
            if migration_file not in executed_migrations:
                if self.execute_migration(migration_file):
                    executed_count += 1
        
        self.logger.info(f"迁移完成，当前版本: {self.get_current_version()}, 执行文件迁移: {executed_count} 个")
        return executed_count
    
    @handle_errors
    def upgrade(self, from_version: int, to_version: int) -> Dict[str, Any]:
        """
        升级数据库到指定版本
        
        Args:
            from_version: 起始版本
            to_version: 目标版本
            
        Returns:
            升级结果信息
            
        Raises:
            MigrationError: 迁移执行失败时抛出
            DatabaseError: 数据库操作失败时抛出
        """
        self.logger.info(f"开始升级数据库: {from_version} -> {to_version}")
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            applied_migrations = []
            
            # 按版本顺序执行升级
            for migration in sorted(VERSION_MIGRATIONS, key=lambda x: x['version']):
                if from_version < migration['version'] <= to_version:
                    self.logger.info(f"执行升级到版本 {migration['version']}: {migration['description']}")
                    
                    # 执行每个SQL语句
                    for sql in migration['upgrade']:
                        try:
                            cursor.execute(sql)
                            self.logger.debug(f"执行SQL成功: {sql[:50]}...")
                        except Exception as e:
                            self.logger.error(f"执行SQL失败: {sql[:50]}... - {str(e)}")
                            raise
                    
                    applied_migrations.append(migration['version'])
            
            conn.commit()
            conn.close()
            
            # 记录所有应用的版本
            for version in applied_migrations:
                migration = next(m for m in VERSION_MIGRATIONS if m['version'] == version)
                self._record_version(version, migration['description'])
            
            self.logger.info(f"数据库升级成功: {from_version} -> {to_version}, 应用了 {len(applied_migrations)} 个迁移")
            
            return {
                'success': True,
                'from_version': from_version,
                'to_version': to_version,
                'applied_migrations': applied_migrations
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            self.logger.error(f"数据库升级失败: {str(e)}")
            raise
    
    @handle_errors
    def downgrade(self, from_version: int, to_version: int) -> Dict[str, Any]:
        """
        降级数据库版本
        
        Args:
            from_version: 当前版本
            to_version: 目标版本
            
        Returns:
            Dict: 降级结果信息
            
        Raises:
            MigrationError: 迁移执行失败时抛出
            DatabaseError: 数据库操作失败时抛出
            ValueError: 无效的版本号范围时抛出
        """
        self.logger.info(f"开始降级数据库: {from_version} -> {to_version}")
        
        # 验证版本号
        if to_version < 0 or from_version < to_version:
            raise ValueError(f"无效的版本号范围: {from_version} -> {to_version}")
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            conn.execute("PRAGMA foreign_keys = OFF")  # 降级时关闭外键约束
            
            reverted_migrations = []
            
            # 按版本倒序执行降级
            for migration in sorted(VERSION_MIGRATIONS, key=lambda x: x['version'], reverse=True):
                if to_version < migration['version'] <= from_version:
                    self.logger.info(f"执行回滚版本 {migration['version']}: {migration['description']}")
                    
                    # 执行每个回滚SQL语句
                    for sql in migration['downgrade']:
                        try:
                            cursor.execute(sql)
                            self.logger.debug(f"执行回滚SQL成功: {sql[:50]}...")
                        except Exception as e:
                            self.logger.warning(f"执行回滚SQL失败: {sql[:50]}... - {str(e)}")
                            # 降级失败不中断，继续尝试其他操作
                            continue
                    
                    # 删除迁移记录
                    cursor.execute(f"DELETE FROM {MIGRATIONS_TABLE} WHERE version = ?", (migration['version'],))
                    reverted_migrations.append(migration['version'])
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"数据库降级成功: {from_version} -> {to_version}, 回滚了 {len(reverted_migrations)} 个迁移")
            
            return {
                'success': True,
                'from_version': from_version,
                'to_version': to_version,
                'reverted_migrations': reverted_migrations
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            self.logger.error(f"数据库降级失败: {str(e)}")
            if isinstance(e, (MigrationError, DatabaseError)):
                raise
            raise MigrationError(f"数据库降级失败: {str(e)}")
    
    def get_migration_history_db(self) -> List[Dict[str, Any]]:
        """
        从数据库获取迁移历史记录
        
        Returns:
            迁移历史记录列表
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查迁移记录表是否存在
            cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name=?
            ''', (MIGRATIONS_TABLE,))
            
            if not cursor.fetchone():
                conn.close()
                return []
            
            # 获取所有迁移记录
            cursor.execute(f"SELECT * FROM {MIGRATIONS_TABLE} ORDER BY version DESC")
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                # 解析JSON数据
                if result.get('migration_data'):
                    try:
                        result['migration_data'] = json.loads(result['migration_data'])
                    except:
                        result['migration_data'] = None
                results.append(result)
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"获取迁移历史失败: {str(e)}")
            return []
    
    @handle_errors
    def export_schema(self, output_file=None):
        """
        导出数据库架构
        
        Args:
            output_file: 输出文件路径，如果为None则返回SQL语句
            
        Returns:
            str: 数据库架构SQL语句
            
        Raises:
            DatabaseError: 数据库操作失败时抛出
            IOError: 文件写入失败时抛出
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()
            
            schema_sql = """-- 数据库架构导出
-- 导出时间: {}\n\n""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 导出每个表的创建语句
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                create_sql = cursor.fetchone()[0]
                schema_sql += f"\n-- 创建表 {table_name}\n"
                schema_sql += create_sql + ";\n\n"
            
            # 导出索引
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
            indexes = cursor.fetchall()
            
            for index in indexes:
                index_name, create_sql = index
                schema_sql += f"\n-- 创建索引 {index_name}\n"
                schema_sql += create_sql + ";\n\n"
            
            # 输出到文件
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(schema_sql)
                self.logger.info(f"数据库架构导出成功: {output_file}")
            
            return schema_sql
            
        except Exception as e:
            self.logger.error(f"导出数据库架构失败: {str(e)}")
            if isinstance(e, (DatabaseError, IOError)):
                raise
            raise DatabaseError(f"导出数据库架构失败: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def optimize_database(self):
        """优化数据库性能"""
        logger.info("开始优化数据库...")
        
        try:
            conn = self.get_connection()
            conn.execute("VACUUM")
            conn.commit()
            logger.info("数据库优化完成")
        except Exception as e:
            logger.error(f"数据库优化失败: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()


# 提供便捷的数据库初始化函数


# MigrationManager类 - 为测试和外部调用提供统一接口
class MigrationManager:
    """
    数据库迁移管理器，提供统一的数据库迁移接口
    """
    def __init__(self, db_path_or_manager):
        """
        初始化MigrationManager
        
        Args:
            db_path_or_manager: 数据库文件路径字符串或DatabaseManager对象
        """
        # 处理DatabaseManager对象的情况
        if hasattr(db_path_or_manager, 'db_path'):
            # 确保提取的db_path是字符串类型
            db_path = db_path_or_manager.db_path
            if not isinstance(db_path, str):
                raise TypeError("DatabaseManager.db_path必须是字符串类型")
            self.db_path = db_path
        elif isinstance(db_path_or_manager, str):
            # 如果是字符串，直接使用
            self.db_path = db_path_or_manager
        else:
            raise TypeError("参数必须是数据库路径字符串或具有db_path属性的DatabaseManager对象")
        
        # 创建DBMigration实例
        self.migration = DBMigration(self.db_path)
    
    def initialize(self):
        """
        初始化数据库
        """
        return init_database(self.db_path)
    
    def migrate_all(self):
        """
        执行所有未执行的迁移
        """
        return run_migrations(self.db_path)
    
    def migrate_to(self, target_version=None):
        """
        迁移到指定版本
        
        Args:
            target_version: 目标版本，如果为None则迁移到最新版本
            
        Returns:
            迁移结果
        """
        return run_migration(self.db_path, target_version)
    
    def get_current_version(self):
        """
        获取当前数据库版本
        
        Returns:
            当前版本号
        """
        return self.migration.get_current_version()
    
    def get_latest_version(self):
        """
        获取最新可用版本
        
        Returns:
            最新版本号
        """
        return self.migration.get_latest_version()
    
    def get_history(self):
        """
        获取迁移历史
        
        Returns:
            迁移历史记录列表
        """
        return self.migration.get_migration_history_db()
    
    def verify_integrity(self):
        """
        验证数据库完整性
        
        Returns:
            完整性检查结果
        """
        return verify_database_integrity(self.db_path)

def init_database(db_path):
    """
    初始化数据库的便捷函数
    
    Args:
        db_path: 数据库文件路径
    """
    migration = DBMigration(db_path)
    migration.initialize_database()
    migration.insert_initial_data()
    migration.optimize_database()
    logger.info(f"数据库初始化完成: {db_path}")


def run_migrations(db_path):
    """
    执行数据库迁移的便捷函数
    
    Args:
        db_path: 数据库文件路径
    """
    migration = DBMigration(db_path)
    migration.migrate_all()
    logger.info(f"数据库迁移完成: {db_path}")


def run_migration(db_path: str, target_version: int = None) -> Dict[str, Any]:
    """
    运行数据库迁移到指定版本（外部统一接口）
    
    Args:
        db_path: 数据库文件路径
        target_version: 目标版本，如果为None则迁移到最新版本
        
    Returns:
        迁移结果信息
    """
    try:
        migration = DBMigration(db_path)
        current_version = migration.get_current_version()
        
        # 如果未指定目标版本，则迁移到最新版本
        if target_version is None:
            target_version = migration.get_latest_version()
        
        # 验证目标版本
        if target_version < 0 or target_version > migration.get_latest_version():
            raise ValueError(f"无效的目标版本: {target_version}")
        
        # 检查是否已经是目标版本
        if current_version == target_version:
            logger.info(f"数据库已经是目标版本: {current_version}")
            return {
                'success': True,
                'current_version': current_version,
                'target_version': target_version,
                'message': f'数据库已经是版本 {current_version}'
            }
        
        # 执行升级或降级
        if current_version < target_version:
            result = migration.upgrade(current_version, target_version)
            result['message'] = f'数据库升级成功: {current_version} -> {target_version}'
        else:
            result = migration.downgrade(current_version, target_version)
            result['message'] = f'数据库降级成功: {current_version} -> {target_version}'
        
        result['success'] = True
        return result
        
    except Exception as e:
        logger.error(f"运行数据库迁移失败: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': '数据库迁移失败'
        }


def verify_database_integrity(db_path: str) -> Dict[str, Any]:
    """
    验证数据库完整性
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        完整性检查结果
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 执行完整性检查
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchall()
        
        # 检查迁移版本
        migration = DBMigration(db_path)
        current_version = migration.get_current_version()
        latest_version = migration.get_latest_version()
        
        # 检查必要的表是否存在
        required_tables = ['users', 'accounts', 'categories', 'transactions', 'budgets']
        existing_tables = []
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for row in cursor.fetchall():
            existing_tables.append(row[0])
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        conn.close()
        
        return {
            'success': len(integrity_result) > 0 and integrity_result[0][0] == 'ok' and not missing_tables,
            'integrity_check': 'ok' if len(integrity_result) > 0 and integrity_result[0][0] == 'ok' else 'failed',
            'current_version': current_version,
            'latest_version': latest_version,
            'is_up_to_date': current_version == latest_version,
            'missing_tables': missing_tables,
            'message': '数据库完整性检查通过' if len(integrity_result) > 0 and integrity_result[0][0] == 'ok' and not missing_tables else '数据库完整性检查失败'
        }
        
    except Exception as e:
        logger.error(f"数据库完整性检查失败: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': '数据库完整性检查失败'
        }


# 当直接运行此脚本时
if __name__ == "__main__":
    import sys
    
    # 默认数据库路径
    default_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                 'data', 'finance_system.db')
    
    # 处理命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'init':
            # 初始化数据库
            print(f"初始化数据库: {default_db_path}")
            init_database(default_db_path)
            print("数据库初始化成功！")
            
        elif command == 'version':
            # 显示当前版本
            migration = DBMigration(default_db_path)
            version = migration.get_current_version()
            latest = migration.get_latest_version()
            print(f"当前数据库版本: {version}")
            print(f"最新可用版本: {latest}")
            print(f"数据库是否是最新版本: {'是' if version == latest else '否'}")
            
        elif command == 'upgrade':
            # 升级数据库
            target_version = int(sys.argv[2]) if len(sys.argv) > 2 else None
            print(f"升级数据库到版本: {target_version or '最新'}")
            result = run_migration(default_db_path, target_version)
            print(f"升级结果: {'成功' if result['success'] else '失败'}")
            print(f"消息: {result.get('message', '未知')}")
            
        elif command == 'downgrade':
            # 降级数据库
            if len(sys.argv) > 2:
                target_version = int(sys.argv[2])
                print(f"降级数据库到版本: {target_version}")
                result = run_migration(default_db_path, target_version)
                print(f"降级结果: {'成功' if result['success'] else '失败'}")
                print(f"消息: {result.get('message', '未知')}")
            else:
                print("请指定目标版本: python db_migration.py downgrade <version>")
                
        elif command == 'history':
            # 显示迁移历史
            migration = DBMigration(default_db_path)
            history = migration.get_migration_history_db()
            if history:
                print("迁移历史:")
                print("-" * 80)
                print(f"{'版本':<10}{'描述':<40}{'应用时间':<25}")
                print("-" * 80)
                for entry in history:
                    print(f"{entry['version']:<10}{entry['description']:<40}{entry['applied_at']:<25}")
            else:
                print("暂无迁移历史记录")
                
        elif command == 'migrate':
            # 执行所有迁移
            print(f"执行数据库迁移: {default_db_path}")
            run_migrations(default_db_path)
            print("数据库迁移完成！")
            
        elif command == 'check':
            # 检查数据库完整性
            result = verify_database_integrity(default_db_path)
            print("数据库完整性检查:")
            print(f"检查结果: {'通过' if result['success'] else '失败'}")
            print(f"完整性状态: {result['integrity_check']}")
            print(f"当前版本: {result['current_version']}")
            print(f"最新版本: {result['latest_version']}")
            if result['missing_tables']:
                print(f"缺失的表: {', '.join(result['missing_tables'])}")
                
        else:
            print("未知命令。可用命令:")
            print("  init      - 初始化数据库")
            print("  version   - 显示当前版本")
            print("  upgrade   - 升级数据库 [版本号]")
            print("  downgrade - 降级数据库 <版本号>")
            print("  history   - 显示迁移历史")
            print("  migrate   - 执行所有迁移")
            print("  check     - 检查数据库完整性")
            
    else:
        print("请指定命令。使用方法:")
        print("python db_migration.py <command>")
        print("可用命令: init, version, upgrade, downgrade, history, migrate, check")