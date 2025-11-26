# 报表模型
import datetime
from src.database.db_manager import execute_query


class ReportModel:
    """报表模型类，负责报表生成和利润核算的业务逻辑"""
    
    @staticmethod
    def calculate_profit(start_date, end_date):
        """
        计算指定时间段的利润
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 利润核算结果
        """
        try:
            # 查询收入总额
            income_query = """
            SELECT SUM(amount) as total_income 
            FROM transactions 
            WHERE transaction_type = 'income' 
            AND transaction_date >= ? 
            AND transaction_date <= ?
            """
            income_result = execute_query(income_query, (start_date, end_date), fetch=True)
            total_income = income_result['total_income'] if income_result and income_result['total_income'] else 0
            
            # 查询支出总额
            expense_query = """
            SELECT SUM(amount) as total_expense 
            FROM transactions 
            WHERE transaction_type = 'expense' 
            AND transaction_date >= ? 
            AND transaction_date <= ?
            """
            expense_result = execute_query(expense_query, (start_date, end_date), fetch=True)
            total_expense = expense_result['total_expense'] if expense_result and expense_result['total_expense'] else 0
            
            # 计算净利润
            net_profit = total_income + total_expense  # 注意：expense是负数
            
            # 计算毛利率
            gross_margin = 0
            if total_income > 0:
                gross_margin = (net_profit / total_income) * 100
            
            # 交易笔数
            transaction_count = execute_query(
                "SELECT COUNT(*) as count FROM transactions WHERE transaction_date >= ? AND transaction_date <= ?",
                (start_date, end_date),
                fetch=True
            )['count']
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'total_income': total_income,
                'total_expense': abs(total_expense),  # 返回正数
                'net_profit': net_profit,
                'gross_margin': gross_margin,
                'transaction_count': transaction_count
            }
            
        except Exception as e:
            print(f"计算利润失败: {str(e)}")
            return {
                'start_date': start_date,
                'end_date': end_date,
                'total_income': 0,
                'total_expense': 0,
                'net_profit': 0,
                'gross_margin': 0,
                'transaction_count': 0
            }
    
    @staticmethod
    def generate_income_statement(start_date, end_date):
        """
        生成利润表（损益表）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 利润表数据
        """
        try:
            # 查询收入明细
            income_details = execute_query(
                """
                SELECT c.name as category, SUM(t.amount) as amount
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.transaction_type = 'income' 
                AND t.transaction_date BETWEEN ? AND ?
                GROUP BY c.name
                ORDER BY amount DESC
                """,
                (start_date, end_date),
                fetchall=True
            )
            
            # 查询支出明细
            expense_details = execute_query(
                """
                SELECT c.name as category, SUM(t.amount) as amount
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.transaction_type = 'expense' 
                AND t.transaction_date BETWEEN ? AND ?
                GROUP BY c.name
                ORDER BY amount DESC
                """,
                (start_date, end_date),
                fetchall=True
            )
            
            # 计算总收入和总支出
            total_income = sum(item['amount'] for item in income_details) if income_details else 0
            total_expense = sum(item['amount'] for item in expense_details) if expense_details else 0
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'total_income': total_income,
                'total_expense': total_expense,
                'net_profit': total_income - total_expense,
                'income_details': income_details or [],
                'expense_details': expense_details or []
            }
            
        except Exception as e:
            print(f"生成利润表失败: {str(e)}")
            # 返回默认值以避免程序崩溃
            return {
                'start_date': start_date,
                'end_date': end_date,
                'total_income': 0,
                'total_expense': 0,
                'net_profit': 0,
                'income_details': [],
                'expense_details': []
            }
    
    @staticmethod
    def generate_balance_sheet(as_of_date):
        """
        生成资产负债表
        
        Args:
            as_of_date: 报表日期
            
        Returns:
            dict: 资产负债表数据
        """
        try:
            # 获取资产账户
            asset_accounts = execute_query(
                """
                SELECT id, name, account_type, balance 
                FROM accounts 
                WHERE account_type = 'asset' 
                AND status = 'active' 
                ORDER BY name
                """,
                fetch_all=True
            )
            
            # 获取负债账户
            liability_accounts = execute_query(
                """
                SELECT id, name, account_type, balance 
                FROM accounts 
                WHERE account_type = 'liability' 
                AND status = 'active' 
                ORDER BY name
                """,
                fetch_all=True
            )
            
            # 获取权益账户
            equity_accounts = execute_query(
                """
                SELECT id, name, account_type, balance 
                FROM accounts 
                WHERE account_type = 'equity' 
                AND status = 'active' 
                ORDER BY name
                """,
                fetch_all=True
            )
            
            # 计算资产总额
            total_assets = sum(account['balance'] for account in asset_accounts) if asset_accounts else 0
            
            # 计算负债总额
            total_liabilities = sum(account['balance'] for account in liability_accounts) if liability_accounts else 0
            
            # 计算权益总额
            total_equity = sum(account['balance'] for account in equity_accounts) if equity_accounts else 0
            
            # 验证会计等式：资产 = 负债 + 所有者权益
            balance_valid = abs(total_assets - (total_liabilities + total_equity)) < 0.01
            
            return {
                'as_of_date': as_of_date,
                'asset_accounts': asset_accounts,
                'liability_accounts': liability_accounts,
                'equity_accounts': equity_accounts,
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'total_equity': total_equity,
                'balance_valid': balance_valid
            }
            
        except Exception as e:
            print(f"生成资产负债表失败: {str(e)}")
            return {
                'as_of_date': as_of_date,
                'asset_accounts': [],
                'liability_accounts': [],
                'equity_accounts': [],
                'total_assets': 0,
                'total_liabilities': 0,
                'total_equity': 0,
                'balance_valid': False
            }
    
    @staticmethod
    def generate_cash_flow_statement(start_date, end_date):
        """
        生成现金流量表（简化版）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 现金流量表数据
        """
        try:
            # 获取经营活动现金流（这里简化处理，使用收入减去支出）
            operating_cash_flow = ReportModel.calculate_profit(start_date, end_date)['net_profit']
            
            # 获取投资活动现金流（这里简化处理，使用资产类账户的变动）
            # 在实际应用中，可能需要更复杂的逻辑来区分投资活动
            investing_cash_flow = execute_query(
                """
                SELECT SUM(amount) as total 
                FROM transactions t 
                JOIN accounts a ON t.account_id = a.id 
                WHERE a.account_type = 'asset' 
                AND t.transaction_date >= ? 
                AND t.transaction_date <= ?
                """,
                (start_date, end_date),
                fetch=True
            )
            investing_cash_flow = investing_cash_flow['total'] if investing_cash_flow and investing_cash_flow['total'] else 0
            
            # 获取筹资活动现金流（这里简化处理，使用负债和权益类账户的变动）
            financing_cash_flow = execute_query(
                """
                SELECT SUM(amount) as total 
                FROM transactions t 
                JOIN accounts a ON t.account_id = a.id 
                WHERE a.account_type IN ('liability', 'equity') 
                AND t.transaction_date >= ? 
                AND t.transaction_date <= ?
                """,
                (start_date, end_date),
                fetch=True
            )
            financing_cash_flow = financing_cash_flow['total'] if financing_cash_flow and financing_cash_flow['total'] else 0
            
            # 计算现金净增加额
            net_cash_increase = operating_cash_flow + investing_cash_flow + financing_cash_flow
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'operating_cash_flow': operating_cash_flow,
                'investing_cash_flow': investing_cash_flow,
                'financing_cash_flow': financing_cash_flow,
                'net_cash_increase': net_cash_increase
            }
            
        except Exception as e:
            print(f"生成现金流量表失败: {str(e)}")
            return {
                'start_date': start_date,
                'end_date': end_date,
                'operating_cash_flow': 0,
                'investing_cash_flow': 0,
                'financing_cash_flow': 0,
                'net_cash_increase': 0
            }
    
    @staticmethod
    def generate_trend_analysis(months=12):
        """
        生成趋势分析数据
        
        Args:
            months: 分析的月数
            
        Returns:
            list: 月度趋势数据
        """
        try:
            trend_data = []
            current_date = datetime.datetime.now()
            
            for i in range(months - 1, -1, -1):
                # 计算月份
                target_date = current_date - datetime.timedelta(days=i*30)
                year, month = target_date.year, target_date.month
                
                # 获取月度汇总
                month_summary = ReportModel.get_month_summary(year, month)
                
                # 格式化月份标签
                month_label = f"{year}-{month:02d}"
                
                trend_data.append({
                    'month': month_label,
                    'income': month_summary['total_income'],
                    'expense': month_summary['total_expense'],
                    'profit': month_summary['profit'],
                    'transaction_count': month_summary['transaction_count']
                })
            
            return trend_data
            
        except Exception as e:
            print(f"生成趋势分析失败: {str(e)}")
            return []
    
    @staticmethod
    def get_month_summary(year, month):
        """
        获取指定月份的汇总数据
        
        Args:
            year: 年份
            month: 月份
            
        Returns:
            dict: 月度汇总数据
        """
        try:
            # 构建日期范围
            start_date = f"{year}-{month:02d}-01"
            
            # 计算月末日期
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
            
            end_date = f"{next_year}-{next_month:02d}-01"
            
            # 查询收入总额
            income_query = """
            SELECT SUM(amount) as total 
            FROM transactions 
            WHERE transaction_type = 'income' 
            AND transaction_date >= ? 
            AND transaction_date < ?
            """
            income_result = execute_query(income_query, (start_date, end_date), fetch=True)
            total_income = income_result['total'] if income_result and income_result['total'] else 0
            
            # 查询支出总额
            expense_query = """
            SELECT SUM(amount) as total 
            FROM transactions 
            WHERE transaction_type = 'expense' 
            AND transaction_date >= ? 
            AND transaction_date < ?
            """
            expense_result = execute_query(expense_query, (start_date, end_date), fetch=True)
            total_expense = expense_result['total'] if expense_result and expense_result['total'] else 0
            
            # 计算利润
            profit = total_income + total_expense  # expense是负数
            
            # 交易笔数
            transaction_count = execute_query(
                "SELECT COUNT(*) as count FROM transactions WHERE transaction_date >= ? AND transaction_date < ?",
                (start_date, end_date),
                fetch=True
            )['count']
            
            return {
                'year': year,
                'month': month,
                'total_income': total_income,
                'total_expense': abs(total_expense),  # 返回正数
                'profit': profit,
                'transaction_count': transaction_count
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
    def generate_account_summary(start_date=None, end_date=None):
        """
        生成账户汇总报表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 账户汇总数据
        """
        try:
            # 构建查询语句
            query = """
            SELECT a.id, a.name, a.account_type, a.balance,
            (SELECT COALESCE(SUM(amount), 0) FROM transactions 
             WHERE account_id = a.id AND transaction_type = 'income'
             """
            
            if start_date:
                query += f" AND transaction_date >= '{start_date}'"
            if end_date:
                query += f" AND transaction_date <= '{end_date}'"
            
            query += " ) as total_income, (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE account_id = a.id AND transaction_type = 'expense' """
            
            if start_date:
                query += f" AND transaction_date >= '{start_date}'"
            if end_date:
                query += f" AND transaction_date <= '{end_date}'"
            
            query += " ) as total_expense, (SELECT COUNT(*) FROM transactions WHERE account_id = a.id"
            
            if start_date:
                query += f" AND transaction_date >= '{start_date}'"
            if end_date:
                query += f" AND transaction_date <= '{end_date}'"
            
            query += " ) as transaction_count FROM accounts a WHERE a.status = 'active' ORDER BY a.account_type, a.name"
            
            # 执行查询
            results = execute_query(query, fetch_all=True)
            
            # 按账户类型分组
            summary_by_type = {}
            for account in results:
                account_type = account['account_type']
                if account_type not in summary_by_type:
                    summary_by_type[account_type] = {
                        'accounts': [],
                        'total_balance': 0,
                        'total_income': 0,
                        'total_expense': 0,
                        'transaction_count': 0
                    }
                
                # 将支出转为正数
                account['total_expense'] = abs(account['total_expense'])
                
                summary_by_type[account_type]['accounts'].append(account)
                summary_by_type[account_type]['total_balance'] += account['balance']
                summary_by_type[account_type]['total_income'] += account['total_income']
                summary_by_type[account_type]['total_expense'] += account['total_expense']
                summary_by_type[account_type]['transaction_count'] += account['transaction_count']
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'accounts': results,
                'summary_by_type': summary_by_type,
                'total_accounts': len(results)
            }
            
        except Exception as e:
            print(f"生成账户汇总报表失败: {str(e)}")
            return {
                'start_date': start_date,
                'end_date': end_date,
                'accounts': [],
                'summary_by_type': {},
                'total_accounts': 0
            }