"""
系统配置管理模块
负责管理和维护应用程序的所有配置项，提供配置的读取、更新、缓存和验证功能
"""
import json
import os
import threading
from typing import Any, Dict, Optional, Union, List
from pathlib import Path

# 延迟导入避免循环依赖
# 实际使用时在需要的方法内导入
# from src.models.system_config import get_system_config, update_system_config

from src.utils.logger import LoggerManager

# 自定义异常
class ConfigError(Exception):
    """配置错误异常类"""
    pass

# 辅助函数：获取日志记录器
def get_logger(name: str):
    """获取日志记录器"""
    return LoggerManager.get_logger(name)

# 错误处理装饰器
def handle_errors(error_types=None):
    """
    错误处理装饰器，捕获和记录异常
    
    Args:
        error_types: 要捕获的异常类型列表
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger('config_manager')
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 如果指定了错误类型且异常不在列表中，则重新抛出
                if error_types and not any(isinstance(e, error_type) for error_type in error_types):
                    raise
                logger.error(f"{func.__name__} 执行失败: {str(e)}")
                raise
        return wrapper
    return decorator

# 默认配置文件路径
DEFAULT_CONFIG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'config'
)
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, 'config.json')

# 默认配置项
DEFAULT_CONFIG = {
    'database': {
        'path': './data/finance_system.db',
        'backup': {
            'enabled': True,
            'interval_hours': 24,
            'keep_days': 7,
            'min_keep': 5,
            'folder': './data/backups'
        }
    },
    'logging': {
        'level': 'INFO',
        'file': './logs/finance_system.log',
        'max_bytes': 10485760,  # 10MB
        'backup_count': 5
    },
    'app': {
        'name': 'Finance Management System',
        'version': '1.0.0',
        'debug': False,
        'max_transactions_per_page': 50,
        'currency_symbol': '¥'
    },
    'security': {
        'password_min_length': 8,
        'session_timeout_minutes': 30,
        'allow_guest_access': False
    }
}

# 配置验证规则
CONFIG_VALIDATION_RULES = {
    'database': {
        'path': {'type': str, 'required': True},
        'backup': {
            'enabled': {'type': bool, 'required': True},
            'interval_hours': {'type': (int, float), 'required': True, 'min': 0.1},
            'keep_days': {'type': int, 'required': True, 'min': 1},
            'min_keep': {'type': int, 'required': True, 'min': 1},
            'folder': {'type': str, 'required': True}
        }
    },
    'logging': {
        'level': {'type': str, 'required': True, 'allowed': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']},
        'file': {'type': str, 'required': True},
        'max_bytes': {'type': int, 'required': True, 'min': 1024},
        'backup_count': {'type': int, 'required': True, 'min': 1}
    },
    'app': {
        'name': {'type': str, 'required': True},
        'version': {'type': str, 'required': True},
        'debug': {'type': bool, 'required': True},
        'max_transactions_per_page': {'type': int, 'required': True, 'min': 1},
        'currency_symbol': {'type': str, 'required': True}
    },
    'security': {
        'password_min_length': {'type': int, 'required': True, 'min': 4},
        'session_timeout_minutes': {'type': int, 'required': True, 'min': 5},
        'allow_guest_access': {'type': bool, 'required': True}
    }
}


class ConfigManager:
    """
    配置管理器类
    提供配置的读取、更新、缓存和验证功能
    """
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        """单例模式实现"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化配置管理器"""
        self.logger = get_logger('config_manager')
        self.config_file = DEFAULT_CONFIG_FILE
        self._config = {}
        self._config_loaded = False
        self._last_modified = 0
        self._db_config_loaded = False
        self._db_config = {}
        self._db_last_updated = 0
        
        # 确保配置目录存在
        os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
        
        # 尝试加载配置文件，如果不存在则创建默认配置
        if not os.path.exists(self.config_file):
            self._create_default_config()
    
    @handle_errors(error_types=[ConfigError])
    def _create_default_config(self):
        """
        创建默认配置文件
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 写入默认配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"默认配置文件已创建: {self.config_file}")
        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {str(e)}")
            raise ConfigError(f"创建默认配置文件失败: {str(e)}")
    
    def _load_db_config(self):
        """从数据库加载配置
        
        Returns:
            Dict: 数据库中的配置字典
        """
        try:
            # 导入避免循环依赖
            from src.models.system_config import get_system_config
            
            # 从数据库获取所有系统配置
            db_config_items = get_system_config() or []
            
            # 确保db_config_items是列表格式
            if not isinstance(db_config_items, list):
                self.logger.warning("数据库返回的配置格式不正确，应为列表类型")
                db_config_items = []
            
            # 转换为嵌套字典格式
            db_config = {}
            for item in db_config_items:
                try:
                    if isinstance(item, dict) and 'key' in item:
                        key = item['key']
                        value = json.loads(item['value']) if item.get('value') else None
                        
                        # 支持嵌套键路径
                        keys = key.split('.')
                        config = db_config
                        
                        for k in keys[:-1]:
                            if k not in config:
                                config[k] = {}
                            config = config[k]
                        
                        config[keys[-1]] = value
                except Exception as item_error:
                    self.logger.warning(f"处理配置项时出错: {str(item_error)}")
                    continue
            
            self._db_config = db_config
            self._db_config_loaded = True
            self._db_last_updated = os.path.getmtime(self.config_file) if os.path.exists(self.config_file) else 0
            
            self.logger.info("数据库配置已成功加载")
            return db_config
            
        except Exception as e:
            self.logger.warning(f"加载数据库配置失败: {str(e)}，将仅使用文件配置")
            self._db_config = {}
            self._db_config_loaded = True  # 标记为已尝试加载，避免重复尝试
            return {}
    
    @handle_errors(error_types=[ConfigError])
    def load_config(self, config_file: str = None, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载配置（混合文件和数据库配置）
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
            force_reload: 是否强制重新加载配置
            
        Returns:
            Dict: 合并后的配置字典
            
        Raises:
            ConfigError: 加载配置失败时抛出
        """
        if config_file is not None:
            self.config_file = os.path.abspath(config_file)
        
        try:
            # 检查文件是否存在
            if not os.path.exists(self.config_file):
                self._create_default_config()
            
            # 检查是否需要重新加载文件配置
            reload_file = force_reload
            if not reload_file and self._config_loaded:
                current_mtime = os.path.getmtime(self.config_file)
                reload_file = current_mtime > self._last_modified
            
            # 加载文件配置
            if reload_file:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # 验证配置
                self._validate_config(file_config)
                
                # 合并默认配置（如果有缺失项）
                file_config = self._merge_with_defaults(file_config)
                
                # 更新缓存和时间戳
                self._config = file_config
                self._config_loaded = True
                self._last_modified = os.path.getmtime(self.config_file)
                
                self.logger.info(f"配置文件已成功加载: {self.config_file}")
            
            # 加载数据库配置（如果未加载或强制重新加载）
            if not self._db_config_loaded or force_reload:
                self._load_db_config()
            
            # 合并文件配置和数据库配置（数据库配置优先级更高）
            merged_config = self._merge_configs(self._config, self._db_config)
            
            return merged_config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件格式错误: {str(e)}")
            raise ConfigError(f"配置文件格式错误: {str(e)}")
        except Exception as e:
            self.logger.error(f"加载配置失败: {str(e)}")
            raise ConfigError(f"加载配置失败: {str(e)}")
    
    def _merge_configs(self, file_config: Dict[str, Any], db_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并文件配置和数据库配置
        数据库配置优先级高于文件配置
        
        Args:
            file_config: 文件配置
            db_config: 数据库配置
            
        Returns:
            Dict: 合并后的配置
        """
        def merge_recursive(base: Dict, override: Dict) -> Dict:
            """递归合并配置字典"""
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_recursive(result[key], value)
                else:
                    result[key] = value
            return result
        
        return merge_recursive(file_config, db_config)
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置的有效性
        
        Args:
            config: 配置字典
            
        Returns:
            bool: 配置是否有效
            
        Raises:
            ConfigError: 配置无效时抛出
        """
        try:
            self._validate_recursive(config, CONFIG_VALIDATION_RULES)
            return True
        except Exception as e:
            raise ConfigError(f"配置验证失败: {str(e)}")
    
    def _validate_recursive(self, config: Dict[str, Any], rules: Dict[str, Any], path: str = ''):
        """
        递归验证配置项
        
        Args:
            config: 配置字典
            rules: 验证规则
            path: 当前路径
        """
        # 检查必需的配置项
        for key, rule in rules.items():
            full_path = f"{path}.{key}" if path else key
            
            # 检查配置项是否存在
            if key not in config:
                if isinstance(rule, dict) and rule.get('required', True):
                    raise ValueError(f"缺少必需的配置项: {full_path}")
                continue
            
            # 检查配置项类型
            config_value = config[key]
            expected_type = rule.get('type') if isinstance(rule, dict) else dict
            
            if isinstance(expected_type, type):
                if not isinstance(config_value, expected_type):
                    raise ValueError(f"配置项 {full_path} 类型错误，期望 {expected_type.__name__}，实际 {type(config_value).__name__}")
            elif isinstance(expected_type, tuple):
                if not isinstance(config_value, expected_type):
                    expected_names = ', '.join([t.__name__ for t in expected_type])
                    raise ValueError(f"配置项 {full_path} 类型错误，期望 {expected_names}，实际 {type(config_value).__name__}")
            
            # 递归验证嵌套配置
            if isinstance(config_value, dict) and isinstance(rule, dict) and 'type' not in rule:
                self._validate_recursive(config_value, rule, full_path)
            
            # 检查值范围和约束
            if isinstance(rule, dict):
                if 'min' in rule and config_value < rule['min']:
                    raise ValueError(f"配置项 {full_path} 值太小，最小允许值为 {rule['min']}")
                if 'max' in rule and config_value > rule['max']:
                    raise ValueError(f"配置项 {full_path} 值太大，最大允许值为 {rule['max']}")
                if 'allowed' in rule and config_value not in rule['allowed']:
                    allowed_values = ', '.join([str(v) for v in rule['allowed']])
                    raise ValueError(f"配置项 {full_path} 值不在允许范围内，允许值为: {allowed_values}")
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        将配置与默认配置合并
        
        Args:
            config: 用户配置
            
        Returns:
            Dict: 合并后的配置
        """
        def merge_dicts(default: Dict, user: Dict) -> Dict:
            """递归合并字典"""
            result = default.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            return result
        
        return merge_dicts(DEFAULT_CONFIG, config)
    
    @handle_errors(error_types=[ConfigError])
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项的值（从合并后的配置中）
        
        Args:
            key: 配置项键（支持点号分隔的嵌套路径，如 'database.path'）
            default: 默认值，如果配置项不存在则返回
            
        Returns:
            Any: 配置项的值或默认值
        """
        # 确保配置已加载
        if not self._config_loaded:
            self.load_config()
        
        # 合并配置
        merged_config = self._merge_configs(self._config, self._db_config)
        
        # 解析键路径
        keys = key.split('.')
        value = merged_config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    @handle_errors(error_types=[ConfigError])
    def set(self, key: str, value: Any, save: bool = True, source: str = 'database') -> bool:
        """
        设置配置项的值
        
        Args:
            key: 配置项键（支持点号分隔的嵌套路径）
            value: 配置值
            save: 是否立即保存
            source: 保存源，'database' 或 'file'
            
        Returns:
            bool: 设置是否成功
            
        Raises:
            ConfigError: 设置配置失败时抛出
        """
        # 确保配置已加载
        if not self._config_loaded:
            self.load_config()
        
        try:
            # 获取当前的完整配置
            temp_config = self._merge_configs(self._config, self._db_config)
            keys = key.split('.')
            config = temp_config
            
            # 导航到目标键的父级，确保保留现有配置结构
            for k in keys[:-1]:
                if k not in config:
                    # 如果父级不存在，使用默认配置的结构
                    if k in DEFAULT_CONFIG and isinstance(DEFAULT_CONFIG[k], dict):
                        config[k] = DEFAULT_CONFIG[k].copy()
                    else:
                        config[k] = {}
                elif not isinstance(config[k], dict):
                    # 如果父级存在但不是字典，将其转换为字典
                    config[k] = {}
                config = config[k]
            
            # 设置值进行验证
            config[keys[-1]] = value
            
            # 在验证前将temp_config与默认配置合并，确保所有必需的配置项都存在
            temp_config = self._merge_with_defaults(temp_config)
            self._validate_config(temp_config)
            
            # 根据源保存配置
            if save:
                if source == 'database':
                    # 导入避免循环依赖
                    from src.models.system_config import update_system_config
                    
                    # 保存到数据库
                    json_value = json.dumps(value) if value is not None else None
                    update_system_config(key, json_value)
                    
                    # 更新内存中的数据库配置
                    self._load_db_config()
                    
                    self.logger.info(f"配置项 {key} 已保存到数据库: {value}")
                else:
                    # 保存到文件
                    config = self._config
                    for k in keys[:-1]:
                        if k not in config or not isinstance(config[k], dict):
                            config[k] = {}
                        config = config[k]
                    config[keys[-1]] = value
                    self.save_config()
                    
                    self.logger.info(f"配置项 {key} 已保存到文件: {value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"设置配置项 {key} 失败: {str(e)}")
            raise ConfigError(f"设置配置项 {key} 失败: {str(e)}")
    
    @handle_errors(error_types=[ConfigError])
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存是否成功
            
        Raises:
            ConfigError: 保存配置失败时抛出
        """
        try:
            # 在验证前将配置与默认配置合并，确保所有必需的配置项都存在
            self._config = self._merge_with_defaults(self._config)
            
            # 验证配置
            self._validate_config(self._config)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 写入文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            
            # 更新时间戳
            self._last_modified = os.path.getmtime(self.config_file)
            
            self.logger.info(f"配置已成功保存到: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
            raise ConfigError(f"保存配置文件失败: {str(e)}")
    
    @handle_errors(error_types=[ConfigError])
    def reset_to_defaults(self) -> bool:
        """
        重置配置为默认值
        
        Returns:
            bool: 重置是否成功
            
        Raises:
            ConfigError: 重置配置失败时抛出
        """
        try:
            self._config = DEFAULT_CONFIG.copy()
            self.save_config()
            self.logger.info("配置已重置为默认值")
            return True
        except Exception as e:
            self.logger.error(f"重置配置失败: {str(e)}")
            raise ConfigError(f"重置配置失败: {str(e)}")
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置项（合并文件和数据库配置）
        
        Returns:
            Dict: 所有配置项
        """
        if not self._config_loaded:
            self.load_config()
        
        # 返回合并后的配置
        return self._merge_configs(self._config, self._db_config)
    
    @handle_errors(error_types=[ConfigError])
    def sync_config_to_db(self) -> bool:
        """
        将文件配置同步到数据库
        
        Returns:
            bool: 同步是否成功
        """
        try:
            # 导入避免循环依赖
            from src.models.system_config import update_system_config
            
            # 扁平化配置字典
            def flatten_dict(d: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
                """递归扁平化字典"""
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}.{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key).items())
                    else:
                        items.append((new_key, v))
                return dict(items)
            
            # 扁平化配置
            flat_config = flatten_dict(self._config)
            
            # 同步到数据库
            for key, value in flat_config.items():
                json_value = json.dumps(value) if value is not None else None
                update_system_config(key, json_value)
            
            # 重新加载数据库配置
            self._load_db_config()
            
            self.logger.info("文件配置已成功同步到数据库")
            return True
            
        except Exception as e:
            self.logger.error(f"同步配置到数据库失败: {str(e)}")
            raise ConfigError(f"同步配置到数据库失败: {str(e)}")
    
    @handle_errors(error_types=[ConfigError])
    def sync_config_to_file(self) -> bool:
        """
        将数据库配置同步到文件
        
        Returns:
            bool: 同步是否成功
        """
        try:
            # 确保数据库配置已加载
            if not self._db_config_loaded:
                self._load_db_config()
            
            # 合并数据库配置到文件配置
            merged_config = self._merge_configs(self._config, self._db_config)
            
            # 保存到文件
            self._config = merged_config
            self.save_config()
            
            self.logger.info("数据库配置已成功同步到文件")
            return True
            
        except Exception as e:
            self.logger.error(f"同步配置到文件失败: {str(e)}")
            raise ConfigError(f"同步配置到文件失败: {str(e)}")
    
    def refresh(self) -> bool:
        """
        重新加载配置文件
        
        Returns:
            bool: 刷新是否成功
        """
        try:
            self._config_loaded = False
            self.load_config()
            return True
        except Exception:
            return False


# 创建全局配置管理器实例
config_manager = ConfigManager()


# 便捷函数
@handle_errors(error_types=[ConfigError])
def get_config(key: str = None, default: Any = None) -> Any:
    """
    获取配置项的便捷函数
    
    Args:
        key: 配置项键，如果为None则返回所有配置
        default: 默认值
        
    Returns:
        Any: 配置值或默认值
    """
    if key is None:
        return config_manager.get_all()
    return config_manager.get(key, default)


@handle_errors(error_types=[ConfigError])
def set_config(key: str, value: Any, save: bool = True, source: str = 'database') -> bool:
    """
    设置配置项的便捷函数
    
    Args:
        key: 配置项键
        value: 配置值
        save: 是否立即保存
        source: 保存源，'database' 或 'file'
        
    Returns:
        bool: 设置是否成功
    """
    return config_manager.set(key, value, save, source)


@handle_errors(error_types=[ConfigError])
def save_config() -> bool:
    """
    保存配置的便捷函数
    
    Returns:
        bool: 保存是否成功
    """
    return config_manager.save_config()


@handle_errors(error_types=[ConfigError])
def load_config(config_file: str = None) -> Dict[str, Any]:
    """
    加载配置的便捷函数
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        Dict: 配置字典
    """
    return config_manager.load_config(config_file)


@handle_errors(error_types=[ConfigError])
def reset_config() -> bool:
    """
    重置配置为默认值的便捷函数
    
    Returns:
        bool: 重置是否成功
    """
    return config_manager.reset_to_defaults()


@handle_errors(error_types=[ConfigError])
def refresh_config() -> bool:
    """
    刷新配置的便捷函数
    
    Returns:
        bool: 刷新是否成功
    """
    return config_manager.refresh()


@handle_errors(error_types=[ConfigError])
def sync_config_to_db() -> bool:
    """
    将文件配置同步到数据库的便捷函数
    
    Returns:
        bool: 同步是否成功
    """
    return config_manager.sync_config_to_db()


@handle_errors(error_types=[ConfigError])
def sync_config_to_file() -> bool:
    """
    将数据库配置同步到文件的便捷函数
    
    Returns:
        bool: 同步是否成功
    """
    return config_manager.sync_config_to_file()
