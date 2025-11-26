# 数据库迁移工具
import sqlite3
import os
import json
import logging
from datetime import datetime

# 添加项目根目录到Python路径
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.security import hash_password

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
        self.db_path = db_path
        self.migrations_dir = os.path.join(os.path.dirname(db_path), "migrations")
        self.migration_history = os.path.join(self.migrations_dir, "history.json")
        
        # 确保迁移目录存在
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
            logger.info(f"创建迁移目录: {self.migrations_dir}")
        
        # 确保迁移历史文件存在
        if not os.path.exists(self.migration_history):
            with open(self.migration_history, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
                logger.info(f"创建迁移历史文件: {self.migration_history}")
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def get_migration_history(self):
        """获取已执行的迁移记录"""
        try:
            with open(self.migration_history, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取迁移历史失败: {str(e)}")
            return []
    
    def save_migration_history(self, history):
        """保存迁移历史"""
        try:
            with open(self.migration_history, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                logger.info(f"保存迁移历史成功")
        except Exception as e:
            logger.error(f"保存迁移历史失败: {str(e)}")
    
    def initialize_database(self):
        """初始化数据库，创建必要的表结构"""
        logger.info("开始初始化数据库...")
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
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
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """)
            logger.info("创建transactions表成功")
            
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
            
            # 9. 创建索引以提高查询性能
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(category_type)")
            logger.info("创建索引成功")
            
            # 提交事务
            conn.commit()
            logger.info("数据库初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
            raise
        finally:
            if 'conn' in locals():
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
    
    def execute_migration(self, migration_file):
        """
        执行指定的迁移文件
        
        Args:
            migration_file: 迁移文件名称
        """
        try:
            # 检查迁移是否已执行
            history = self.get_migration_history()
            if migration_file in [m['file'] for m in history]:
                logger.warning(f"迁移文件已执行: {migration_file}")
                return False
            
            # 读取迁移文件
            migration_path = os.path.join(self.migrations_dir, migration_file)
            if not os.path.exists(migration_path):
                logger.error(f"迁移文件不存在: {migration_file}")
                return False
            
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
            
            logger.info(f"迁移文件执行成功: {migration_file}")
            return True
            
        except Exception as e:
            logger.error(f"执行迁移文件失败: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def migrate_all(self):
        """执行所有未执行的迁移文件"""
        logger.info("开始执行所有未执行的迁移文件...")
        
        try:
            # 获取已执行的迁移
            history = self.get_migration_history()
            executed_migrations = [m['file'] for m in history]
            
            # 获取所有迁移文件
            migration_files = [f for f in os.listdir(self.migrations_dir) 
                             if f.endswith('.sql') and f != 'init.sql']
            
            # 按时间顺序排序
            migration_files.sort()
            
            # 执行未执行的迁移
            executed_count = 0
            for migration_file in migration_files:
                if migration_file not in executed_migrations:
                    if self.execute_migration(migration_file):
                        executed_count += 1
            
            logger.info(f"迁移完成，共执行 {executed_count} 个迁移文件")
            return executed_count
            
        except Exception as e:
            logger.error(f"执行迁移失败: {str(e)}")
            raise
    
    def export_schema(self, output_file=None):
        """
        导出数据库架构
        
        Args:
            output_file: 输出文件路径，如果为None则返回SQL语句
            
        Returns:
            str: 数据库架构SQL语句
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
                logger.info(f"数据库架构导出成功: {output_file}")
            
            return schema_sql
            
        except Exception as e:
            logger.error(f"导出数据库架构失败: {str(e)}")
            raise
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