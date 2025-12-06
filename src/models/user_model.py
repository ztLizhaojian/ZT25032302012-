# 用户认证模型
import sqlite3
import hashlib
import time
import re
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from src.database.db_access import DBAccess
from src.database.db_manager import DB_PATH, log_operation, get_db_path
from src.utils.security import hash_password, verify_password
import logging

# 创建数据访问实例
db_access = DBAccess(DB_PATH)

logger = logging.getLogger(__name__)


class UserModel:
    """用户认证模型类，负责处理用户认证相关的数据库操作"""
    
    # 密码策略配置
    PASSWORD_MIN_LENGTH = 6
    PASSWORD_REGEX_STRONG = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Dict[str, Any]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            dict: 包含认证结果和用户信息
        """
        try:
            # 添加详细日志：打印数据库连接信息
            logger.info(f"开始认证用户: {username}")
            
            # 尝试获取数据库路径信息
            try:
                from src.database.db_manager import DB_PATH
                logger.info(f"使用的数据库路径: {DB_PATH}")
            except Exception as e:
                logger.info(f"无法获取数据库路径: {str(e)}")
            
            # 查询用户信息 - 添加详细日志
            logger.info(f"执行SQL查询: SELECT id, username, password, fullname, email, role, status, last_login FROM users WHERE username = ?")
            logger.info(f"查询参数: username={username}")
            
            result = db_access.execute_query(
                "SELECT id, username, password, fullname, email, role, status, last_login "
                "FROM users WHERE username = ?", 
                (username,), 
                fetch_all=False
            )
            
            # 检查用户是否存在 - 添加详细日志
            logger.info(f"查询结果类型: {type(result)}")
            logger.info(f"查询结果值: {result}")
            
            if not result:
                logger.warning(f"用户不存在: {username}")
                return {
                    'success': False,
                    'message': '用户名或密码错误'
                }
            
            # 正确处理字典格式的查询结果
            logger.info("使用字典键访问用户数据")
            user_id = result['id']
            db_username = result['username']
            password_hash = result['password']
            fullname = result['fullname']
            email = result['email']
            role = result['role']
            status = result['status']  # 正确获取状态值
            last_login = result.get('last_login')
            
            logger.info(f"获取用户数据成功: user_id={user_id}, username={db_username}")
            logger.info(f"状态值详细信息: value='{status}', type={type(status)}, repr={repr(status)}")
            
            # 检查用户状态 - 详细日志版本
            expected_status = 'active'
            logger.info(f"比较状态: 实际='{status}' vs 期望='{expected_status}'")
            logger.info(f"状态比较结果: {status != expected_status}")
            
            if status != expected_status:
                logger.warning(f"用户账户未激活: {username}, 当前状态='{status}'")
                return {
                    'success': False,
                    'message': '账户未激活，请联系管理员'
                }
            
            # 验证密码 - 详细日志
            logger.info("开始密码验证")
            password_valid = verify_password(password, password_hash)
            logger.info(f"密码验证结果: {password_valid}")
            
            if not password_valid:
                # 记录失败尝试
                UserModel._record_login_attempt(user_id, success=False)
                logger.warning(f"密码验证失败: {username}")
                return {
                    'success': False,
                    'message': '用户名或密码错误'
                }
            
            # 记录登录成功
            UserModel._update_last_login(user_id)
            UserModel._record_login_attempt(user_id, success=True)
            
            # 清除失败尝试记录
            UserModel._clear_login_attempts(user_id)
            
            logger.info(f"用户登录成功: {username}")
            
            # 记录操作日志
            try:
                log_operation(
                    user_id,
                    'login',
                    f"用户登录成功: {username}"
                )
            except Exception as e:
                logger.warning(f"记录操作日志失败: {str(e)}")
            
            return {
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user_id,
                    'username': db_username,
                    'fullname': fullname,
                    'email': email,
                    'role': role,
                    'status': status
                }
            }
            
        except Exception as e:
            logger.error(f"用户认证失败: {str(e)}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            return {
                'success': False,
                'message': f'认证过程中发生错误: {str(e)}'
            }
    
    @staticmethod
    def create_user(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新用户
        
        Args:
            data: 包含用户信息的字典
            
        Returns:
            dict: 包含创建结果的信息
        """
        try:
            # 验证用户名
            if not data.get('username') or len(data['username']) < 3:
                return {
                    'success': False,
                    'message': '用户名至少需要3个字符'
                }
            
            # 检查用户名是否已存在
            existing_user = db_access.execute_query(
                "SELECT id FROM users WHERE username = ?",
                (data['username'],),
                fetch_all=False
            )
            
            if existing_user:
                return {
                    'success': False,
                    'message': '用户名已存在'
                }
            
            # 验证密码
            password_validation = UserModel._validate_password(data.get('password'))
            if not password_validation['valid']:
                return password_validation
            
            # 哈希密码
            password_hash = hash_password(data['password'])
            
            # 准备用户数据
            user_data = {
                'username': data['username'],
                'password': password_hash,
                'fullname': data.get('fullname', ''),
                'email': data.get('email', ''),
                'role': data.get('role', 'user'),
                'status': data.get('status', 'active'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 插入用户记录
            db_access.execute_query(
                """INSERT INTO users (username, password, fullname, email, role, status, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_data['username'], user_data['password'], user_data['fullname'],
                 user_data['email'], user_data['role'], user_data['status'], user_data['created_at'])
            )
            
            # 获取插入后的用户ID
            user_id = db_access.execute_query(
                "SELECT last_insert_rowid() as id FROM users",
                fetch_all=False
            )['id']
            
            logger.info(f"用户创建成功: {user_data['username']}, ID: {user_id}")
            
            # 记录操作日志（如果有操作用户ID）
            if data.get('created_by'):
                log_operation(
                    data['created_by'],
                    'create_user',
                    f"创建用户: {user_data['username']}, 角色: {user_data['role']}"
                )
            
            return {
                'success': True,
                'message': '用户创建成功',
                'user_id': user_id
            }
            
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            return {
                'success': False,
                'message': f'创建用户失败: {str(e)}'
            }
    
    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        修改用户密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            dict: 包含修改结果的信息
        """
        try:
            # 获取用户当前密码
            result = execute_query(
                "SELECT password, username FROM users WHERE id = ?",
                (user_id,),
                fetch_all=False
            )
            
            if not result:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            current_password_hash, username = result
            
            # 验证旧密码
            if not verify_password(old_password, current_password_hash):
                return {
                    'success': False,
                    'message': '原密码错误'
                }
            
            # 验证新密码
            password_validation = UserModel._validate_password(new_password)
            if not password_validation['valid']:
                return password_validation
            
            # 哈希新密码
            new_password_hash = hash_password(new_password)
            
            # 更新密码
            execute_query(
                "UPDATE users SET password = ? WHERE id = ?",
                (new_password_hash, user_id)
            )
            
            logger.info(f"用户密码修改成功: {username}")
            
            # 记录操作日志
            log_operation(
                user_id,
                'change_password',
                f"用户密码修改成功: {username}"
            )
            
            return {
                'success': True,
                'message': '密码修改成功'
            }
            
        except Exception as e:
            logger.error(f"修改密码失败: {str(e)}")
            return {
                'success': False,
                'message': f'修改密码失败: {str(e)}'
            }
    
    @staticmethod
    def reset_password(user_id: int, new_password: str, operator_id: int) -> Dict[str, Any]:
        """
        重置用户密码（管理员功能）
        
        Args:
            user_id: 用户ID
            new_password: 新密码
            operator_id: 操作人ID
            
        Returns:
            dict: 包含重置结果的信息
        """
        try:
            # 获取用户信息
            result = execute_query(
                "SELECT username FROM users WHERE id = ?",
                (user_id,),
                fetch_all=False
            )
            
            if not result:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            username = result[0]
            
            # 验证新密码
            password_validation = UserModel._validate_password(new_password)
            if not password_validation['valid']:
                return password_validation
            
            # 哈希新密码
            new_password_hash = hash_password(new_password)
            
            # 更新密码
            execute_query(
                "UPDATE users SET password = ? WHERE id = ?",
                (new_password_hash, user_id)
            )
            
            logger.info(f"用户密码重置成功: {username} (操作人: {operator_id})")
            
            # 记录操作日志
            log_operation(
                operator_id,
                'reset_password',
                f"重置用户密码: {username}"
            )
            
            return {
                'success': True,
                'message': '密码重置成功'
            }
            
        except Exception as e:
            logger.error(f"重置密码失败: {str(e)}")
            return {
                'success': False,
                'message': f'重置密码失败: {str(e)}'
            }
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 用户信息，如果不存在则返回None
        """
        try:
            result = execute_query(
                """SELECT id, username, fullname, email, role, status, created_at, last_login 
                   FROM users WHERE id = ?""",
                (user_id,),
                fetch_all=False
            )
            
            if not result:
                return None
            
            return {
                'id': result[0],
                'username': result[1],
                'fullname': result[2],
                'email': result[3],
                'role': result[4],
                'status': result[5],
                'created_at': result[6],
                'last_login': result[7]
            }
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            return None
    
    @staticmethod
    def get_all_users(role: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有用户列表
        
        Args:
            role: 可选，按角色过滤
            status: 可选，按状态过滤
            
        Returns:
            list: 用户列表
        """
        try:
            # 构建查询条件
            conditions = []
            params = []
            
            if role:
                conditions.append("role = ?")
                params.append(role)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            # 构建SQL
            sql = """SELECT id, username, fullname, email, role, status, created_at, last_login 
                   FROM users"""
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            
            sql += " ORDER BY created_at DESC"
            
            # 执行查询
            results = execute_query(sql, params, fetch_all=True)
            
            # 转换为字典列表
            users = []
            for result in results:
                users.append({
                    'id': result[0],
                    'username': result[1],
                    'fullname': result[2],
                    'email': result[3],
                    'role': result[4],
                    'status': result[5],
                    'created_at': result[6],
                    'last_login': result[7]
                })
            
            return users
            
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            return []
    
    @staticmethod
    def update_user(user_id: int, data: Dict[str, Any], operator_id: int) -> Dict[str, Any]:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            data: 要更新的字段
            operator_id: 操作人ID
            
        Returns:
            dict: 更新结果
        """
        try:
            # 检查用户是否存在
            user = UserModel.get_user_by_id(user_id)
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 构建更新字段
            update_fields = []
            params = []
            
            # 安全字段检查，不允许直接更新密码
            for key, value in data.items():
                if key in ['fullname', 'email', 'role', 'status']:
                    update_fields.append(f"{key} = ?")
                    params.append(value)
            
            if not update_fields:
                return {
                    'success': False,
                    'message': '没有可更新的字段'
                }
            
            # 添加用户ID到参数
            params.append(user_id)
            
            # 执行更新
            execute_query(
                f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?",
                params
            )
            
            logger.info(f"用户信息更新成功: {user['username']} (ID: {user_id})")
            
            # 记录操作日志
            log_operation(
                operator_id,
                'update_user',
                f"更新用户信息: {user['username']} (ID: {user_id})",
                json.dumps(data)
            )
            
            return {
                'success': True,
                'message': '用户信息更新成功'
            }
            
        except Exception as e:
            logger.error(f"更新用户信息失败: {str(e)}")
            return {
                'success': False,
                'message': f'更新用户信息失败: {str(e)}'
            }
    
    @staticmethod
    def delete_user(user_id: int, operator_id: int) -> Dict[str, Any]:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            operator_id: 操作人ID
            
        Returns:
            dict: 删除结果
        """
        try:
            # 不允许删除自己
            if user_id == operator_id:
                return {
                    'success': False,
                    'message': '不允许删除自己的账户'
                }
            
            # 检查用户是否存在
            user = UserModel.get_user_by_id(user_id)
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 检查是否还有其他管理员
            if user['role'] == 'admin':
                admin_count = execute_query(
                    "SELECT COUNT(*) FROM users WHERE role = 'admin' AND status = 'active'",
                    fetch_all=False
                )
                
                if admin_count and admin_count[0] <= 1:
                    return {
                        'success': False,
                        'message': '至少需要保留一个活跃的管理员账户'
                    }
            
            # 软删除 - 更新状态为inactive
            execute_query(
                "UPDATE users SET status = 'inactive' WHERE id = ?",
                (user_id,)
            )
            
            logger.info(f"用户已禁用: {user['username']} (ID: {user_id})")
            
            # 记录操作日志
            log_operation(
                operator_id,
                'delete_user',
                f"禁用用户: {user['username']} (ID: {user_id})"
            )
            
            return {
                'success': True,
                'message': '用户已成功禁用'
            }
            
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return {
                'success': False,
                'message': f'删除用户失败: {str(e)}'
            }
    
    @staticmethod
    def _validate_password(password: str) -> Dict[str, Any]:
        """
        验证密码强度
        
        Args:
            password: 密码
            
        Returns:
            dict: 验证结果
        """
        # 检查密码是否为空
        if not password:
            return {
                'valid': False,
                'message': '密码不能为空'
            }
        
        # 检查密码长度
        if len(password) < UserModel.PASSWORD_MIN_LENGTH:
            return {
                'valid': False,
                'message': f'密码至少需要{UserModel.PASSWORD_MIN_LENGTH}个字符'
            }
        
        # 检查密码强度（可选）
        # 实际应用中可以根据配置决定是否启用强密码策略
        # 这里暂时只做基本检查
        
        return {
            'valid': True
        }
    
    @staticmethod
    def _update_last_login(user_id: int):
        """
        更新用户最后登录时间
        
        Args:
            user_id: 用户ID
        """
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            execute_query(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (current_time, user_id)
            )
        except Exception as e:
            logger.error(f"更新登录时间失败: {str(e)}")
    
    @staticmethod
    def _record_login_attempt(user_id: int, success: bool):
        """
        记录登录尝试（实际实现可能需要创建login_attempts表）
        
        Args:
            user_id: 用户ID
            success: 是否成功
        """
        # 这里简化处理，实际项目中应该创建专门的登录尝试表
        pass
    
    @staticmethod
    def _clear_login_attempts(user_id: int):
        """
        清除登录失败尝试记录
        
        Args:
            user_id: 用户ID
        """
        # 这里简化处理，实际项目中应该清除登录尝试表中的记录
        pass
    
    @staticmethod
    def check_account_locked(username: str) -> Tuple[bool, str]:
        """
        检查账户是否被锁定
        
        Args:
            username: 用户名
            
        Returns:
            tuple: (是否锁定, 锁定原因)
        """
        # 简化实现，实际项目中应该基于登录失败次数和时间来判断
        return False, ""


# 添加必要的导入
from typing import List
import json


# 创建全局用户模型实例
user_model = UserModel()


if __name__ == "__main__":
    # 简单测试
    print("用户模型测试")
    
    # 测试创建用户
    create_result = UserModel.create_user({
        'username': 'test_user',
        'password': 'Test123!',
        'fullname': '测试用户',
        'email': 'test@example.com',
        'role': 'user',
        'created_by': 1
    })
    
    print(f"创建用户结果: {create_result}")