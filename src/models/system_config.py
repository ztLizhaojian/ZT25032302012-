"""
系统配置数据模型
负责系统配置的数据库存储和管理
"""
from typing import Dict, Any, Optional, Union
from datetime import datetime

from src.database.db_manager import db_manager, handle_errors, DatabaseError
from src.utils.logger import get_logger


class SystemConfig:
    """
    系统配置数据模型类
    提供配置项的数据库存储和管理功能
    """
    def __init__(self):
        """初始化系统配置管理器"""
        self.logger = get_logger('system_config')
        # 初始化配置表
        self._init_config_table()
    
    @handle_errors()
    def _init_config_table(self):
        """
        初始化配置表
        """
        try:
            conn = db_manager._get_connection()
            cursor = conn.cursor()
            
            # 创建配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'string',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(key)')
            
            conn.commit()
            self.logger.info("系统配置表初始化完成")
            
            # 插入默认配置（如果不存在）
            self._insert_default_configs()
            
        except Exception as e:
            self.logger.error(f"初始化配置表失败: {str(e)}")
            raise DatabaseError(f"初始化配置表失败: {str(e)}")
    
    def _insert_default_configs(self):
        """
        插入默认配置项
        """
        default_configs = [
            ('app.name', 'Finance Management System', 'string', '应用名称'),
            ('app.version', '1.0.0', 'string', '应用版本'),
            ('app.debug', 'false', 'boolean', '调试模式'),
            ('app.currency_symbol', '¥', 'string', '货币符号'),
            ('app.date_format', 'YYYY-MM-DD', 'string', '日期格式'),
            ('app.time_format', 'HH:mm:ss', 'string', '时间格式'),
            ('app.max_records_per_page', '50', 'integer', '每页最大记录数'),
            ('security.password_min_length', '8', 'integer', '密码最小长度'),
            ('security.session_timeout', '30', 'integer', '会话超时时间（分钟）'),
            ('security.login_attempts', '5', 'integer', '最大登录尝试次数'),
            ('backup.enabled', 'true', 'boolean', '是否启用自动备份'),
            ('backup.interval_hours', '24', 'integer', '备份间隔（小时）'),
            ('notification.email_enabled', 'false', 'boolean', '是否启用邮件通知'),
            ('notification.sms_enabled', 'false', 'boolean', '是否启用短信通知'),
        ]
        
        try:
            conn = db_manager._get_connection()
            cursor = conn.cursor()
            
            for key, value, config_type, description in default_configs:
                # 检查是否已存在
                cursor.execute('SELECT id FROM system_config WHERE key = ?', (key,))
                if not cursor.fetchone():
                    cursor.execute(
                        '''INSERT INTO system_config (key, value, type, description)
                           VALUES (?, ?, ?, ?)''',
                        (key, value, config_type, description)
                    )
            
            conn.commit()
            self.logger.info("默认配置项已插入")
            
        except Exception as e:
            self.logger.error(f"插入默认配置失败: {str(e)}")
    
    @handle_errors()
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项的值
        
        Args:
            key: 配置项键名
            default: 默认值，如果配置项不存在则返回
            
        Returns:
            Any: 解析后的配置值
        """
        try:
            conn = db_manager._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT value, type FROM system_config WHERE key = ?',
                (key,)
            )
            
            result = cursor.fetchone()
            if not result:
                return default
            
            value, config_type = result
            return self._parse_value(value, config_type)
            
        except Exception as e:
            self.logger.error(f"获取配置项失败 {key}: {str(e)}")
            raise DatabaseError(f"获取配置项失败 {key}: {str(e)}")
    
    @handle_errors()
    def set_config(self, key: str, value: Any, config_type: str = None, description: str = None) -> bool:
        """
        设置配置项的值
        
        Args:
            key: 配置项键名
            value: 配置值
            config_type: 配置类型（string, boolean, integer, float, json），如果为None则自动检测
            description: 配置描述
            
        Returns:
            bool: 设置是否成功
        """
        try:
            # 确定配置类型
            if config_type is None:
                config_type = self._detect_type(value)
            
            # 序列化值
            serialized_value = self._serialize_value(value, config_type)
            
            conn = db_manager._get_connection()
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute('SELECT id FROM system_config WHERE key = ?', (key,))
            existing = cursor.fetchone()
            
            if existing:
                # 更新
                update_sql = '''UPDATE system_config 
                               SET value = ?, type = ?, updated_at = ?''' 
                params = [serialized_value, config_type, datetime.now()]
                
                # 如果提供了描述，也更新描述
                if description is not None:
                    update_sql += ', description = ?'
                    params.append(description)
                
                update_sql += ' WHERE key = ?'
                params.append(key)
                
                cursor.execute(update_sql, params)
                self.logger.info(f"配置项已更新: {key} = {value}")
            else:
                # 插入
                cursor.execute(
                    '''INSERT INTO system_config (key, value, type, description, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (key, serialized_value, config_type, description, datetime.now(), datetime.now())
                )
                self.logger.info(f"配置项已创建: {key} = {value}")
            
            conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"设置配置项失败 {key}: {str(e)}")
            raise DatabaseError(f"设置配置项失败 {key}: {str(e)}")
    
    @handle_errors()
    def delete_config(self, key: str) -> bool:
        """
        删除配置项
        
        Args:
            key: 配置项键名
            
        Returns:
            bool: 删除是否成功
        """
        try:
            conn = db_manager._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM system_config WHERE key = ?', (key,))
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                self.logger.info(f"配置项已删除: {key}")
            else:
                self.logger.warning(f"配置项不存在: {key}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"删除配置项失败 {key}: {str(e)}")
            raise DatabaseError(f"删除配置项失败 {key}: {str(e)}")
    
    @handle_errors()
    def get_all_configs(self) -> Dict[str, Any]:
        """
        获取所有配置项
        
        Returns:
            Dict[str, Any]: 所有配置项的字典
        """
        try:
            conn = db_manager._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT key, value, type FROM system_config')
            results = cursor.fetchall()
            
            configs = {}
            for key, value, config_type in results:
                configs[key] = self._parse_value(value, config_type)
            
            return configs
            
        except Exception as e:
            self.logger.error(f"获取所有配置项失败: {str(e)}")
            raise DatabaseError(f"获取所有配置项失败: {str(e)}")
    
    @handle_errors()
    def get_configs_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """
        获取指定前缀的所有配置项
        
        Args:
            prefix: 配置项前缀（如 'app.'）
            
        Returns:
            Dict[str, Any]: 匹配的配置项字典
        """
        try:
            conn = db_manager._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT key, value, type FROM system_config WHERE key LIKE ?',
                (f'{prefix}%',)
            )
            results = cursor.fetchall()
            
            configs = {}
            for key, value, config_type in results:
                configs[key] = self._parse_value(value, config_type)
            
            return configs
            
        except Exception as e:
            self.logger.error(f"获取前缀配置项失败 {prefix}: {str(e)}")
            raise DatabaseError(f"获取前缀配置项失败 {prefix}: {str(e)}")
    
    @handle_errors()
    def update_multiple_configs(self, configs: Dict[str, Any]) -> bool:
        """
        批量更新配置项
        
        Args:
            configs: 配置项字典 {key: value}
            
        Returns:
            bool: 更新是否成功
        """
        try:
            conn = db_manager._get_connection()
            cursor = conn.cursor()
            
            for key, value in configs.items():
                config_type = self._detect_type(value)
                serialized_value = self._serialize_value(value, config_type)
                
                # 检查是否已存在
                cursor.execute('SELECT id FROM system_config WHERE key = ?', (key,))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute(
                        'UPDATE system_config SET value = ?, type = ?, updated_at = ? WHERE key = ?',
                        (serialized_value, config_type, datetime.now(), key)
                    )
                else:
                    cursor.execute(
                        '''INSERT INTO system_config (key, value, type, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?)''',
                        (key, serialized_value, config_type, datetime.now(), datetime.now())
                    )
            
            conn.commit()
            self.logger.info(f"成功更新 {len(configs)} 个配置项")
            return True
            
        except Exception as e:
            self.logger.error(f"批量更新配置项失败: {str(e)}")
            raise DatabaseError(f"批量更新配置项失败: {str(e)}")
    
    def _detect_type(self, value: Any) -> str:
        """
        自动检测值的类型
        
        Args:
            value: 要检测的值
            
        Returns:
            str: 类型字符串
        """
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, (dict, list)):
            return 'json'
        else:
            return 'string'
    
    def _parse_value(self, value: str, config_type: str) -> Any:
        """
        根据类型解析配置值
        
        Args:
            value: 字符串值
            config_type: 配置类型
            
        Returns:
            Any: 解析后的值
        """
        try:
            if config_type == 'boolean':
                return value.lower() in ('true', '1', 'yes', 'y')
            elif config_type == 'integer':
                return int(value)
            elif config_type == 'float':
                return float(value)
            elif config_type == 'json':
                import json
                return json.loads(value)
            else:  # string
                return value
        except (ValueError, TypeError, json.JSONDecodeError):
            self.logger.warning(f"解析配置值失败: {value} (类型: {config_type})")
            return value
    
    def _serialize_value(self, value: Any, config_type: str) -> str:
        """
        根据类型序列化配置值
        
        Args:
            value: 要序列化的值
            config_type: 配置类型
            
        Returns:
            str: 序列化后的字符串
        """
        if config_type == 'boolean':
            return 'true' if value else 'false'
        elif config_type == 'json':
            import json
            return json.dumps(value)
        else:
            return str(value)
    
    @handle_errors()
    def export_configs(self) -> str:
        """
        导出所有配置为JSON字符串
        
        Returns:
            str: JSON格式的配置字符串
        """
        try:
            import json
            configs = self.get_all_configs()
            return json.dumps(configs, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"导出配置失败: {str(e)}")
            raise DatabaseError(f"导出配置失败: {str(e)}")
    
    @handle_errors()
    def import_configs(self, config_json: str, overwrite: bool = True) -> int:
        """
        从JSON字符串导入配置
        
        Args:
            config_json: JSON格式的配置字符串
            overwrite: 是否覆盖已存在的配置
            
        Returns:
            int: 导入的配置项数量
        """
        try:
            import json
            configs = json.loads(config_json)
            
            conn = db_manager._get_connection()
            cursor = conn.cursor()
            
            imported_count = 0
            for key, value in configs.items():
                # 如果不覆盖且已存在，则跳过
                if not overwrite:
                    cursor.execute('SELECT id FROM system_config WHERE key = ?', (key,))
                    if cursor.fetchone():
                        continue
                
                # 设置配置项
                config_type = self._detect_type(value)
                serialized_value = self._serialize_value(value, config_type)
                
                # 检查是否已存在
                cursor.execute('SELECT id FROM system_config WHERE key = ?', (key,))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute(
                        'UPDATE system_config SET value = ?, type = ?, updated_at = ? WHERE key = ?',
                        (serialized_value, config_type, datetime.now(), key)
                    )
                else:
                    cursor.execute(
                        '''INSERT INTO system_config (key, value, type, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?)''',
                        (key, serialized_value, config_type, datetime.now(), datetime.now())
                    )
                
                imported_count += 1
            
            conn.commit()
            self.logger.info(f"成功导入 {imported_count} 个配置项")
            return imported_count
            
        except json.JSONDecodeError as e:
            self.logger.error(f"导入配置失败: JSON格式错误 - {str(e)}")
            raise DatabaseError(f"导入配置失败: JSON格式错误 - {str(e)}")
        except Exception as e:
            self.logger.error(f"导入配置失败: {str(e)}")
            raise DatabaseError(f"导入配置失败: {str(e)}")


# 创建系统配置实例
system_config = SystemConfig()


# 便捷函数
@handle_errors()
def get_sys_config(key: str, default: Any = None) -> Any:
    """
    获取系统配置的便捷函数
    
    Args:
        key: 配置项键名
        default: 默认值
        
    Returns:
        Any: 配置值
    """
    return system_config.get_config(key, default)


@handle_errors()
def update_system_config(key: str, value: Any, config_type: str = None, description: str = None) -> bool:
    """
    更新系统配置的便捷函数
    
    Args:
        key: 配置项键名
        value: 配置值
        config_type: 配置类型
        description: 配置描述
        
    Returns:
        bool: 更新是否成功
    """
    return system_config.set_config(key, value, config_type, description)


@handle_errors()
def set_sys_config(key: str, value: Any, config_type: str = None, description: str = None) -> bool:
    """
    设置系统配置的便捷函数
    
    Args:
        key: 配置项键名
        value: 配置值
        config_type: 配置类型
        description: 配置描述
        
    Returns:
        bool: 设置是否成功
    """
    return system_config.set_config(key, value, config_type, description)


@handle_errors()
def delete_sys_config(key: str) -> bool:
    """
    删除系统配置的便捷函数
    
    Args:
        key: 配置项键名
        
    Returns:
        bool: 删除是否成功
    """
    return system_config.delete_config(key)


@handle_errors()
def get_all_sys_configs() -> Dict[str, Any]:
    """
    获取所有系统配置的便捷函数
    
    Returns:
        Dict[str, Any]: 所有配置项
    """
    return system_config.get_all_configs()


@handle_errors()
def get_sys_configs_by_prefix(prefix: str) -> Dict[str, Any]:
    """
    获取指定前缀的系统配置的便捷函数
    
    Args:
        prefix: 配置项前缀
        
    Returns:
        Dict[str, Any]: 匹配的配置项
    """
    return system_config.get_configs_by_prefix(prefix)


@handle_errors()
def init_system_config_table():
    """
    初始化系统配置表
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        # 调用SystemConfig实例的内部方法来初始化配置表
        system_config._init_config_table()
        return True
    except Exception as e:
        raise DatabaseError(f"初始化系统配置表失败: {str(e)}")


@handle_errors()
def get_system_config(key: str, default: Any = None) -> Any:
    """
    获取系统配置的便捷函数
    
    Args:
        key: 配置项键名
        default: 默认值
        
    Returns:
        Any: 配置值
    """
    return system_config.get_config(key, default)
