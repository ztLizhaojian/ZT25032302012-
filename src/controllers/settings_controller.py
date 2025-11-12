#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统设置控制器模块
负责管理系统配置、用户偏好和系统参数等设置功能
"""

import json
import logging
import os
from datetime import datetime
import configparser

# 导入数据库和模型
try:
    from src.database.db_manager import execute_query, log_operation, get_db_connection
    from src.models.user import user_model
    DATABASE_READY = True
except ImportError as e:
    logging.error(f"导入数据库模块失败: {str(e)}")
    DATABASE_READY = False

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs', 'settings.log'),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("SettingsController")


class SettingsController:
    """
    系统设置控制器
    管理系统配置、用户偏好和系统参数
    """
    
    def __init__(self):
        """
        初始化系统设置控制器
        """
        # 设置配置文件路径
        self.app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_dir = os.path.join(self.app_root, 'config')
        self.settings_file = os.path.join(self.config_dir, 'app_settings.json')
        self.backup_dir = os.path.join(self.app_root, 'backups')
        
        # 创建必要的目录
        self._ensure_directories()
        
        # 初始化默认设置
        self.default_settings = {
            "app": {
                "app_name": "企业财务账目录入与利润核算系统",
                "version": "1.0.0",
                "language": "zh_CN",
                "theme": "light",
                "auto_backup": True,
                "backup_interval": 7,  # 天
                "last_backup": None,
                "auto_update": False
            },
            "database": {
                "backup_path": self.backup_dir,
                "max_backups": 10,
                "optimize_frequency": 30  # 天
            },
            "interface": {
                "show_toolbar": True,
                "show_statusbar": True,
                "default_view": "dashboard",
                "recent_files_limit": 10,
                "font_size": 12
            },
            "finance": {
                "currency_symbol": "¥",
                "decimal_places": 2,
                "default_account_id": None,
                "tax_rate": 0.13,
                "financial_year_start": "01-01"
            },
            "security": {
                "session_timeout": 30,  # 分钟
                "password_min_length": 6,
                "require_strong_password": False,
                "login_attempts_limit": 5,
                "account_lock_duration": 30  # 分钟
            }
        }
        
        # 加载设置
        self.settings = self.load_settings()
    
    def _ensure_directories(self):
        """
        确保必要的目录存在
        """
        # 创建配置目录
        if not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir)
                logger.info(f"创建配置目录: {self.config_dir}")
            except Exception as e:
                logger.error(f"创建配置目录失败: {str(e)}")
        
        # 创建备份目录
        if not os.path.exists(self.backup_dir):
            try:
                os.makedirs(self.backup_dir)
                logger.info(f"创建备份目录: {self.backup_dir}")
            except Exception as e:
                logger.error(f"创建备份目录失败: {str(e)}")
    
    def load_settings(self):
        """
        从配置文件加载系统设置
        
        Returns:
            dict: 系统设置
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info("系统设置加载成功")
                
                # 合并默认设置（确保新添加的设置项存在）
                return self._merge_settings(self.default_settings, settings)
            else:
                logger.warning("配置文件不存在，使用默认设置")
                return self.default_settings.copy()
        except Exception as e:
            logger.error(f"加载设置失败: {str(e)}")
            return self.default_settings.copy()
    
    def save_settings(self, settings=None):
        """
        保存系统设置到配置文件
        
        Args:
            settings: 要保存的设置，如果为None则保存当前设置
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if settings is None:
                settings = self.settings
            
            # 确保配置目录存在
            self._ensure_directories()
            
            # 保存到文件
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            logger.info("系统设置保存成功")
            
            # 更新当前设置
            self.settings = settings
            
            return True
        except Exception as e:
            logger.error(f"保存设置失败: {str(e)}")
            return False
    
    def _merge_settings(self, default, custom):
        """
        合并默认设置和自定义设置
        
        Args:
            default: 默认设置
            custom: 自定义设置
            
        Returns:
            dict: 合并后的设置
        """
        result = default.copy()
        
        if isinstance(custom, dict):
            for key, value in custom.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    # 递归合并嵌套字典
                    result[key] = self._merge_settings(result[key], value)
                else:
                    # 直接替换
                    result[key] = value
        
        return result
    
    def get_setting(self, key_path, default=None):
        """
        获取指定的设置项
        
        Args:
            key_path: 键路径，支持点号分隔的嵌套键，如 "app.theme"
            default: 默认值，如果键不存在则返回
            
        Returns:
            对应的值或默认值
        """
        keys = key_path.split('.')
        value = self.settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            logger.warning(f"设置项不存在: {key_path}")
            return default
    
    def set_setting(self, key_path, value):
        """
        设置指定的设置项
        
        Args:
            key_path: 键路径，支持点号分隔的嵌套键，如 "app.theme"
            value: 要设置的值
            
        Returns:
            bool: 是否设置成功
        """
        keys = key_path.split('.')
        settings = self.settings.copy()
        
        try:
            # 导航到目标键的父级
            current = settings
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 设置值
            current[keys[-1]] = value
            
            # 保存设置
            return self.save_settings(settings)
        except Exception as e:
            logger.error(f"设置项更新失败: {str(e)}")
            return False
    
    def get_all_settings(self):
        """
        获取所有设置
        
        Returns:
            dict: 所有系统设置
        """
        return self.settings.copy()
    
    def reset_settings(self):
        """
        重置所有设置为默认值
        
        Returns:
            bool: 是否重置成功
        """
        logger.info("重置系统设置为默认值")
        return self.save_settings(self.default_settings.copy())
    
    def export_settings(self, file_path=None):
        """
        导出系统设置
        
        Args:
            file_path: 导出文件路径，如果为None则使用默认路径
            
        Returns:
            str: 导出的文件路径，如果失败则返回None
        """
        try:
            if file_path is None:
                # 生成默认导出文件名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = os.path.join(self.config_dir, f'settings_export_{timestamp}.json')
            
            # 保存设置到导出文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            
            logger.info(f"系统设置导出成功: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"导出设置失败: {str(e)}")
            return None
    
    def import_settings(self, file_path):
        """
        导入系统设置
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            bool: 是否导入成功
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"导入文件不存在: {file_path}")
                return False
            
            # 读取导入文件
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # 验证导入数据的有效性
            if not isinstance(imported_settings, dict):
                logger.error("导入文件格式无效")
                return False
            
            # 合并导入的设置
            merged_settings = self._merge_settings(self.settings, imported_settings)
            
            # 保存合并后的设置
            success = self.save_settings(merged_settings)
            
            if success:
                logger.info(f"系统设置导入成功: {file_path}")
            
            return success
        except Exception as e:
            logger.error(f"导入设置失败: {str(e)}")
            return False
    
    def should_auto_backup(self):
        """
        检查是否需要自动备份
        
        Returns:
            bool: 是否需要备份
        """
        # 检查是否启用了自动备份
        if not self.get_setting('app.auto_backup', False):
            return False
        
        # 获取最后备份时间
        last_backup_str = self.get_setting('app.last_backup')
        if not last_backup_str:
            # 从未备份过，需要备份
            return True
        
        # 计算距离上次备份的天数
        try:
            last_backup = datetime.fromisoformat(last_backup_str)
            days_since_backup = (datetime.now() - last_backup).days
            
            # 检查是否超过了备份间隔
            backup_interval = self.get_setting('app.backup_interval', 7)
            return days_since_backup >= backup_interval
        except Exception as e:
            logger.error(f"计算备份时间失败: {str(e)}")
            return True
    
    def update_last_backup_time(self):
        """
        更新最后备份时间
        
        Returns:
            bool: 是否更新成功
        """
        current_time = datetime.now().isoformat()
        return self.set_setting('app.last_backup', current_time)
    
    def get_backup_directory(self):
        """
        获取备份目录
        
        Returns:
            str: 备份目录路径
        """
        backup_path = self.get_setting('database.backup_path', self.backup_dir)
        
        # 确保备份目录存在
        if not os.path.exists(backup_path):
            try:
                os.makedirs(backup_path)
                logger.info(f"创建备份目录: {backup_path}")
            except Exception as e:
                logger.error(f"创建备份目录失败，使用默认路径: {str(e)}")
                backup_path = self.backup_dir
                # 确保默认备份目录存在
                if not os.path.exists(backup_path):
                    os.makedirs(backup_path)
        
        return backup_path
    
    def cleanup_old_backups(self):
        """
        清理旧备份文件
        
        Returns:
            int: 清理的文件数量
        """
        try:
            backup_dir = self.get_backup_directory()
            max_backups = self.get_setting('database.max_backups', 10)
            
            # 获取所有备份文件
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.endswith('.db') and filename.startswith('backup_'):
                    file_path = os.path.join(backup_dir, filename)
                    # 获取文件的修改时间
                    mtime = os.path.getmtime(file_path)
                    backup_files.append((mtime, file_path))
            
            # 按修改时间排序（最新的在前）
            backup_files.sort(reverse=True)
            
            # 删除超过数量限制的旧备份
            files_to_delete = backup_files[max_backups:]
            deleted_count = 0
            
            for _, file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"删除旧备份文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除备份文件失败: {str(e)}")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"清理旧备份失败: {str(e)}")
            return 0
    
    def load_user_preferences(self, user_id):
        """
        加载用户偏好设置
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 用户偏好设置
        """
        try:
            if not DATABASE_READY:
                return {}
            
            # 从数据库加载用户偏好
            query = "SELECT preferences FROM user_preferences WHERE user_id = ?"
            result = execute_query(query, (user_id,))
            
            if result:
                preferences_json = result[0][0]
                try:
                    return json.loads(preferences_json)
                except json.JSONDecodeError:
                    logger.error(f"用户偏好解析失败: 用户ID {user_id}")
                    return {}
            else:
                # 如果没有用户偏好记录，返回空字典
                return {}
        
        except Exception as e:
            logger.error(f"加载用户偏好失败: {str(e)}")
            return {}
    
    def save_user_preferences(self, user_id, preferences):
        """
        保存用户偏好设置
        
        Args:
            user_id: 用户ID
            preferences: 用户偏好设置
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if not DATABASE_READY:
                return False
            
            # 将偏好设置转换为JSON
            preferences_json = json.dumps(preferences, ensure_ascii=False)
            
            # 使用事务保存
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                # 检查是否存在记录
                cursor.execute("SELECT id FROM user_preferences WHERE user_id = ?", (user_id,))
                if cursor.fetchone():
                    # 更新现有记录
                    cursor.execute(
                        "UPDATE user_preferences SET preferences = ?, updated_at = datetime('now') WHERE user_id = ?",
                        (preferences_json, user_id)
                    )
                else:
                    # 创建新记录
                    cursor.execute(
                        "INSERT INTO user_preferences (user_id, preferences, created_at, updated_at) VALUES (?, ?, datetime('now'), datetime('now'))",
                        (user_id, preferences_json)
                    )
                
                # 提交事务
                conn.commit()
                logger.info(f"用户偏好保存成功: 用户ID {user_id}")
                
                # 记录操作日志
                log_operation(
                    user_id=user_id,
                    action="save_preferences",
                    details="用户偏好设置已更新"
                )
                
                return True
            except Exception as e:
                conn.rollback()
                logger.error(f"保存用户偏好到数据库失败: {str(e)}")
                return False
            finally:
                cursor.close()
                conn.close()
        
        except Exception as e:
            logger.error(f"保存用户偏好失败: {str(e)}")
            return False
    
    def update_user_setting(self, user_id, key, value):
        """
        更新用户的单个偏好设置
        
        Args:
            user_id: 用户ID
            key: 设置键
            value: 设置值
            
        Returns:
            bool: 是否更新成功
        """
        # 获取当前偏好
        preferences = self.load_user_preferences(user_id)
        
        # 更新设置
        preferences[key] = value
        
        # 保存更新后的偏好
        return self.save_user_preferences(user_id, preferences)
    
    def get_system_info(self):
        """
        获取系统信息
        
        Returns:
            dict: 系统信息
        """
        import platform
        import sys
        
        system_info = {
            "app": {
                "name": self.get_setting('app.app_name'),
                "version": self.get_setting('app.version')
            },
            "environment": {
                "python_version": platform.python_version(),
                "operating_system": platform.system(),
                "os_version": platform.version(),
                "architecture": platform.architecture()[0],
                "machine": platform.machine()
            },
            "paths": {
                "app_root": self.app_root,
                "config_dir": self.config_dir,
                "backup_dir": self.backup_dir,
                "database_ready": DATABASE_READY
            }
        }
        
        return system_info


# 创建全局设置控制器实例
settings_controller = SettingsController()


if __name__ == "__main__":
    # 测试设置控制器功能
    print("系统设置控制器测试")
    
    controller = SettingsController()
    
    # 测试获取和设置功能
    print(f"当前主题: {controller.get_setting('app.theme')}")
    
    # 测试更新设置
    success = controller.set_setting('app.theme', 'dark')
    print(f"更新主题结果: {success}")
    print(f"更新后主题: {controller.get_setting('app.theme')}")
    
    # 测试系统信息
    print("系统信息:")
    print(json.dumps(controller.get_system_info(), ensure_ascii=False, indent=2))