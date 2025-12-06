# 数据访问工具
import sqlite3
import json
import logging
import os
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DBAccess")

# 数据库文件路径 - 与db_manager保持一致
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                      'data', 'finance_system.db')

class DBAccess:
    """数据访问类，提供统一的数据库操作接口"""
    
    def __init__(self, db_path):
        """
        初始化数据访问对象
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
        # 注册JSON序列化和反序列化函数
        sqlite3.register_adapter(dict, json.dumps)
        sqlite3.register_adapter(list, json.dumps)
        sqlite3.register_converter("JSON", json.loads)
    
    def connect(self):
        """建立数据库连接"""
        try:
            # 检查连接是否已经建立且有效
            if self.connection is None:
                self.connection = sqlite3.connect(
                    self.db_path,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                    check_same_thread=False  # 允许多线程访问
                )
                # 设置行工厂为字典形式
                self.connection.row_factory = sqlite3.Row
                self.cursor = self.connection.cursor()
                logger.info(f"连接数据库成功: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return False
    
    def disconnect(self):
        """关闭数据库连接"""
        try:
            if self.connection is not None:
                self.connection.close()
                self.connection = None
                self.cursor = None
                logger.info("关闭数据库连接")
            return True
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {str(e)}")
            return False
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, 
                     fetch_all: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]], int, None]:
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            fetch_all: 是否返回所有记录（True返回列表，False返回单条）
            
        Returns:
            当fetch_all=False时返回单条记录（字典）
            当fetch_all=True时返回多条记录（字典列表）
            对于INSERT/UPDATE/DELETE等修改操作，返回影响的行数
        """
        try:
            # 确保连接已建立
            if not self.connect():
                return None
            
            # 执行查询
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # 根据需求返回结果
            # 检查是否为SELECT语句（包括以WITH开头的CTE查询）
            # 移除所有前导空白和注释，然后检查是否以SELECT或WITH开头
            cleaned_query = query.strip()
            while cleaned_query.startswith('--'):
                # 移除单行注释
                cleaned_query = cleaned_query[cleaned_query.find('\n'):].strip()
            
            upper_query = cleaned_query.upper()
            is_select = upper_query.startswith('SELECT') or upper_query.startswith('WITH')
            
            if is_select:
                if fetch_all:
                    results = self.cursor.fetchall()
                    result_dicts = [dict(row) for row in results]
                    return result_dicts
                else:
                    result = self.cursor.fetchone()
                    if result:
                        result_dict = dict(result)
                        return result_dict
                    return None
            else:
                # 对于非SELECT语句，返回影响的行数
                row_count = self.cursor.rowcount
                return row_count
                
        except Exception as e:
            import traceback
            print(f"执行查询失败: {str(e)}")
            print(f"SQL: {query}")
            print(f"参数: {params}")
            print(f"错误堆栈: {traceback.format_exc()}")
            logger.error(f"执行查询失败: {str(e)}")
            logger.error(f"SQL: {query}")
            logger.error(f"参数: {params}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def execute_transaction(self, queries: List[Tuple[str, Optional[Tuple]]]) -> bool:
        """
        执行事务（多条SQL语句）
        
        Args:
            queries: SQL查询语句和参数的列表
            
        Returns:
            是否执行成功
        """
        try:
            # 确保连接已建立
            if not self.connect():
                return False
            
            # 开始事务
            self.connection.begin()
            
            # 执行所有查询
            for query, params in queries:
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
            
            # 提交事务
            self.connection.commit()
            logger.info(f"事务执行成功，共{len(queries)}条语句")
            return True
            
        except Exception as e:
            logger.error(f"事务执行失败: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        插入数据
        
        Args:
            table: 表名
            data: 要插入的数据（字典形式）
            
        Returns:
            新插入记录的ID，如果失败返回None
        """
        try:
            # 构建SQL语句
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data.keys()])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            # 执行插入
            result = self.execute_query(query, tuple(data.values()))
            
            # 返回插入的ID
            if result is not None and result >= 0:
                return self.cursor.lastrowid
            return None
            
        except Exception as e:
            logger.error(f"插入数据失败: {str(e)}")
            return None
    
    def update(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> Optional[int]:
        """
        更新数据
        
        Args:
            table: 表名
            data: 要更新的数据（字典形式）
            where: 更新条件（字典形式）
            
        Returns:
            影响的行数，如果失败返回None
        """
        try:
            # 构建更新部分
            update_parts = [f"{k} = ?" for k in data.keys()]
            update_clause = ', '.join(update_parts)
            
            # 构建条件部分
            where_parts = [f"{k} = ?" for k in where.keys()]
            where_clause = ' AND '.join(where_parts)
            
            # 构建完整SQL语句
            query = f"UPDATE {table} SET {update_clause} WHERE {where_clause}"
            
            # 合并参数
            params = tuple(data.values()) + tuple(where.values())
            
            # 执行更新
            return self.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"更新数据失败: {str(e)}")
            return None
    
    def delete(self, table: str, where: Dict[str, Any]) -> Optional[int]:
        """
        删除数据
        
        Args:
            table: 表名
            where: 删除条件（字典形式）
            
        Returns:
            影响的行数，如果失败返回None
        """
        try:
            # 构建条件部分
            where_parts = [f"{k} = ?" for k in where.keys()]
            where_clause = ' AND '.join(where_parts)
            
            # 构建完整SQL语句
            query = f"DELETE FROM {table} WHERE {where_clause}"
            
            # 执行删除
            return self.execute_query(query, tuple(where.values()))
            
        except Exception as e:
            logger.error(f"删除数据失败: {str(e)}")
            return None
    
    def select(self, table: str, where: Optional[Dict[str, Any]] = None, 
               fields: Optional[List[str]] = None, order_by: Optional[str] = None,
               limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查询数据
        
        Args:
            table: 表名
            where: 查询条件（字典形式）
            fields: 要查询的字段列表
            order_by: 排序字段
            limit: 限制返回记录数
            offset: 偏移量
            
        Returns:
            查询结果列表（字典列表）
        """
        try:
            # 构建字段部分
            if fields:
                fields_clause = ', '.join(fields)
            else:
                fields_clause = '*'
            
            # 构建查询语句
            query = f"SELECT {fields_clause} FROM {table}"
            params = []
            
            # 添加条件
            if where:
                where_parts = [f"{k} = ?" for k in where.keys()]
                where_clause = ' WHERE ' + ' AND '.join(where_parts)
                query += where_clause
                params.extend(where.values())
            
            # 添加排序
            if order_by:
                query += f" ORDER BY {order_by}"
            
            # 添加分页
            if limit is not None:
                query += f" LIMIT {limit}"
                if offset is not None:
                    query += f" OFFSET {offset}"
            
            # 执行查询
            return self.execute_query(query, tuple(params), fetch_all=True)
            
        except Exception as e:
            logger.error(f"查询数据失败: {str(e)}")
            return []
    
    def count(self, table: str, where: Optional[Dict[str, Any]] = None) -> int:
        """
        统计记录数
        
        Args:
            table: 表名
            where: 查询条件（字典形式）
            
        Returns:
            记录数
        """
        try:
            # 构建查询语句
            query = f"SELECT COUNT(*) as count FROM {table}"
            params = []
            
            # 添加条件
            if where:
                where_parts = [f"{k} = ?" for k in where.keys()]
                where_clause = ' WHERE ' + ' AND '.join(where_parts)
                query += where_clause
                params.extend(where.values())
            
            # 执行查询
            result = self.execute_query(query, tuple(params), fetch=True)
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"统计记录数失败: {str(e)}")
            return 0
    
    def exists(self, table: str, where: Dict[str, Any]) -> bool:
        """
        检查记录是否存在
        
        Args:
            table: 表名
            where: 查询条件（字典形式）
            
        Returns:
            是否存在
        """
        return self.count(table, where) > 0
    
    def get_column_names(self, table: str) -> List[str]:
        """
        获取表的列名
        
        Args:
            table: 表名
            
        Returns:
            列名列表
        """
        try:
            # 执行PRAGMA语句获取表信息
            query = f"PRAGMA table_info({table})"
            results = self.execute_query(query, fetch_all=True)
            
            # 提取列名
            return [row['name'] for row in results]
            
        except Exception as e:
            logger.error(f"获取表列名失败: {str(e)}")
            return []
    
    def get_table_names(self) -> List[str]:
        """
        获取所有表名
        
        Returns:
            表名列表
        """
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            results = self.execute_query(query, fetch_all=True)
            
            return [row['name'] for row in results]
            
        except Exception as e:
            logger.error(f"获取表名列表失败: {str(e)}")
            return []
    
    def get_distinct_values(self, table: str, column: str, 
                          where: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        获取指定列的唯一值
        
        Args:
            table: 表名
            column: 列名
            where: 查询条件（字典形式）
            
        Returns:
            唯一值列表
        """
        try:
            # 构建查询语句
            query = f"SELECT DISTINCT {column} FROM {table}"
            params = []
            
            # 添加条件
            if where:
                where_parts = [f"{k} = ?" for k in where.keys()]
                where_clause = ' WHERE ' + ' AND '.join(where_parts)
                query += where_clause
                params.extend(where.values())
            
            # 执行查询
            results = self.execute_query(query, tuple(params), fetch_all=True)
            return [row[column] for row in results]
            
        except Exception as e:
            logger.error(f"获取唯一值失败: {str(e)}")
            return []
    
    def get_max_value(self, table: str, column: str, 
                     where: Optional[Dict[str, Any]] = None) -> Any:
        """
        获取指定列的最大值
        
        Args:
            table: 表名
            column: 列名
            where: 查询条件（字典形式）
            
        Returns:
            最大值
        """
        try:
            # 构建查询语句
            query = f"SELECT MAX({column}) as max_value FROM {table}"
            params = []
            
            # 添加条件
            if where:
                where_parts = [f"{k} = ?" for k in where.keys()]
                where_clause = ' WHERE ' + ' AND '.join(where_parts)
                query += where_clause
                params.extend(where.values())
            
            # 执行查询
            result = self.execute_query(query, tuple(params), fetch=True)
            return result['max_value'] if result and result['max_value'] is not None else None
            
        except Exception as e:
            logger.error(f"获取最大值失败: {str(e)}")
            return None
    
    def get_min_value(self, table: str, column: str, 
                     where: Optional[Dict[str, Any]] = None) -> Any:
        """
        获取指定列的最小值
        
        Args:
            table: 表名
            column: 列名
            where: 查询条件（字典形式）
            
        Returns:
            最小值
        """
        try:
            # 构建查询语句
            query = f"SELECT MIN({column}) as min_value FROM {table}"
            params = []
            
            # 添加条件
            if where:
                where_parts = [f"{k} = ?" for k in where.keys()]
                where_clause = ' WHERE ' + ' AND '.join(where_parts)
                query += where_clause
                params.extend(where.values())
            
            # 执行查询
            result = self.execute_query(query, tuple(params), fetch=True)
            return result['min_value'] if result and result['min_value'] is not None else None
            
        except Exception as e:
            logger.error(f"获取最小值失败: {str(e)}")
            return None
    
    def get_sum_value(self, table: str, column: str, 
                     where: Optional[Dict[str, Any]] = None) -> Any:
        """
        获取指定列的总和
        
        Args:
            table: 表名
            column: 列名
            where: 查询条件（字典形式）
            
        Returns:
            总和
        """
        try:
            # 构建查询语句
            query = f"SELECT SUM({column}) as sum_value FROM {table}"
            params = []
            
            # 添加条件
            if where:
                where_parts = [f"{k} = ?" for k in where.keys()]
                where_clause = ' WHERE ' + ' AND '.join(where_parts)
                query += where_clause
                params.extend(where.values())
            
            # 执行查询
            result = self.execute_query(query, tuple(params), fetch=True)
            return result['sum_value'] if result and result['sum_value'] is not None else 0
            
        except Exception as e:
            logger.error(f"获取总和失败: {str(e)}")
            return 0
    
    def log_operation(self, user_id: Optional[int], operation_type: str, 
                     operation_desc: str, operation_table: Optional[str] = None,
                     operation_data: Optional[Dict[str, Any]] = None, 
                     ip_address: Optional[str] = None) -> None:
        """
        记录操作日志
        
        Args:
            user_id: 用户ID
            operation_type: 操作类型
            operation_desc: 操作描述
            operation_table: 操作的表名
            operation_data: 操作的数据
            ip_address: IP地址
        """
        try:
            log_data = {
                'user_id': user_id,
                'operation_type': operation_type,
                'operation_desc': operation_desc,
                'operation_table': operation_table,
                'operation_data': json.dumps(operation_data) if operation_data else None,
                'ip_address': ip_address,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 过滤掉None值
            log_data = {k: v for k, v in log_data.items() if v is not None}
            
            # 插入日志表
            self.insert('operation_logs', log_data)
            
        except Exception as e:
            logger.error(f"记录操作日志失败: {str(e)}")


# 提供全局数据访问实例
_db_access_instance = None

def get_db_access(db_path=None):
    """
    获取全局数据库访问实例
    
    Args:
        db_path: 数据库文件路径，如果已存在实例则忽略
        
    Returns:
        DBAccess实例
    """
    global _db_access_instance
    
    # 如果还没有实例，尝试创建一个
    if _db_access_instance is None:
        # 如果提供了db_path，使用它创建实例
        if db_path:
            _db_access_instance = DBAccess(db_path)
        else:
            # 尝试使用默认路径
            import os
            default_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                       'data', 'finance_system.db')
            if os.path.exists(default_path):
                _db_access_instance = DBAccess(default_path)
    
    return _db_access_instance

def close_db_access():
    """
    关闭全局数据库访问实例
    """
    global _db_access_instance
    
    if _db_access_instance:
        _db_access_instance.disconnect()
        _db_access_instance = None


# 提供便捷的查询函数
def execute_query(query, params=None, fetch=False, fetch_all=False):
    """
    便捷的查询函数
    
    Args:
        query: SQL查询语句
        params: 查询参数
        fetch: 是否返回单条记录（兼容旧代码）
        fetch_all: 是否返回所有记录
        
    Returns:
        查询结果
    """
    db_access = get_db_access()
    if db_access:
        # 兼容旧代码：如果fetch=True，自动设置fetch_all=False
        if fetch:
            fetch_all = False
        return db_access.execute_query(query, params, fetch_all=fetch_all)
    return None


def insert_record(table, data):
    """
    便捷的插入函数
    
    Args:
        table: 表名
        data: 要插入的数据
        
    Returns:
        插入的ID
    """
    db_access = get_db_access()
    if db_access:
        return db_access.insert(table, data)
    return None


def update_record(table, data, where):
    """
    便捷的更新函数
    
    Args:
        table: 表名
        data: 要更新的数据
        where: 更新条件
        
    Returns:
        影响的行数
    """
    db_access = get_db_access()
    if db_access:
        return db_access.update(table, data, where)
    return None


def delete_record(table, where):
    """
    便捷的删除函数
    
    Args:
        table: 表名
        where: 删除条件
        
    Returns:
        影响的行数
    """
    db_access = get_db_access()
    if db_access:
        return db_access.delete(table, where)
    return None


def select_records(table, where=None, fields=None, order_by=None, limit=None, offset=None):
    """
    便捷的查询函数
    
    Args:
        table: 表名
        where: 查询条件
        fields: 字段列表
        order_by: 排序字段
        limit: 限制记录数
        offset: 偏移量
        
    Returns:
        查询结果列表
    """
    db_access = get_db_access()
    if db_access:
        return db_access.select(table, where, fields, order_by, limit, offset)
    return []