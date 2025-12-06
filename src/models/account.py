# 账户模型
from src.database.db_manager import execute_query, log_operation
from src.models.user import user_model


class AccountModel:
    """账户模型类，负责账户相关的业务逻辑处理"""
    
    @staticmethod
    def create_account(data, user_id):
        """
        创建新账户
        
        Args:
            data: 包含账户信息的字典
            user_id: 操作用户ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 插入账户记录
            execute_query(
                """INSERT INTO accounts (name, account_type, balance, 
                description, status) 
                VALUES (?, ?, ?, ?, ?)""",
                (
                    data['name'],
                    data['account_type'],
                    float(data.get('initial_balance', 0)),
                    data.get('description', ''),
                    data.get('status', 'active')
                )
            )
            
            # 记录操作日志
            log_operation(
                user_id,
                'create_account',
                f"创建了账户: {data['name']}"
            )
            
            return True
            
        except Exception as e:
            print(f"创建账户失败: {str(e)}")
            return False
    
    @staticmethod
    def update_account(account_id, data, user_id):
        """
        更新账户信息
        
        Args:
            account_id: 账户ID
            data: 包含更新信息的字典
            user_id: 操作用户ID
            
        Returns:
            bool: 操作是否成功
        """
        # 检查用户是否有权限操作该账户
        if not user_model.has_resource_permission('account', account_id, 'write'):
            log_operation(user_id, 'update_account', f"无权限更新账户: {account_id}", success=False)
            return False
            
        try:
            # 更新账户记录
            execute_query(
                """UPDATE accounts SET name = ?, account_type = ?, 
                description = ?, status = ?, updated_by = ?, updated_at = ? 
                WHERE id = ?""",
                (
                    data['name'],
                    data['account_type'],
                    data.get('description', ''),
                    data.get('status', 'active'),
                    user_id,
                    data['updated_at'],
                    account_id
                )
            )
            
            # 记录操作日志
            log_operation(
                user_id,
                'update_account',
                f"更新了账户ID: {account_id}"
            )
            
            return True
            
        except Exception as e:
            print(f"更新账户失败: {str(e)}")
            return False
    
    @staticmethod
    def delete_account(account_id, user_id):
        """
        删除账户
        
        Args:
            account_id: 账户ID
            user_id: 操作用户ID
            
        Returns:
            tuple: (是否成功, 错误信息)
        """
        # 检查用户是否有权限操作该账户
        if not user_model.has_resource_permission('account', account_id, 'delete'):
            log_operation(user_id, 'delete_account', f"无权限删除账户: {account_id}", success=False)
            return False, "无权限操作该账户"
            
        try:
            # 检查账户是否有交易记录
            transaction_count = execute_query(
                "SELECT COUNT(*) as count FROM transactions WHERE account_id = ?",
                (account_id,),
                fetch_all=False
            )
            
            if transaction_count and transaction_count['count'] > 0:
                return False, "该账户存在交易记录，无法删除"
            
            # 获取账户名称用于日志
            account = AccountModel.get_account_by_id(account_id)
            account_name = account['name'] if account else str(account_id)
            
            # 删除账户
            execute_query("DELETE FROM accounts WHERE id = ?", (account_id,))
            
            # 记录操作日志
            log_operation(
                user_id,
                'delete_account',
                f"删除了账户: {account_name}"
            )
            
            return True, ""
            
        except Exception as e:
            print(f"删除账户失败: {str(e)}")
            return False, f"删除失败: {str(e)}"
    
    @staticmethod
    def get_account_by_id(account_id):
        """
        根据ID获取账户信息
        
        Args:
            account_id: 账户ID
            
        Returns:
            dict: 账户信息
        """
        # 检查用户是否有权限查看该账户
        if not user_model.has_resource_permission('account', account_id, 'read'):
            return None
            
        try:
            result = execute_query(
                "SELECT * FROM accounts WHERE id = ?",
                (account_id,),
                fetch_all=False
            )
            return result
            
        except Exception as e:
            print(f"获取账户信息失败: {str(e)}")
            return None
    
    @staticmethod
    def get_all_accounts(filters=None):
        """
        获取所有账户列表
        
        Args:
            filters: 过滤条件字典
            
        Returns:
            list: 账户列表
        """
        try:
            # 构建查询语句
            query = "SELECT * FROM accounts WHERE 1=1"
            params = []
            
            # 添加过滤条件
            if filters:
                if 'account_type' in filters and filters['account_type']:
                    query += " AND account_type = ?"
                    params.append(filters['account_type'])
                
                if 'status' in filters and filters['status']:
                    query += " AND status = ?"
                    params.append(filters['status'])
                
                if 'name' in filters and filters['name']:
                    query += " AND name LIKE ?"
                    params.append(f"%{filters['name']}%")
            
            # 添加排序
            query += " ORDER BY name"
            
            # 执行查询
            results = execute_query(query, params, fetch_all=True)
            
            return results
            
        except Exception as e:
            print(f"获取账户列表失败: {str(e)}")
            return []
    
    @staticmethod
    def get_account_balance_summary():
        """
        获取账户余额汇总
        
        Returns:
            dict: 账户余额汇总信息
        """
        try:
            # 查询总资产
            total_asset = execute_query(
                "SELECT SUM(balance) as total FROM accounts WHERE account_type = 'asset' AND status = 'active'",
                fetch_all=False
            )
            total_asset = total_asset['total'] if total_asset and total_asset['total'] else 0
            
            # 查询总负债
            total_liability = execute_query(
                "SELECT SUM(balance) as total FROM accounts WHERE account_type = 'liability' AND status = 'active'",
                fetch_all=False
            )
            total_liability = total_liability['total'] if total_liability and total_liability['total'] else 0
            
            # 查询总权益
            total_equity = execute_query(
                "SELECT SUM(balance) as total FROM accounts WHERE account_type = 'equity' AND status = 'active'",
                fetch_all=False
            )
            total_equity = total_equity['total'] if total_equity and total_equity['total'] else 0
            
            # 查询总收入账户
            total_income = execute_query(
                "SELECT SUM(balance) as total FROM accounts WHERE account_type = 'income' AND status = 'active'",
                fetch_all=False
            )
            total_income = total_income['total'] if total_income and total_income['total'] else 0
            
            # 查询总支出账户
            total_expense = execute_query(
                "SELECT SUM(balance) as total FROM accounts WHERE account_type = 'expense' AND status = 'active'",
                fetch_all=False
            )
            total_expense = total_expense['total'] if total_expense and total_expense['total'] else 0
            
            return {
                'total_asset': total_asset,
                'total_liability': total_liability,
                'total_equity': total_equity,
                'total_income': total_income,
                'total_expense': total_expense,
                'net_worth': total_asset - total_liability + total_equity,
                'total_accounts': AccountModel.get_accounts_count()
            }
            
        except Exception as e:
            print(f"获取账户余额汇总失败: {str(e)}")
            return {
                'total_asset': 0,
                'total_liability': 0,
                'total_equity': 0,
                'total_income': 0,
                'total_expense': 0,
                'net_worth': 0,
                'total_accounts': 0
            }
    
    @staticmethod
    def get_accounts_count():
        """
        获取账户总数
        
        Returns:
            int: 账户总数
        """
        try:
            result = execute_query(
                "SELECT COUNT(*) as count FROM accounts WHERE status = 'active'",
                fetch_all=False
            )
            return result['count'] if result else 0
            
        except Exception as e:
            print(f"获取账户总数失败: {str(e)}")
            return 0
    
    @staticmethod
    def validate_account(data):
        """
        验证账户数据的有效性
        
        Args:
            data: 账户数据字典
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        # 验证账户名称
        if not data.get('name') or not data['name'].strip():
            return False, "账户名称不能为空"
        
        # 验证账户类型
        valid_types = ['asset', 'liability', 'equity', 'income', 'expense']
        if data.get('account_type') not in valid_types:
            return False, "无效的账户类型"
        
        # 验证初始余额
        if 'initial_balance' in data:
            try:
                balance = float(data['initial_balance'])
            except ValueError:
                return False, "初始余额必须是数字"
        
        return True, ""
    
    @staticmethod
    def get_active_accounts_for_transaction(transaction_type=None):
        """
        获取可用于交易的活跃账户列表
        
        Args:
            transaction_type: 交易类型，可选值为'income'或'expense'
            
        Returns:
            list: 活跃账户列表
        """
        try:
            # 基础查询
            query = """
            SELECT id, name, account_type, balance 
            FROM accounts 
            WHERE status = 'active'
            """
            params = []
            
            # 根据交易类型筛选账户
            if transaction_type == 'expense':
                query += " AND account_type IN ('cash', 'bank', 'credit_card')"
            elif transaction_type == 'income':
                query += " AND account_type IN ('cash', 'bank', 'asset')"
            else:
                # 默认情况返回所有资产和负债类账户
                query += " AND account_type IN ('asset', 'liability')"
            
            # 按名称排序
            query += " ORDER BY name"
            
            # 执行查询
            results = execute_query(query, params, fetch_all=True)
            return results
            
        except Exception as e:
            print(f"获取活跃账户列表失败: {str(e)}")
            return []
    
    @staticmethod
    def get_account_transactions(account_id, filters=None, limit=50, offset=0):
        """
        获取指定账户的交易记录
        
        Args:
            account_id: 账户ID
            filters: 过滤条件字典
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            list: 交易记录列表
        """
        try:
            # 构建查询语句
            query = """
            SELECT t.*, c.name as category_name 
            FROM transactions t 
            LEFT JOIN categories c ON t.category_id = c.id 
            WHERE t.account_id = ?
            """
            
            params = [account_id]
            
            # 添加过滤条件
            if filters:
                if 'start_date' in filters and filters['start_date']:
                    query += " AND t.transaction_date >= ?"
                    params.append(filters['start_date'])
                
                if 'end_date' in filters and filters['end_date']:
                    query += " AND t.transaction_date <= ?"
                    params.append(filters['end_date'])
                
                if 'transaction_type' in filters and filters['transaction_type']:
                    query += " AND t.transaction_type = ?"
                    params.append(filters['transaction_type'])
                
                if 'category_id' in filters and filters['category_id']:
                    query += " AND t.category_id = ?"
                    params.append(filters['category_id'])
                
                if 'description' in filters and filters['description']:
                    query += " AND t.description LIKE ?"
                    params.append(f"%{filters['description']}%")
            
            # 添加排序和分页
            query += " ORDER BY t.transaction_date DESC, t.id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # 执行查询
            results = execute_query(query, params, fetch_all=True)
            
            return results
            
        except Exception as e:
            print(f"获取账户交易记录失败: {str(e)}")
            return []
    
    @staticmethod
    def get_account_transactions_count(account_id, filters=None):
        """
        获取指定账户的交易记录总数
        
        Args:
            account_id: 账户ID
            filters: 过滤条件字典
            
        Returns:
            int: 交易记录总数
        """
        try:
            # 构建查询语句
            query = """
            SELECT COUNT(*) as count 
            FROM transactions t 
            WHERE t.account_id = ?
            """
            
            params = [account_id]
            
            # 添加过滤条件
            if filters:
                if 'start_date' in filters and filters['start_date']:
                    query += " AND t.transaction_date >= ?"
                    params.append(filters['start_date'])
                
                if 'end_date' in filters and filters['end_date']:
                    query += " AND t.transaction_date <= ?"
                    params.append(filters['end_date'])
                
                if 'transaction_type' in filters and filters['transaction_type']:
                    query += " AND t.transaction_type = ?"
                    params.append(filters['transaction_type'])
                
                if 'category_id' in filters and filters['category_id']:
                    query += " AND t.category_id = ?"
                    params.append(filters['category_id'])
                
                if 'description' in filters and filters['description']:
                    query += " AND t.description LIKE ?"
                    params.append(f"%{filters['description']}%")
            
            # 执行查询
            result = execute_query(query, params, fetch_all=True)
            
            return result[0]['count'] if result else 0
            
        except Exception as e:
            print(f"获取账户交易记录总数失败: {str(e)}")
            return 0
    
    @staticmethod
    def get_account_transaction_summary(account_id, start_date=None, end_date=None):
        """
        获取指定账户的交易汇总信息
        
        Args:
            account_id: 账户ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            dict: 交易汇总信息
        """
        try:
            # 构建基础查询
            query = """
            SELECT 
                SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as total_expense,
                COUNT(*) as transaction_count
            FROM transactions 
            WHERE account_id = ?
            """
            
            params = [account_id]
            
            # 添加日期过滤
            if start_date:
                query += " AND transaction_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND transaction_date <= ?"
                params.append(end_date)
            
            # 执行查询
            result = execute_query(query, params, fetch_all=True)
            
            if result:
                return {
                    'total_income': result[0]['total_income'] or 0,
                    'total_expense': abs(result[0]['total_expense'] or 0),  # 返回正数
                    'net_change': (result[0]['total_income'] or 0) + (result[0]['total_expense'] or 0),
                    'transaction_count': result[0]['transaction_count'] or 0
                }
            
            return {
                'total_income': 0,
                'total_expense': 0,
                'net_change': 0,
                'transaction_count': 0
            }
            
        except Exception as e:
            print(f"获取账户交易汇总失败: {str(e)}")
            return {
                'total_income': 0,
                'total_expense': 0,
                'net_change': 0,
                'transaction_count': 0
            }