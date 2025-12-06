# 日志管理模块
import logging
import os
import sys
from datetime import datetime
import traceback
from typing import Optional, Union, Dict, Any

# 导入配置管理器（避免循环导入，使用懒加载）

# 日志配置常量
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 日志级别映射
LOG_LEVEL_MAP = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


class LoggerManager:
    """
    日志管理器类，负责配置和获取应用程序日志记录器
    """
    
    # 存储已配置的日志记录器实例
    _loggers = {}
    
    # 默认配置
    _default_config = {
        'log_level': 'info',
        'log_to_file': True,
        'log_directory': None,
        'console_output': True,
        'log_file_max_size': 10 * 1024 * 1024,  # 10MB
        'log_file_backup_count': 5
    }
    
    @classmethod
    def init_logging(cls, config: Optional[Dict[str, Any]] = None):
        """
        初始化日志系统
        
        Args:
            config: 日志配置字典
        """
        # 默认配置
        merged_config = cls._default_config.copy()
        
        # 合并传入的配置
        if config:
            merged_config.update(config)
        
        # 设置根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(LOG_LEVEL_MAP.get(merged_config['log_level'], logging.INFO))
        
        # 清空已有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加控制台处理器
        if merged_config['console_output']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(
                DEFAULT_LOG_FORMAT,
                DEFAULT_LOG_DATE_FORMAT
            ))
            root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        if merged_config['log_to_file']:
            # 确定日志目录
            log_dir = merged_config['log_directory']
            if not log_dir:
                # 默认日志目录: app_root/logs
                app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                log_dir = os.path.join(app_root, 'logs')
            
            # 创建日志目录
            os.makedirs(log_dir, exist_ok=True)
            
            # 日志文件名
            log_filename = os.path.join(
                log_dir,
                f"app_{datetime.now().strftime('%Y%m%d')}.log"
            )
            
            # 设置文件处理器
            file_handler = logging.FileHandler(log_filename, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(
                DEFAULT_LOG_FORMAT,
                DEFAULT_LOG_DATE_FORMAT
            ))
            root_logger.addHandler(file_handler)
        
        # 记录初始化信息
        logger = cls.get_logger('LoggerManager')
        logger.info(f"日志系统初始化完成，日志级别: {merged_config['log_level']}")
        if merged_config['log_to_file']:
            logger.info(f"日志文件目录: {log_dir}")
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器实例
        """
        if name not in cls._loggers:
            # 如果根日志记录器没有配置，先进行默认配置
            if not logging.getLogger().handlers:
                cls.init_logging()
            
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def set_log_level(cls, level: str):
        """
        动态设置日志级别
        
        Args:
            level: 日志级别名称 (debug, info, warning, error, critical)
        """
        log_level = LOG_LEVEL_MAP.get(level.lower(), logging.INFO)
        
        # 更新根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # 更新所有处理器级别
        for handler in root_logger.handlers:
            handler.setLevel(log_level)
        
        # 记录级别变更
        logger = cls.get_logger('LoggerManager')
        logger.info(f"日志级别已更改为: {level}")


# 错误处理装饰器
def handle_errors(logger_name: str = 'default', fallback_return: Any = None):
    """
    错误处理装饰器，用于捕获和记录函数执行过程中的异常
    
    Args:
        logger_name: 日志记录器名称
        fallback_return: 发生异常时的返回值
        
    Returns:
        装饰后的函数
    """
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = LoggerManager.get_logger(logger_name)
            
            try:
                # 记录函数调用信息 - 使用更可靠的方式获取函数名
                try:
                    # 优先使用__qualname__获取完整的函数/方法路径
                    if hasattr(func, '__qualname__'):
                        func_name = f"{func.__module__}.{func.__qualname__}"
                    else:
                        # 回退到__name__
                        func_name = f"{func.__module__}.{getattr(func, '__name__', 'unknown')}"
                except:
                    func_name = "unknown_function"
                
                logger.debug(f"调用函数: {func_name}")
                
                # 执行原函数
                result = func(*args, **kwargs)
                
                logger.debug(f"函数执行成功: {func_name}")
                return result
                
            except Exception as e:
                # 记录异常信息
                try:
                    if hasattr(func, '__qualname__'):
                        func_name = f"{func.__module__}.{func.__qualname__}"
                    else:
                        func_name = f"{func.__module__}.{getattr(func, '__name__', 'unknown')}"
                except:
                    func_name = "unknown_function"
                
                error_stack = traceback.format_exc()
                
                logger.error(f"函数执行异常: {func_name}")
                logger.error(f"异常类型: {type(e).__name__}")
                logger.error(f"异常信息: {str(e)}")
                logger.debug(f"异常堆栈: {error_stack}")
                
                # 返回默认值
                return fallback_return
        
        return wrapper
    
    return decorator


class DatabaseError(Exception):
    """
    数据库操作异常基类
    """
    def __init__(self, message: str, error_code: int = 500, original_exception: Optional[Exception] = None):
        self.message = message
        self.error_code = error_code
        self.original_exception = original_exception
        super().__init__(self.message)
    
    def __str__(self):
        if self.original_exception:
            return f"{self.message} (原始异常: {str(self.original_exception)})"
        return self.message


class DataValidationError(DatabaseError):
    """
    数据验证异常
    """
    def __init__(self, message: str, field_errors: Optional[Dict[str, str]] = None):
        self.field_errors = field_errors or {}
        super().__init__(message, error_code=400)


class NotFoundError(DatabaseError):
    """
    资源未找到异常
    """
    def __init__(self, message: str, resource_type: str = '记录'):
        self.resource_type = resource_type
        super().__init__(message, error_code=404)


class AccessDeniedError(DatabaseError):
    """
    访问权限异常
    """
    def __init__(self, message: str):
        super().__init__(message, error_code=403)


class OperationLogger:
    """
    操作日志记录器，用于记录用户操作
    """
    
    @staticmethod
    def log_operation(user_id: int, operation_type: str, description: str, details: Optional[str] = None):
        """
        记录用户操作日志
        
        Args:
            user_id: 用户ID
            operation_type: 操作类型
            description: 操作描述
            details: 操作详情（JSON格式）
        """
        from src.database.db_manager import execute_query
        
        try:
            # 记录到数据库
            execute_query(
                """INSERT INTO operation_logs (user_id, operation_type, description, details, created_at) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, operation_type, description, details, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            
            # 同时记录到应用日志
            logger = LoggerManager.get_logger('OperationLogger')
            logger.info(f"用户操作: [{operation_type}] 用户ID: {user_id} - {description}")
            if details:
                logger.debug(f"操作详情: {details}")
                
        except Exception as e:
            # 即使数据库记录失败，也要记录到应用日志
            logger = LoggerManager.get_logger('OperationLogger')
            logger.error(f"记录操作日志失败: {str(e)}")


