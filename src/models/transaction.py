# 交易记录模型
import datetime
from src.database.db_manager import execute_query, log_operation


class TransactionModel:
    """财务交易记录模型类，负责交易数据的业务逻辑处理"""
    
    @staticmethod
    def create_transaction(data, user_id):
        """
        创建新的交易记录
        
        Args:
            data: 包含交易信息的字典
            user_id: 操作用户ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 处理金额正负号
            amount = float(data['amount'])
            if data['transaction_type'] == 'expense' and amount > 0:
                amount = -amount
            elif data['transaction_type'] == 'income' and amount < 0:
                amount = -amount
            
            # 插入交易记录
            execute_query(
                """INSERT INTO transactions (account_id, category_id, transaction_type, amount, 
                transaction_date, description, reference_number, created_by, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    int(data['account_id']),
                    int(data['category_id']),
                    data['transaction_type'],
                    amount,
                    data['transaction_date'],
                    data.get('description', ''),
                    data.get('reference_number', ''),
                    user_id,
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
            
            # 更新账户余额
            TransactionModel._update_account_balance(int(data['account_id']), amount)
            
            # 记录操作日志
            log_operation(
                user_id,
                'create_transaction',
                f"创建了交易记录: {data['description'] or '未命名'} - {amount}"
            )
            
            return True
            
        except Exception as e:
            print(f"创建交易记录失败: {str(e)}")
            return False
    
    @staticmethod
    def update_transaction(transaction_id, data, user_id):
        """
        更新交易记录
        
        Args:
            transaction_id: 交易记录ID
            data: 包含更新信息的字典
            user_id: 操作用户ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 获取原交易记录
            original_transaction = TransactionModel.get_transaction_by_id(transaction_id)
            if not original_transaction:
                return False
            
            # 处理金额
            amount = float(data['amount'])
            if data['transaction_type'] == 'expense' and amount > 0:
                amount = -amount
            elif data['transaction_type'] == 'income' and amount < 0:
                amount = -amount
            
            # 计算金额差值
            amount_diff = amount - original_transaction['amount']
            
            # 更新交易记录
            execute_query(
                """UPDATE transactions SET account_id = ?, category_id = ?, transaction_type = ?, amount = ?, 
                transaction_date = ?, description = ?, reference_number = ?, updated_by = ?, updated_at = ? 
                WHERE id = ?""",
                (
                    int(data['account_id']),
                    int(data['category_id']),
                    data['transaction_type'],
                    amount,
                    data['transaction_date'],
                    data.get('description', ''),
                    data.get('reference_number', ''),
                    user_id,
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    transaction_id
                )
            )
            
            # 如果账户发生变化，需要调整两个账户的余额
            if int(data['account_id']) != original_transaction['account_id']:
                # 从原账户减去原金额
                TransactionModel._update_account_balance(
                    original_transaction['account_id'], 
                    -original_transaction['amount']
                )
                # 向新账户添加新金额
                TransactionModel._update_account_balance(int(data['account_id']), amount)
            else:
                # 调整原账户的余额
                TransactionModel._update_account_balance(int(data['account_id']), amount_diff)
            
            # 记录操作日志
            log_operation(
                user_id,
                'update_transaction',
                f"更新了交易记录ID: {transaction_id}"
            )
            
            return True
            
        except Exception as e:
            print(f"更新交易记录失败: {str(e)}")
            return False
    
    @staticmethod
    def delete_transaction(transaction_id, user_id):
        """
        删除交易记录
        
        Args:
            transaction_id: 交易记录ID
            user_id: 操作用户ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 获取交易记录信息
            transaction = TransactionModel.get_transaction_by_id(transaction_id)
            if not transaction:
                return False
            
            # 删除交易记录
            execute_query("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            
            # 更新账户余额（减去交易金额）
            TransactionModel._update_account_balance(
                transaction['account_id'], 
                -transaction['amount']
            )
            
            # 记录操作日志
            log_operation(
                user_id,
                'delete_transaction',
                f"删除了交易记录ID: {transaction_id}"
            )
            
            return True
            
        except Exception as e:
            print(f"删除交易记录失败: {str(e)}")
            return False
    
    @staticmethod
    def get_transaction_by_id(transaction_id):
        """
        根据ID获取交易记录
        
        Args:
            transaction_id: 交易记录ID
            
        Returns:
            dict: 交易记录信息
        """
        try:
            result = execute_query(
                """SELECT t.*, a.name as account_name, c.name as category_name 
                FROM transactions t 
                LEFT JOIN accounts a ON t.account_id = a.id 
                LEFT JOIN categories c ON t.category_id = c.id 
                WHERE t.id = ?""",
                (transaction_id,),
                fetch=True
            )
            return result
        except Exception as e:
            print(f"获取交易记录失败: {str(e)}")
            return None
    
    @staticmethod
    def get_transactions(filters=None, limit=100, offset=0):
        """
        查询交易记录列表
        
        Args:
            filters: 过滤条件字典
            limit: 返回记录数限制
            offset: 偏移量
            
        Returns:
            list: 交易记录列表
        """
        try:
            # 构建查询语句
            query = """
            SELECT t.*, a.name as account_name, c.name as category_name 
            FROM transactions t 
            LEFT JOIN accounts a ON t.account_id = a.id 
            LEFT JOIN categories c ON t.category_id = c.id 
            WHERE 1=1
            """
            
            params = []
            
            # 添加过滤条件
            if filters:
                if 'start_date' in filters and filters['start_date']:
                    query += " AND t.transaction_date >= ?"
                    params.append(filters['start_date'])
                
                if 'end_date' in filters and filters['end_date']:
                    query += " AND t.transaction_date <= ?"
                    params.append(filters['end_date'])
                
                if 'account_id' in filters and filters['account_id']:
                    query += " AND t.account_id = ?"
                    params.append(filters['account_id'])
                
                if 'category_id' in filters and filters['category_id']:
                    query += " AND t.category_id = ?"
                    params.append(filters['category_id'])
                
                if 'transaction_type' in filters and filters['transaction_type']:
                    query += " AND t.transaction_type = ?"
                    params.append(filters['transaction_type'])
                
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
            print(f"查询交易记录失败: {str(e)}")
            return []
    
    @staticmethod
    def get_transactions_count(filters=None):
        """
        获取交易记录总数
        
        Args:
            filters: 过滤条件字典
            
        Returns:
            int: 交易记录总数
        """
        try:
            # 构建查询语句
            query = """
            SELECT COUNT(*) as count 
            FROM transactions t 
            WHERE 1=1
            """
            
            params = []
            
            # 添加过滤条件
            if filters:
                if 'start_date' in filters and filters['start_date']:
                    query += " AND t.transaction_date >= ?"
                    params.append(filters['start_date'])
                
                if 'end_date' in filters and filters['end_date']:
                    query += " AND t.transaction_date <= ?"
                    params.append(filters['end_date'])
                
                if 'account_id' in filters and filters['account_id']:
                    query += " AND t.account_id = ?"
                    params.append(filters['account_id'])
                
                if 'category_id' in filters and filters['category_id']:
                    query += " AND t.category_id = ?"
                    params.append(filters['category_id'])
                
                if 'transaction_type' in filters and filters['transaction_type']:
                    query += " AND t.transaction_type = ?"
                    params.append(filters['transaction_type'])
                
                if 'description' in filters and filters['description']:
                    query += " AND t.description LIKE ?"
                    params.append(f"%{filters['description']}%")
            
            # 执行查询
            result = execute_query(query, params, fetch=True)
            
            return result['count'] if result else 0
            
        except Exception as e:
            print(f"查询交易记录总数失败: {str(e)}")
            return 0
    
    @staticmethod
    def get_monthly_summary(year, month):
        """
        获取指定月份的收支汇总
        
        Args:
            year: 年份
            month: 月份
            
        Returns:
            dict: 月度汇总信息
        """
        try:
            # 构建日期范围
            start_date = f"{year}-{month:02d}-01"
            
            # 计算月末日期
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            # 查询收入总额
            income_query = """
            SELECT SUM(amount) as total_income 
            FROM transactions 
            WHERE transaction_type = 'income' 
            AND transaction_date >= ? 
            AND transaction_date < ?
            """
            income_result = execute_query(income_query, (start_date, end_date), fetch=True)
            total_income = income_result['total_income'] if income_result and income_result['total_income'] else 0
            
            # 查询支出总额
            expense_query = """
            SELECT SUM(amount) as total_expense 
            FROM transactions 
            WHERE transaction_type = 'expense' 
            AND transaction_date >= ? 
            AND transaction_date < ?
            """
            expense_result = execute_query(expense_query, (start_date, end_date), fetch=True)
            total_expense = expense_result['total_expense'] if expense_result and expense_result['total_expense'] else 0
            
            # 计算利润（注意支出是负数）
            profit = total_income + total_expense
            
            return {
                'year': year,
                'month': month,
                'total_income': total_income,
                'total_expense': abs(total_expense),  # 返回正数
                'profit': profit,
                'transaction_count': TransactionModel.get_transactions_count({
                    'start_date': start_date,
                    'end_date': f"{end_date}"
                })
            }
            
        except Exception as e:
            print(f"获取月度汇总失败: {str(e)}")
            return {
                'year': year,
                'month': month,
                'total_income': 0,
                'total_expense': 0,
                'profit': 0,
                'transaction_count': 0
            }
    
    @staticmethod
    def _update_account_balance(account_id, amount_change):
        """
        更新账户余额
        
        Args:
            account_id: 账户ID
            amount_change: 余额变化量
        """
        try:
            execute_query(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (amount_change, account_id)
            )
        except Exception as e:
            print(f"更新账户余额失败: {str(e)}")
    
    @staticmethod
    def get_recent_transactions(limit=10):
        """
        获取最近的交易记录
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            list: 最近交易记录列表
        """
        try:
            query = """
            SELECT t.*, a.name as account_name, c.name as category_name 
            FROM transactions t 
            LEFT JOIN accounts a ON t.account_id = a.id 
            LEFT JOIN categories c ON t.category_id = c.id 
            ORDER BY t.created_at DESC 
            LIMIT ?
            """
            
            results = execute_query(query, (limit,), fetch_all=True)
            
            return results
            
        except Exception as e:
            print(f"获取最近交易记录失败: {str(e)}")
            return []
    
    @staticmethod
    def validate_transaction(data):
        """
        验证交易数据的有效性
        
        Args:
            data: 交易数据字典
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        # 验证金额
        try:
            amount = float(data.get('amount', 0))
            if amount == 0:
                return False, "金额不能为零"
        except ValueError:
            return False, "金额必须是数字"
        
        # 验证必填字段
        if not data.get('account_id'):
            return False, "请选择账户"
        
        if not data.get('category_id'):
            return False, "请选择分类"
        
        if not data.get('transaction_date'):
            return False, "请选择交易日期"
        
        # 验证日期格式
        try:
            datetime.datetime.strptime(data['transaction_date'], '%Y-%m-%d')
        except ValueError:
            return False, "日期格式不正确，应为 YYYY-MM-DD"
        
        return True, ""