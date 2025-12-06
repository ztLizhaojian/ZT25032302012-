"""
数据备份和恢复管理模块
提供数据库的自动备份、手动备份和恢复功能
"""
import os
import shutil
import datetime
import threading
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# 导入配置管理模块
from src.utils.config_manager import get_config

from src.utils.logger import LoggerManager

# 获取日志记录器
def get_logger(name: str):
    """获取日志记录器"""
    return LoggerManager.get_logger(name)

# 错误处理装饰器
def handle_errors(func):
    """
    错误处理装饰器
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = get_logger('backup_manager')
            logger.error(f"{func.__name__}: {str(e)}")
            raise
    return wrapper
# 自定义备份异常类
class BackupError(Exception):
    """备份相关的异常类"""
    pass

# 日志记录器
logger = get_logger('backup_manager')

# 日志记录函数
def log_info(message: str):
    """记录信息日志"""
    logger.info(message)

def log_error(message: str):
    """记录错误日志"""
    logger.error(message)

def log_warning(message: str):
    """记录警告日志"""
    logger.warning(message)


class BackupManager:
    """
    数据库备份和恢复管理器
    提供数据库的备份、恢复、清理过期备份等功能
    """
    
    def __init__(self, db_path: str, backup_dir: str = None):
        """
        初始化备份管理器
        
        Args:
            db_path: 数据库文件路径
            backup_dir: 备份文件存储目录，默认为数据库文件同目录下的backups文件夹
        """
        self.db_path = os.path.abspath(db_path)
        
        # 默认备份目录设置
        if backup_dir is None:
            # 从配置文件获取备份目录
            config_backup_dir = get_config('database.backup.folder', './backups')
            
            # 处理相对路径
            if not os.path.isabs(config_backup_dir):
                db_dir = os.path.dirname(self.db_path)
                self.backup_dir = os.path.join(db_dir, config_backup_dir)
            else:
                self.backup_dir = config_backup_dir
        else:
            self.backup_dir = os.path.abspath(backup_dir)
        
        # 确保备份目录存在
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
        # 备份线程控制
        self._backup_thread = None
        self._stop_event = threading.Event()
        
        log_info(f"备份管理器初始化成功: 数据库路径={self.db_path}, 备份目录={self.backup_dir}")
    
    @handle_errors
    def create_backup(self, description: str = "manual_backup") -> str:
        """
        创建数据库备份
        
        Args:
            description: 备份描述
            
        Returns:
            str: 备份文件路径
            
        Raises:
            IOError: 文件操作失败时抛出
            BackupError: 数据库备份失败时抛出
        """
        # 检查源数据库文件是否存在
        if not os.path.exists(self.db_path):
            raise IOError(f"源数据库文件不存在: {self.db_path}")
        
        # 生成备份文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        db_filename = os.path.basename(self.db_path)
        backup_filename = f"{db_filename}.{description}.{timestamp}.bak"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # 复制数据库文件
            shutil.copy2(self.db_path, backup_path)
            
            # 验证备份文件是否成功创建
            if not os.path.exists(backup_path):
                raise IOError(f"备份文件创建失败: {backup_path}")
            
            log_info(f"数据库备份成功: {backup_path}")
            return backup_path
            
        except Exception as e:
            log_error(f"数据库备份失败: {str(e)}")
            if os.path.exists(backup_path):
                os.remove(backup_path)  # 清理失败的备份文件
            raise IOError(f"数据库备份失败: {str(e)}")
    
    @handle_errors
    def restore_from_backup(self, backup_path: str, overwrite: bool = True) -> bool:
        """
        从备份文件恢复数据库
        
        Args:
            backup_path: 备份文件路径
            overwrite: 是否覆盖现有数据库文件
            
        Returns:
            bool: 恢复是否成功
            
        Raises:
            IOError: 文件操作失败时抛出
            BackupError: 数据库恢复失败时抛出
        """
        # 检查备份文件是否存在
        if not os.path.exists(backup_path):
            raise IOError(f"备份文件不存在: {backup_path}")
        
        # 检查目标数据库文件是否存在
        if os.path.exists(self.db_path) and not overwrite:
            raise IOError(f"目标数据库文件已存在: {self.db_path}，请设置overwrite=True或删除目标文件")
        
        # 备份当前数据库（如果存在）
        if os.path.exists(self.db_path):
            current_backup = self.create_backup("pre_restore_backup")
            log_info(f"恢复前创建了当前数据库备份: {current_backup}")
        
        try:
            # 复制备份文件到目标位置
            shutil.copy2(backup_path, self.db_path)
            
            # 验证恢复是否成功
            if not os.path.exists(self.db_path):
                raise IOError(f"数据库恢复失败，目标文件未创建: {self.db_path}")
            
            log_info(f"数据库恢复成功: 从 {backup_path} 恢复到 {self.db_path}")
            return True
            
        except Exception as e:
            log_error(f"数据库恢复失败: {str(e)}")
            # 如果之前创建了备份，尝试恢复到恢复前的状态
            if 'current_backup' in locals() and os.path.exists(current_backup):
                try:
                    shutil.copy2(current_backup, self.db_path)
                    log_warning(f"恢复失败，已回滚到恢复前的数据库状态")
                except:
                    log_error(f"恢复失败且回滚操作也失败")
            raise IOError(f"数据库恢复失败: {str(e)}")
    
    @handle_errors
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的备份文件
        
        Returns:
            List[Dict]: 备份文件信息列表，包含路径、大小、创建时间等
        """
        backups = []
        
        if not os.path.exists(self.backup_dir):
            log_info(f"备份目录不存在: {self.backup_dir}")
            return backups
        
        try:
            # 获取所有备份文件
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.bak'):
                    backup_path = os.path.join(self.backup_dir, filename)
                    
                    # 获取文件信息
                    file_stat = os.stat(backup_path)
                    file_size = file_stat.st_size
                    created_time = datetime.datetime.fromtimestamp(file_stat.st_ctime)
                    
                    # 解析文件名获取描述和时间戳
                    parts = filename.split('.')
                    description = "manual" if len(parts) < 3 else parts[1]
                    
                    backup_info = {
                        'path': backup_path,
                        'filename': filename,
                        'size': file_size,
                        'size_human': self._format_size(file_size),
                        'created_at': created_time,
                        'created_at_str': created_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'description': description
                    }
                    backups.append(backup_info)
            
            # 按创建时间倒序排序
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            log_info(f"找到 {len(backups)} 个备份文件")
            return backups
            
        except Exception as e:
            log_error(f"列出备份文件失败: {str(e)}")
            raise IOError(f"列出备份文件失败: {str(e)}")
    
    @handle_errors
    def delete_backup(self, backup_path: str) -> bool:
        """
        删除指定的备份文件
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 删除是否成功
        """
        # 检查文件是否存在
        if not os.path.exists(backup_path):
            log_warning(f"要删除的备份文件不存在: {backup_path}")
            return False
        
        # 检查是否是备份目录中的文件
        if not backup_path.startswith(self.backup_dir):
            raise IOError(f"不允许删除备份目录外的文件: {backup_path}")
        
        try:
            os.remove(backup_path)
            log_info(f"备份文件已删除: {backup_path}")
            return True
        except Exception as e:
            log_error(f"删除备份文件失败: {str(e)}")
            raise IOError(f"删除备份文件失败: {str(e)}")
    
    @handle_errors
    def cleanup_old_backups(self, days: int = None, keep_min: int = None) -> int:
        """
        清理过期的备份文件
        
        Args:
            days: 保留最近多少天的备份（默认从配置获取）
            keep_min: 至少保留多少个备份文件（默认从配置获取）
            
        Returns:
            int: 删除的备份文件数量
        """
        # 从配置获取默认值（如果参数未提供）
        if days is None:
            days = get_config('database.backup.keep_days', 7)
        if keep_min is None:
            keep_min = get_config('database.backup.min_keep', 5)
        backups = self.list_backups()
        if len(backups) <= keep_min:
            log_info(f"备份文件数量({len(backups)})少于最小保留数量({keep_min})，不执行清理")
            return 0
        
        # 计算过期时间
        expire_time = datetime.datetime.now() - datetime.timedelta(days=days)
        
        # 筛选出过期的备份文件，但保留最近的keep_min个
        old_backups = []
        for backup in backups[keep_min:]:  # 跳过最新的keep_min个备份
            if backup['created_at'] < expire_time:
                old_backups.append(backup)
        
        # 删除过期的备份文件
        deleted_count = 0
        for backup in old_backups:
            try:
                self.delete_backup(backup['path'])
                deleted_count += 1
            except Exception as e:
                log_error(f"删除备份文件失败: {backup['path']}, 错误: {str(e)}")
        
        log_info(f"备份清理完成，删除了 {deleted_count} 个过期备份文件")
        return deleted_count
    
    @handle_errors
    def start_auto_backup(self, interval_hours: float = None, description: str = "auto_backup"):
        """
        启动自动备份
        
        Args:
            interval_hours: 备份间隔（小时）
            description: 备份描述
        """
        # 从配置获取默认间隔（如果未提供）
        if interval_hours is None:
            interval_hours = get_config('database.backup.interval_hours', 24)
        # 如果已经在运行，先停止
        if self._backup_thread and self._backup_thread.is_alive():
            self.stop_auto_backup()
        
        # 重置停止事件
        self._stop_event.clear()
        
        # 创建并启动备份线程
        def backup_task():
            log_info(f"自动备份任务已启动，间隔 {interval_hours} 小时")
            
            while not self._stop_event.is_set():
                try:
                    self.create_backup(description)
                    self.cleanup_old_backups()
                except Exception as e:
                    log_error(f"自动备份执行失败: {str(e)}")
                
                # 等待下一次备份
                self._stop_event.wait(interval_hours * 3600)
            
            log_info("自动备份任务已停止")
        
        self._backup_thread = threading.Thread(target=backup_task, daemon=True)
        self._backup_thread.start()
        log_info(f"自动备份已启动: 间隔 {interval_hours} 小时")
    
    @handle_errors
    def stop_auto_backup(self):
        """
        停止自动备份
        """
        if self._stop_event.is_set():
            log_info("自动备份已经停止")
            return
        
        # 设置停止事件
        self._stop_event.set()
        
        # 等待线程结束
        if self._backup_thread and self._backup_thread.is_alive():
            self._backup_thread.join(timeout=5)
        
        log_info("自动备份已停止")
    
    def is_auto_backup_running(self) -> bool:
        """
        检查自动备份是否正在运行
        
        Returns:
            bool: 自动备份是否运行中
        """
        return self._backup_thread is not None and self._backup_thread.is_alive() and not self._stop_event.is_set()
    
    def _format_size(self, size_bytes: int) -> str:
        """
        格式化文件大小为人类可读格式
        
        Args:
            size_bytes: 文件大小（字节）
            
        Returns:
            str: 格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


# 便捷函数
def create_backup(db_path: str, backup_dir: str = None, description: str = "manual_backup") -> str:
    """
    创建数据库备份的便捷函数
    
    Args:
        db_path: 数据库文件路径
        backup_dir: 备份目录
        description: 备份描述
        
    Returns:
        str: 备份文件路径
        
    Raises:
        BackupError: 操作失败时抛出
    """
    manager = BackupManager(db_path, backup_dir)
    return manager.create_backup(description)


def restore_backup(db_path: str, backup_path: str, overwrite: bool = True) -> bool:
    """
    从备份恢复数据库的便捷函数
    
    Args:
        db_path: 数据库文件路径
        backup_path: 备份文件路径
        overwrite: 是否覆盖现有数据库
        
    Returns:
        bool: 恢复是否成功
        
    Raises:
        BackupError: 操作失败时抛出
    """
    manager = BackupManager(db_path)
    return manager.restore_from_backup(backup_path, overwrite)


def list_all_backups(db_path: str, backup_dir: str = None) -> List[Dict[str, Any]]:
    """
    列出所有备份的便捷函数
    
    Args:
        db_path: 数据库文件路径
        backup_dir: 备份目录
        
    Returns:
        List[Dict]: 备份文件信息列表
        
    Raises:
        BackupError: 操作失败时抛出
    """
    manager = BackupManager(db_path, backup_dir)
    return manager.list_backups()


def cleanup_backups(db_path: str, backup_dir: str = None, days: int = 7, keep_min: int = 5) -> int:
    """
    清理过期备份的便捷函数
    
    Args:
        db_path: 数据库文件路径
        backup_dir: 备份目录
        days: 保留最近多少天的备份
        keep_min: 至少保留多少个备份
        
    Returns:
        int: 删除的备份数量
        
    Raises:
        BackupError: 操作失败时抛出
    """
    manager = BackupManager(db_path, backup_dir)
    return manager.cleanup_old_backups(days, keep_min)