# 注意：日志系统会在首次获取logger时自动初始化


# 导出便捷函数
def get_logger(name: str) -> logging.Logger:
    """
    便捷函数：获取日志记录器
    """
    return LoggerManager.get_logger(name)


def log_error(logger_name: str, message: str, exception: Optional[Exception] = None):
    """
    便捷函数：记录错误信息
    """
    logger = LoggerManager.get_logger(logger_name)
    if exception:
        logger.error(f"{message}: {str(exception)}")
        logger.debug(traceback.format_exc())
    else:
        logger.error(message)


def log_info(logger_name: str, message: str):
    """
    便捷函数：记录信息
    """
    logger = LoggerManager.get_logger(logger_name)
    logger.info(message)


def log_debug(logger_name: str, message: str):
    """
    便捷函数：记录调试信息
    """
    logger = LoggerManager.get_logger(logger_name)
    logger.debug(message)


if __name__ == "__main__":
    # 简单测试
    LoggerManager.init_logging({
        'log_level': 'debug',
        'log_to_file': True
    })
    
    # 测试获取日志记录器
    logger = get_logger('TestLogger')
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.critical("这是一条严重错误信息")
    
    # 测试错误处理装饰器
    @handle_errors('TestErrorHandler')
    def test_function():
        raise ValueError("测试异常")
    
    result = test_function()
    print(f"测试函数返回结果: {result}")
    
    print("日志模块测试完成")