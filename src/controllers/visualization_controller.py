#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据可视化控制器模块
负责处理图表生成、数据处理和可视化逻辑
"""

import logging
import os
from datetime import datetime, timedelta
import random

# 导入必要的可视化库
try:
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式后端
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    import pandas as pd
    VISUALIZATION_READY = True
except ImportError as e:
    logging.error(f"导入可视化库失败: {str(e)}")
    VISUALIZATION_READY = False

# 导入模型
try:
    from src.models.transaction import TransactionModel
    from src.models.report import report_model
    from src.models.category import category_model
    from src.models.account import account_model
    MODELS_READY = True
except ImportError as e:
    logging.error(f"导入模型失败: {str(e)}")
    MODELS_READY = False

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs', 'visualization.log')),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("VisualizationController")


class VisualizationController:
    """
    数据可视化控制器
    负责生成各类图表和数据可视化内容
    """
    
    def __init__(self):
        """
        初始化数据可视化控制器
        """
        self.transaction_model = TransactionModel if MODELS_READY else None
        self.report_model = report_model if MODELS_READY else None
        self.category_model = category_model if MODELS_READY else None
        self.account_model = account_model if MODELS_READY else None
        
        # 设置中文字体支持
        if VISUALIZATION_READY:
            self._setup_chinese_fonts()
    
    def _setup_chinese_fonts(self):
        """
        设置中文字体支持
        """
        try:
            # 尝试不同的中文字体
            fonts = ['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC', 'Arial Unicode MS']
            for font in fonts:
                try:
                    plt.rcParams['font.sans-serif'] = [font]
                    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                    # 测试字体是否可用
                    plt.figure(figsize=(1, 1))
                    plt.text(0.5, 0.5, '测试中文字体')
                    plt.close()
                    logger.info(f"成功设置字体: {font}")
                    break
                except:
                    continue
        except Exception as e:
            logger.warning(f"设置中文字体失败: {str(e)}")
    
    def generate_income_expense_chart(self, start_date, end_date):
        """
        生成收支对比图表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 包含图表数据和设置的字典
        """
        try:
            if not VISUALIZATION_READY:
                return {"success": False, "error": "可视化库未就绪"}
            
            # 获取时间范围内的交易数据
            if MODELS_READY and self.transaction_model:
                transactions = self.transaction_model.get_transactions_by_date_range(start_date, end_date)
            else:
                # 生成模拟数据
                transactions = self._generate_mock_transactions(start_date, end_date)
            
            # 转换为DataFrame进行处理
            df = pd.DataFrame(transactions)
            
            # 按日期和类型分组
            if not df.empty:
                # 确保日期格式正确
                df['date'] = pd.to_datetime(df['date'])
                
                # 按天和类型分组
                daily_summary = df.groupby([df['date'].dt.date, 'type'])['amount'].sum().unstack(fill_value=0)
                
                # 准备图表数据
                dates = daily_summary.index
                income = daily_summary.get('income', [0]*len(dates))
                expense = daily_summary.get('expense', [0]*len(dates))
                
                # 计算累计值
                cumulative_income = income.cumsum()
                cumulative_expense = expense.cumsum()
            else:
                # 如果没有数据，使用模拟数据
                dates = pd.date_range(start=start_date, end=end_date)
                income = [random.randint(10000, 50000) for _ in range(len(dates))]
                expense = [random.randint(5000, 30000) for _ in range(len(dates))]
                cumulative_income = np.cumsum(income)
                cumulative_expense = np.cumsum(expense)
            
            # 创建图表
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # 设置图表标题和坐标轴
            ax1.set_title('收支对比图表', fontsize=16)
            ax1.set_xlabel('日期', fontsize=12)
            ax1.set_ylabel('金额 (元)', fontsize=12)
            
            # 绘制柱状图
            bar_width = 0.35
            x = np.arange(len(dates))
            ax1.bar(x - bar_width/2, income, width=bar_width, label='收入', color='#28a745')
            ax1.bar(x + bar_width/2, expense, width=bar_width, label='支出', color='#dc3545')
            
            # 创建第二个Y轴用于累计值
            ax2 = ax1.twinx()
            ax2.set_ylabel('累计金额 (元)', fontsize=12)
            ax2.plot(x, cumulative_income, label='累计收入', color='#20c997', marker='o', linewidth=2)
            ax2.plot(x, cumulative_expense, label='累计支出', color='#fd7e14', marker='s', linewidth=2)
            
            # 设置X轴标签
            ax1.set_xticks(x)
            ax1.set_xticklabels([date.strftime('%Y-%m-%d') for date in dates], rotation=45)
            
            # 添加图例
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            
            # 设置网格线
            ax1.grid(True, linestyle='--', alpha=0.7)
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图表为字节流
            from io import BytesIO
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            
            # 清理图表
            plt.close(fig)
            
            return {
                "success": True,
                "chart_data": buffer.getvalue(),
                "summary": {
                    "total_income": sum(income),
                    "total_expense": sum(expense),
                    "net_amount": sum(income) - sum(expense)
                }
            }
            
        except Exception as e:
            logger.error(f"生成收支对比图表失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def generate_category_pie_chart(self, start_date, end_date, transaction_type='expense'):
        """
        生成分类饼图
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            transaction_type: 交易类型 ('income' 或 'expense')
            
        Returns:
            dict: 包含图表数据和设置的字典
        """
        try:
            if not VISUALIZATION_READY:
                return {"success": False, "error": "可视化库未就绪"}
            
            # 获取分类统计数据
            if MODELS_READY and self.transaction_model and self.category_model:
                # 获取交易数据
                transactions = self.transaction_model.get_transactions_by_date_range(start_date, end_date, transaction_type)
                
                # 按分类分组
                category_summary = {}
                for t in transactions:
                    category_id = t.get('category_id')
                    if category_id:
                        # 获取分类名称
                        category = self.category_model.get_category_by_id(category_id)
                        if category:
                            category_name = category.get('name', '未分类')
                            if category_name in category_summary:
                                category_summary[category_name] += t.get('amount', 0)
                            else:
                                category_summary[category_name] = t.get('amount', 0)
            else:
                # 生成模拟数据
                if transaction_type == 'income':
                    category_summary = {
                        '主营业务收入': 150000,
                        '投资收益': 25000,
                        '其他收入': 10000,
                        '营业外收入': 5000
                    }
                else:
                    category_summary = {
                        '办公费用': 12000,
                        '工资薪酬': 80000,
                        '采购成本': 45000,
                        '水电费': 3500,
                        '差旅费': 8000,
                        '税费': 15000,
                        '其他费用': 4500
                    }
            
            # 准备饼图数据
            labels = list(category_summary.keys())
            sizes = list(category_summary.values())
            
            # 设置颜色
            colors = plt.cm.Pastel1(np.linspace(0, 1, len(labels)))
            
            # 创建饼图
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # 计算百分比
            wedges, texts, autotexts = ax.pie(sizes, labels=None, autopct='%1.1f%%',
                                             shadow=False, startangle=90, colors=colors)
            
            # 设置文本样式
            for text in texts:
                text.set_fontsize(12)
            for autotext in autotexts:
                autotext.set_fontsize(10)
                autotext.set_color('black')
            
            # 添加标题
            title = f'{"收入" if transaction_type == "income" else "支出"}分类占比'
            ax.set_title(title, fontsize=16)
            
            # 添加图例
            ax.legend(wedges, labels, title="分类", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            
            # 确保饼图是圆的
            ax.axis('equal')
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图表为字节流
            from io import BytesIO
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            
            # 清理图表
            plt.close(fig)
            
            return {
                "success": True,
                "chart_data": buffer.getvalue(),
                "category_summary": category_summary
            }
            
        except Exception as e:
            logger.error(f"生成分类饼图失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def generate_trend_chart(self, start_date, end_date, interval='month'):
        """
        生成收支趋势图表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔 ('day', 'week', 'month')
            
        Returns:
            dict: 包含图表数据和设置的字典
        """
        try:
            if not VISUALIZATION_READY:
                return {"success": False, "error": "可视化库未就绪"}
            
            # 获取交易数据
            if MODELS_READY and self.transaction_model:
                transactions = self.transaction_model.get_transactions_by_date_range(start_date, end_date)
            else:
                # 生成模拟数据
                transactions = self._generate_mock_transactions(start_date, end_date)
            
            # 转换为DataFrame进行处理
            df = pd.DataFrame(transactions)
            
            # 按时间间隔分组
            if not df.empty:
                # 确保日期格式正确
                df['date'] = pd.to_datetime(df['date'])
                
                # 设置时间间隔
                if interval == 'day':
                    grouper = df['date'].dt.date
                elif interval == 'week':
                    grouper = df['date'].dt.to_period('W').dt.to_timestamp()
                else:  # month
                    grouper = df['date'].dt.to_period('M').dt.to_timestamp()
                
                # 按时间间隔和类型分组
                time_summary = df.groupby([grouper, 'type'])['amount'].sum().unstack(fill_value=0)
                
                # 准备趋势图数据
                time_points = time_summary.index
                income = time_summary.get('income', [0]*len(time_points))
                expense = time_summary.get('expense', [0]*len(time_points))
                profit = income - expense
            else:
                # 如果没有数据，使用模拟数据
                if interval == 'month':
                    time_points = pd.date_range(start=start_date, end=end_date, freq='MS')
                elif interval == 'week':
                    time_points = pd.date_range(start=start_date, end=end_date, freq='W-MON')
                else:  # day
                    time_points = pd.date_range(start=start_date, end=end_date)
                
                income = [random.randint(30000, 80000) for _ in range(len(time_points))]
                expense = [random.randint(20000, 50000) for _ in range(len(time_points))]
                profit = [i - e for i, e in zip(income, expense)]
            
            # 创建图表
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 设置图表标题和坐标轴
            interval_text = {'day': '日', 'week': '周', 'month': '月'}
            ax.set_title(f'收支{interval_text.get(interval, "月")}趋势图', fontsize=16)
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('金额 (元)', fontsize=12)
            
            # 绘制折线图
            ax.plot(time_points, income, label='收入', color='#28a745', marker='o', linewidth=2)
            ax.plot(time_points, expense, label='支出', color='#dc3545', marker='s', linewidth=2)
            ax.plot(time_points, profit, label='利润', color='#17a2b8', marker='^', linewidth=2)
            
            # 填充利润区域
            ax.fill_between(time_points, profit, 0, where=(profit >= 0), color='#17a2b8', alpha=0.3)
            ax.fill_between(time_points, profit, 0, where=(profit < 0), color='#dc3545', alpha=0.3)
            
            # 设置X轴格式化
            if interval == 'month':
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            elif interval == 'week':
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            else:  # day
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            
            # 设置日期标签旋转
            plt.xticks(rotation=45)
            
            # 添加图例
            ax.legend(loc='upper left')
            
            # 添加网格线
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图表为字节流
            from io import BytesIO
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            
            # 清理图表
            plt.close(fig)
            
            return {
                "success": True,
                "chart_data": buffer.getvalue(),
                "trend_summary": {
                    "periods": list(time_points),
                    "income": list(income),
                    "expense": list(expense),
                    "profit": list(profit)
                }
            }
            
        except Exception as e:
            logger.error(f"生成趋势图表失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def generate_account_balance_chart(self):
        """
        生成账户余额图表
        
        Returns:
            dict: 包含图表数据和设置的字典
        """
        try:
            if not VISUALIZATION_READY:
                return {"success": False, "error": "可视化库未就绪"}
            
            # 获取账户余额数据
            if MODELS_READY and self.account_model:
                accounts = self.account_model.get_all_accounts()
                account_data = [(acc['name'], acc['balance']) for acc in accounts]
            else:
                # 生成模拟数据
                account_data = [
                    ('现金账户', 50000),
                    ('银行存款-工行', 250000),
                    ('银行存款-建行', 180000),
                    ('应收账款', 120000),
                    ('库存现金', 5000)
                ]
            
            # 准备柱状图数据
            accounts = [item[0] for item in account_data]
            balances = [item[1] for item in account_data]
            
            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 设置图表标题和坐标轴
            ax.set_title('账户余额分布', fontsize=16)
            ax.set_xlabel('账户', fontsize=12)
            ax.set_ylabel('余额 (元)', fontsize=12)
            
            # 绘制水平柱状图
            bars = ax.barh(accounts, balances, color=plt.cm.Blues(np.linspace(0.3, 0.8, len(accounts))))
            
            # 在柱状图上显示金额
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 5000, bar.get_y() + bar.get_height()/2, f'{width:,.2f}',
                        ha='left', va='center', fontsize=10)
            
            # 添加网格线
            ax.grid(True, axis='x', linestyle='--', alpha=0.7)
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图表为字节流
            from io import BytesIO
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            
            # 清理图表
            plt.close(fig)
            
            return {
                "success": True,
                "chart_data": buffer.getvalue(),
                "total_balance": sum(balances),
                "account_count": len(accounts)
            }
            
        except Exception as e:
            logger.error(f"生成账户余额图表失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def generate_profit_analysis_chart(self, start_date, end_date):
        """
        生成利润分析图表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 包含图表数据和设置的字典
        """
        try:
            if not VISUALIZATION_READY:
                return {"success": False, "error": "可视化库未就绪"}
            
            # 获取利润数据
            if MODELS_READY and self.report_model:
                profit_data = self.report_model.calculate_profit(start_date, end_date)
            else:
                # 生成模拟数据
                profit_data = {
                    'total_income': 500000,
                    'total_expense': 350000,
                    'profit': 150000,
                    'expense_breakdown': {
                        '营业成本': 200000,
                        '销售费用': 50000,
                        '管理费用': 40000,
                        '财务费用': 10000,
                        '税费': 30000,
                        '其他费用': 20000
                    }
                }
            
            # 准备图表数据
            labels = ['利润', '总支出']
            sizes = [profit_data['profit'], profit_data['total_expense']]
            
            # 创建图表
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # 第一个图表：利润构成饼图
            colors = ['#28a745', '#dc3545']
            ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
                   shadow=False, startangle=90, colors=colors)
            ax1.set_title('利润构成分析', fontsize=14)
            ax1.axis('equal')
            
            # 第二个图表：支出明细条形图
            expense_items = list(profit_data['expense_breakdown'].keys())
            expense_amounts = list(profit_data['expense_breakdown'].values())
            
            # 按金额降序排列
            sorted_data = sorted(zip(expense_items, expense_amounts), key=lambda x: x[1], reverse=True)
            expense_items, expense_amounts = zip(*sorted_data)
            
            bars = ax2.bar(expense_items, expense_amounts, color=plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(expense_items))))
            ax2.set_title('支出明细分析', fontsize=14)
            ax2.set_xlabel('费用项目', fontsize=12)
            ax2.set_ylabel('金额 (元)', fontsize=12)
            
            # 在柱状图上显示金额
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2, height + 5000, f'{height:,.2f}',
                        ha='center', va='bottom', fontsize=9)
            
            # 旋转X轴标签
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # 添加网格线
            ax2.grid(True, axis='y', linestyle='--', alpha=0.7)
            
            # 添加总体信息文本框
            total_info = f"总收入: {profit_data['total_income']:,.2f}元\n"
            total_info += f"总支出: {profit_data['total_expense']:,.2f}元\n"
            total_info += f"净利润: {profit_data['profit']:,.2f}元\n"
            total_info += f"利润率: {profit_data['profit']/profit_data['total_income']*100:.1f}%"
            
            fig.text(0.5, 0.01, total_info, ha='center', va='bottom', fontsize=12,
                     bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', alpha=0.8))
            
            # 调整布局
            plt.tight_layout(rect=[0, 0.05, 1, 0.95])
            
            # 保存图表为字节流
            from io import BytesIO
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            
            # 清理图表
            plt.close(fig)
            
            return {
                "success": True,
                "chart_data": buffer.getvalue(),
                "profit_summary": profit_data
            }
            
        except Exception as e:
            logger.error(f"生成利润分析图表失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _generate_mock_transactions(self, start_date, end_date):
        """
        生成模拟交易数据（用于测试）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            list: 交易数据列表
        """
        transactions = []
        current_date = start_date
        
        # 模拟收入分类
        income_categories = ['主营业务收入', '投资收益', '其他收入']
        # 模拟支出分类
        expense_categories = ['办公费用', '工资薪酬', '采购成本', '水电费', '差旅费', '税费']
        
        while current_date <= end_date:
            # 生成收入交易
            if random.random() > 0.3:  # 70%概率有收入
                transactions.append({
                    'id': len(transactions) + 1,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'type': 'income',
                    'amount': random.randint(20000, 80000),
                    'category_id': random.randint(1, 3),
                    'category_name': random.choice(income_categories),
                    'account_id': 1,
                    'account_name': '银行存款-工行',
                    'description': f'收到{random.choice(income_categories)}'
                })
            
            # 生成支出交易
            for _ in range(random.randint(1, 3)):
                transactions.append({
                    'id': len(transactions) + 1,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'type': 'expense',
                    'amount': random.randint(1000, 30000),
                    'category_id': random.randint(4, 9),
                    'category_name': random.choice(expense_categories),
                    'account_id': 1,
                    'account_name': '银行存款-工行',
                    'description': f'支付{random.choice(expense_categories)}'
                })
            
            # 前进到下一天
            current_date += timedelta(days=1)
        
        return transactions
    
    def generate_dashboard_summary(self, start_date, end_date):
        """
        生成仪表盘摘要数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 仪表盘摘要数据
        """
        try:
            # 获取各项图表数据
            income_expense_data = self.generate_income_expense_chart(start_date, end_date)
            category_pie_data = self.generate_category_pie_chart(start_date, end_date, 'expense')
            trend_data = self.generate_trend_chart(start_date, end_date, 'month')
            account_balance_data = self.generate_account_balance_chart()
            profit_data = self.generate_profit_analysis_chart(start_date, end_date)
            
            # 汇总数据
            summary = {
                "period": {
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d')
                },
                "income_expense": {
                    "total_income": income_expense_data.get("summary", {}).get("total_income", 0),
                    "total_expense": income_expense_data.get("summary", {}).get("total_expense", 0),
                    "net_amount": income_expense_data.get("summary", {}).get("net_amount", 0)
                },
                "top_expense_categories": sorted(
                    category_pie_data.get("category_summary", {}).items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "total_account_balance": account_balance_data.get("total_balance", 0),
                "profit_margin": profit_data.get("profit_summary", {}).get("profit", 0) / \
                               (profit_data.get("profit_summary", {}).get("total_income", 1) * 100),
                "charts": {
                    "income_expense": income_expense_data.get("chart_data"),
                    "category_pie": category_pie_data.get("chart_data"),
                    "trend": trend_data.get("chart_data"),
                    "account_balance": account_balance_data.get("chart_data"),
                    "profit_analysis": profit_data.get("chart_data")
                }
            }
            
            return {
                "success": True,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"生成仪表盘摘要失败: {str(e)}")
            return {"success": False, "error": str(e)}


# 创建全局可视化控制器实例
visualization_controller = VisualizationController()


if __name__ == "__main__":
    # 测试可视化控制器功能
    print("数据可视化控制器测试")
    
    # 测试生成图表
    if VISUALIZATION_READY:
        controller = VisualizationController()
        
        # 设置日期范围（最近30天）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # 生成收支对比图表
        result = controller.generate_income_expense_chart(start_date, end_date)
        if result["success"]:
            print("收支对比图表生成成功")
        else:
            print(f"生成失败: {result.get('error')}")
        
        # 生成分类饼图
        result = controller.generate_category_pie_chart(start_date, end_date, 'expense')
        if result["success"]:
            print("分类饼图生成成功")
        else:
            print(f"生成失败: {result.get('error')}")
    else:
        print("可视化库未就绪，跳过测试")