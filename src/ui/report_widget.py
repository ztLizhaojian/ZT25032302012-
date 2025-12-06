#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报表分析组件
实现利润核算、财务报表生成和数据可视化功能
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QComboBox, QDateEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, 
    QTableView, QHeaderView, QGroupBox, QMessageBox,
    QSplitter, QScrollArea
)
from PyQt5.QtGui import QFont, QColor, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QDate, QSortFilterProxyModel

import sys
import os
import matplotlib
matplotlib.use('Qt5Agg')  # 使用Qt5后端
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入数据库操作
from src.database.db_manager import execute_query


class ReportWidget(QWidget):
    """报表分析组件类"""
    
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.init_ui()
        self.update_reports()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 创建时间选择区域
        date_selection_group = QGroupBox("时间范围选择")
        date_layout = QHBoxLayout(date_selection_group)
        date_layout.setSpacing(15)
        
        # 快捷时间选择
        date_layout.addWidget(QLabel("快捷选择:"))
        self.quick_date_combo = QComboBox()
        self.quick_date_combo.addItems([
            "本月", "上月", "本季度", "上季度", 
            "本年", "上年", "近6个月", "近12个月"
        ])
        self.quick_date_combo.currentTextChanged.connect(self.on_quick_date_changed)
        date_layout.addWidget(self.quick_date_combo)
        
        # 自定义时间范围
        date_layout.addWidget(QLabel("开始日期:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        # 默认选择本月初
        current_date = QDate.currentDate()
        self.start_date_edit.setDate(QDate(current_date.year(), current_date.month(), 1))
        date_layout.addWidget(self.start_date_edit)
        
        date_layout.addWidget(QLabel("结束日期:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(current_date)
        date_layout.addWidget(self.end_date_edit)
        
        # 更新按钮
        self.update_button = QPushButton("更新报表")
        self.update_button.setFixedHeight(36)
        self.update_button.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
        """)
        self.update_button.clicked.connect(self.update_reports)
        date_layout.addWidget(self.update_button)
        
        # 添加时间选择区域到主布局
        main_layout.addWidget(date_selection_group)
        
        # 创建标签页部件
        self.tab_widget = QTabWidget()
        
        # 创建各个报表标签页
        self.create_summary_tab()       # 收支汇总
        self.create_profit_tab()        # 利润分析
        self.create_category_tab()      # 分类统计
        self.create_account_tab()       # 账户余额
        self.create_trend_tab()         # 趋势分析
        
        # 添加标签页
        self.tab_widget.addTab(self.summary_widget, "收支汇总")
        self.tab_widget.addTab(self.profit_widget, "利润分析")
        self.tab_widget.addTab(self.category_widget, "分类统计")
        self.tab_widget.addTab(self.account_widget, "账户余额")
        self.tab_widget.addTab(self.trend_widget, "趋势分析")
        
        # 添加标签页到主布局
        main_layout.addWidget(self.tab_widget)
    
    def on_quick_date_changed(self, text):
        """快捷时间选择变化时的处理"""
        current_date = QDate.currentDate()
        
        if text == "本月":
            start_date = QDate(current_date.year(), current_date.month(), 1)
            end_date = current_date
        elif text == "上月":
            if current_date.month() == 1:
                start_date = QDate(current_date.year() - 1, 12, 1)
                end_date = QDate(current_date.year() - 1, 12, 31)
            else:
                start_date = QDate(current_date.year(), current_date.month() - 1, 1)
                end_date = QDate(current_date.year(), current_date.month(), 0)
        elif text == "本季度":
            quarter = (current_date.month() - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start_date = QDate(current_date.year(), start_month, 1)
            
            if quarter == 4:
                end_date = QDate(current_date.year(), 12, 31)
            else:
                end_date = QDate(current_date.year(), start_month + 3, 0)
        elif text == "上季度":
            quarter = (current_date.month() - 1) // 3 + 1
            if quarter == 1:
                start_month = 10
                start_date = QDate(current_date.year() - 1, start_month, 1)
                end_date = QDate(current_date.year() - 1, 12, 31)
            else:
                start_month = (quarter - 2) * 3 + 1
                start_date = QDate(current_date.year(), start_month, 1)
                end_date = QDate(current_date.year(), start_month + 3, 0)
        elif text == "本年":
            start_date = QDate(current_date.year(), 1, 1)
            end_date = current_date
        elif text == "上年":
            start_date = QDate(current_date.year() - 1, 1, 1)
            end_date = QDate(current_date.year() - 1, 12, 31)
        elif text == "近6个月":
            start_date = current_date.addMonths(-5)
            start_date = QDate(start_date.year(), start_date.month(), 1)
            end_date = current_date
        elif text == "近12个月":
            start_date = current_date.addMonths(-11)
            start_date = QDate(start_date.year(), start_date.month(), 1)
            end_date = current_date
        
        # 更新日期选择器
        self.start_date_edit.setDate(start_date)
        self.end_date_edit.setDate(end_date)
    
    def create_summary_tab(self):
        """创建收支汇总标签页"""
        self.summary_widget = QWidget()
        summary_layout = QVBoxLayout(self.summary_widget)
        
        # 创建统计卡片布局
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        # 总收入卡片
        self.total_income_group = QGroupBox("总收入")
        income_layout = QVBoxLayout(self.total_income_group)
        self.total_income_label = QLabel("¥0.00")
        self.total_income_label.setFont(QFont("SimHei", 24, QFont.Bold))
        self.total_income_label.setAlignment(Qt.AlignCenter)
        self.total_income_label.setStyleSheet("color: #28a745")
        income_layout.addWidget(self.total_income_label)
        
        # 总支出卡片
        self.total_expense_group = QGroupBox("总支出")
        expense_layout = QVBoxLayout(self.total_expense_group)
        self.total_expense_label = QLabel("¥0.00")
        self.total_expense_label.setFont(QFont("SimHei", 24, QFont.Bold))
        self.total_expense_label.setAlignment(Qt.AlignCenter)
        self.total_expense_label.setStyleSheet("color: #dc3545")
        expense_layout.addWidget(self.total_expense_label)
        
        # 净利润卡片
        self.net_profit_group = QGroupBox("净利润")
        profit_layout = QVBoxLayout(self.net_profit_group)
        self.net_profit_label = QLabel("¥0.00")
        self.net_profit_label.setFont(QFont("SimHei", 24, QFont.Bold))
        self.net_profit_label.setAlignment(Qt.AlignCenter)
        profit_layout.addWidget(self.net_profit_label)
        
        # 收支比卡片
        self.ratio_group = QGroupBox("收支比")
        ratio_layout = QVBoxLayout(self.ratio_group)
        self.ratio_label = QLabel("0%")
        self.ratio_label.setFont(QFont("SimHei", 24, QFont.Bold))
        self.ratio_label.setAlignment(Qt.AlignCenter)
        ratio_layout.addWidget(self.ratio_label)
        
        # 添加卡片到布局
        stats_layout.addWidget(self.total_income_group, 1)
        stats_layout.addWidget(self.total_expense_group, 1)
        stats_layout.addWidget(self.net_profit_group, 1)
        stats_layout.addWidget(self.ratio_group, 1)
        
        # 创建图表
        self.summary_figure = Figure(figsize=(8, 4), dpi=100)
        self.summary_canvas = FigureCanvas(self.summary_figure)
        self.summary_toolbar = NavigationToolbar(self.summary_canvas, self.summary_widget)
        
        # 添加到布局
        summary_layout.addLayout(stats_layout)
        summary_layout.addWidget(self.summary_toolbar)
        summary_layout.addWidget(self.summary_canvas)
    
    def create_profit_tab(self):
        """创建利润分析标签页"""
        self.profit_widget = QWidget()
        profit_layout = QVBoxLayout(self.profit_widget)
        
        # 创建图表
        self.profit_figure = Figure(figsize=(10, 6), dpi=100)
        self.profit_canvas = FigureCanvas(self.profit_figure)
        self.profit_toolbar = NavigationToolbar(self.profit_canvas, self.profit_widget)
        
        # 添加到布局
        profit_layout.addWidget(self.profit_toolbar)
        profit_layout.addWidget(self.profit_canvas)
    
    def create_category_tab(self):
        """创建分类统计标签页"""
        self.category_widget = QWidget()
        category_layout = QVBoxLayout(self.category_widget)
        
        # 创建分类选择
        category_select_layout = QHBoxLayout()
        category_select_layout.addWidget(QLabel("统计类型:"))
        self.category_type_combo = QComboBox()
        self.category_type_combo.addItems(["收入分类", "支出分类"])
        self.category_type_combo.currentTextChanged.connect(self.update_reports)
        category_select_layout.addWidget(self.category_type_combo)
        category_select_layout.addStretch(1)
        
        # 创建拆分器
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建饼图区域
        pie_widget = QWidget()
        pie_layout = QVBoxLayout(pie_widget)
        self.category_pie_figure = Figure(figsize=(6, 6), dpi=100)
        self.category_pie_canvas = FigureCanvas(self.category_pie_figure)
        self.category_pie_toolbar = NavigationToolbar(self.category_pie_canvas, pie_widget)
        pie_layout.addWidget(self.category_pie_toolbar)
        pie_layout.addWidget(self.category_pie_canvas)
        
        # 创建柱状图区域
        bar_widget = QWidget()
        bar_layout = QVBoxLayout(bar_widget)
        self.category_bar_figure = Figure(figsize=(6, 6), dpi=100)
        self.category_bar_canvas = FigureCanvas(self.category_bar_figure)
        self.category_bar_toolbar = NavigationToolbar(self.category_bar_canvas, bar_widget)
        bar_layout.addWidget(self.category_bar_toolbar)
        bar_layout.addWidget(self.category_bar_canvas)
        
        # 添加到拆分器
        splitter.addWidget(pie_widget)
        splitter.addWidget(bar_widget)
        
        # 添加到布局
        category_layout.addLayout(category_select_layout)
        category_layout.addWidget(splitter)
    
    def create_account_tab(self):
        """创建账户余额标签页"""
        self.account_widget = QWidget()
        account_layout = QVBoxLayout(self.account_widget)
        
        # 创建表格视图
        self.account_table = QTableView()
        self.account_table.setAlternatingRowColors(True)
        self.account_table.setSortingEnabled(True)
        self.account_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.account_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 5px;
                font-family: SimHei;
                font-weight: bold;
            }
        """)
        
        # 创建表格模型
        self.account_model = QStandardItemModel(0, 4)
        self.account_model.setHorizontalHeaderLabels(["账户名称", "期初余额", "当前余额", "变动金额"])
        self.account_table.setModel(self.account_model)
        
        # 创建图表
        self.account_figure = Figure(figsize=(8, 4), dpi=100)
        self.account_canvas = FigureCanvas(self.account_figure)
        self.account_toolbar = NavigationToolbar(self.account_canvas, self.account_widget)
        
        # 添加到布局
        account_layout.addWidget(self.account_table)
        account_layout.addWidget(self.account_toolbar)
        account_layout.addWidget(self.account_canvas)
    
    def create_trend_tab(self):
        """创建趋势分析标签页"""
        self.trend_widget = QWidget()
        trend_layout = QVBoxLayout(self.trend_widget)
        
        # 创建时间粒度选择
        time_select_layout = QHBoxLayout()
        time_select_layout.addWidget(QLabel("时间粒度:"))
        self.time_granularity_combo = QComboBox()
        self.time_granularity_combo.addItems(["按日", "按月", "按季度"])
        self.time_granularity_combo.currentTextChanged.connect(self.update_reports)
        time_select_layout.addWidget(self.time_granularity_combo)
        time_select_layout.addStretch(1)
        
        # 创建图表
        self.trend_figure = Figure(figsize=(10, 6), dpi=100)
        self.trend_canvas = FigureCanvas(self.trend_figure)
        self.trend_toolbar = NavigationToolbar(self.trend_canvas, self.trend_widget)
        
        # 添加到布局
        trend_layout.addLayout(time_select_layout)
        trend_layout.addWidget(self.trend_toolbar)
        trend_layout.addWidget(self.trend_canvas)
    
    def update_reports(self):
        """更新所有报表"""
        try:
            # 获取时间范围
            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
            
            # 详细记录每个报表的更新情况
            print("开始更新报表...")
            
            # 更新收支汇总
            print("正在更新收支汇总...")
            self.update_summary_report(start_date, end_date)
            print("收支汇总更新完成")
            
            # 更新利润分析
            print("正在更新利润分析...")
            self.update_profit_report(start_date, end_date)
            print("利润分析更新完成")
            
            # 更新分类统计
            print("正在更新分类统计...")
            self.update_category_report(start_date, end_date)
            print("分类统计更新完成")
            
            # 更新账户余额
            print("正在更新账户余额...")
            self.update_account_report(start_date, end_date)
            print("账户余额更新完成")
            
            # 更新趋势分析
            print("正在更新趋势分析...")
            self.update_trend_report(start_date, end_date)
            print("趋势分析更新完成")
            
            print("所有报表更新完成")
            
        except Exception as e:
            import traceback
            print("更新报表失败:", str(e))
            print("错误堆栈:", traceback.format_exc())
            QMessageBox.critical(self, "错误", f"更新报表失败: {str(e)}")
    
    def update_summary_report(self, start_date, end_date):
        """更新收支汇总报表"""
        # 查询总收入
        income_result = execute_query(
            """
            SELECT SUM(amount) as total_income 
            FROM transactions 
            WHERE transaction_type = 'income' AND transaction_date BETWEEN ? AND ?
            """,
            (start_date, end_date),
            fetch_all=False
        )
        total_income = income_result['total_income'] or 0 if income_result else 0
        
        # 查询总支出
        expense_result = execute_query(
            """
            SELECT SUM(amount) as total_expense 
            FROM transactions 
            WHERE transaction_type = 'expense' AND transaction_date BETWEEN ? AND ?
            """,
            (start_date, end_date),
            fetch_all=False
        )
        total_expense = expense_result['total_expense'] or 0 if expense_result else 0
    
        # 计算净利润
        net_profit = total_income - total_expense
        
        # 计算收支比
        if total_income > 0:
            ratio = (total_expense / total_income) * 100
        else:
            ratio = 0
        
        # 更新标签
        self.total_income_label.setText(f"¥{total_income:.2f}")
        self.total_expense_label.setText(f"¥{total_expense:.2f}")
        self.net_profit_label.setText(f"¥{net_profit:.2f}")
        # 根据利润正负设置颜色
        if net_profit >= 0:
            self.net_profit_label.setStyleSheet("color: #28a745")
        else:
            self.net_profit_label.setStyleSheet("color: #dc3545")
        
        self.ratio_label.setText(f"{ratio:.2f}%")
        # 根据收支比设置颜色
        if ratio <= 50:
            self.ratio_label.setStyleSheet("color: #28a745")  # 支出占比低
        elif ratio <= 80:
            self.ratio_label.setStyleSheet("color: #ffc107")  # 支出占比中等
        else:
            self.ratio_label.setStyleSheet("color: #dc3545")  # 支出占比高
        
        # 更新图表
        self.summary_figure.clear()
        ax = self.summary_figure.add_subplot(111)
        
        # 创建收支对比柱状图
        labels = ['收入', '支出', '净利润']
        values = [total_income, total_expense, net_profit]
        colors = ['#28a745', '#dc3545', '#17a2b8']
        
        bars = ax.bar(labels, values, color=colors, width=0.5)
        
        # 添加数据标签
        for bar in bars:
            height = bar.get_height()
            if height >= 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.02,
                        f'¥{height:.2f}', ha='center', va='bottom', fontsize=10)
            else:
                ax.text(bar.get_x() + bar.get_width()/2., height - max(values)*0.02,
                        f'¥{height:.2f}', ha='center', va='top', fontsize=10)
        
        # 设置图表属性
        ax.set_title(f'收支汇总 ({start_date} 至 {end_date})')
        ax.set_ylabel('金额 (元)')
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # 自动调整布局
        self.summary_figure.tight_layout()
        self.summary_canvas.draw()
    
    def update_profit_report(self, start_date, end_date):
        """更新利润分析报表"""
        # 查询每月/每周的收入和支出
        # 这里简化处理，按周查询
        profit_data = execute_query(
            """
            WITH date_range AS (
                SELECT date(transaction_date) as day, transaction_type, amount
                FROM transactions
                WHERE transaction_date BETWEEN ? AND ?
            )
            SELECT 
                strftime('%Y-%W', day) as week,
                SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expense,
            SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE -amount END) as profit
            FROM date_range
            GROUP BY week
            ORDER BY week
            """,
            (start_date, end_date),
            fetch_all=True
        )
        
        # 更新图表
        self.profit_figure.clear()
        ax = self.profit_figure.add_subplot(111)
        
        if profit_data:
            weeks = [data['week'] for data in profit_data]
            incomes = [data['income'] for data in profit_data]
            expenses = [data['expense'] for data in profit_data]
            profits = [data['profit'] for data in profit_data]
            
            # 创建堆叠柱状图
            ax.bar(weeks, incomes, label='收入', color='#28a745', alpha=0.8)
            ax.bar(weeks, [-exp for exp in expenses], label='支出', color='#dc3545', alpha=0.8)
            
            # 添加净利润折线
            ax.plot(weeks, profits, 'o-', color='#17a2b8', label='净利润', linewidth=2)
            
            # 添加零线
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
            
            # 设置标签
            ax.set_title(f'利润趋势分析 ({start_date} 至 {end_date})')
            ax.set_xlabel('周 (YYYY-WW)')
            ax.set_ylabel('金额 (元)')
            ax.legend()
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
            # 旋转x轴标签避免重叠
            plt.xticks(rotation=45, ha='right')
        else:
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title(f'利润趋势分析 ({start_date} 至 {end_date})')
        
        # 自动调整布局
        self.profit_figure.tight_layout()
        self.profit_canvas.draw()
    
    def update_category_report(self, start_date, end_date):
        """更新分类统计报表"""
        # 获取统计类型
        category_type = self.category_type_combo.currentText()
        type_val = "income" if category_type == "收入分类" else "expense"
        
        # 查询分类统计数据
        category_data = execute_query(
            """
            SELECT 
                c.name as category,
                SUM(t.amount) as total_amount,
                COUNT(*) as transaction_count
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.transaction_type = ? AND t.transaction_date BETWEEN ? AND ?
            GROUP BY c.name
            ORDER BY total_amount DESC
            """,
            (type_val, start_date, end_date),
            fetch_all=True
        )
        
        # 更新饼图
        self.category_pie_figure.clear()
        ax_pie = self.category_pie_figure.add_subplot(111)
        
        # 更新柱状图
        self.category_bar_figure.clear()
        ax_bar = self.category_bar_figure.add_subplot(111)
        
        if category_data:
            categories = [data['category'] for data in category_data]
            amounts = [data['total_amount'] for data in category_data]
            counts = [data['transaction_count'] for data in category_data]
            
            # 生成颜色
            colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
            
            # 创建饼图
            wedges, texts, autotexts = ax_pie.pie(
                amounts, labels=categories, autopct='%1.1f%%',
                shadow=False, startangle=90, colors=colors
            )
            
            # 设置饼图属性
            ax_pie.set_title(f'{category_type}占比')
            ax_pie.axis('equal')  # 保持饼图为圆形
            
            # 创建柱状图
            bars = ax_bar.bar(categories, amounts, color=colors)
            
            # 添加数据标签
            for bar in bars:
                height = bar.get_height()
                ax_bar.text(bar.get_x() + bar.get_width()/2., height + max(amounts)*0.02,
                        f'¥{height:.2f}', ha='center', va='bottom', fontsize=9)
            
            # 设置柱状图属性
            ax_bar.set_title(f'{category_type}金额统计')
            ax_bar.set_xlabel('分类')
            ax_bar.set_ylabel('金额 (元)')
            ax_bar.grid(axis='y', linestyle='--', alpha=0.7)
            
            # 旋转x轴标签避免重叠
            plt.setp(ax_bar.get_xticklabels(), rotation=45, ha='right')
        else:
            ax_pie.text(0.5, 0.5, '暂无数据', ha='center', va='center', transform=ax_pie.transAxes, fontsize=12)
            ax_pie.set_title(f'{category_type}占比')
            
            ax_bar.text(0.5, 0.5, '暂无数据', ha='center', va='center', transform=ax_bar.transAxes, fontsize=12)
            ax_bar.set_title(f'{category_type}金额统计')
        
        # 自动调整布局
        self.category_pie_figure.tight_layout()
        self.category_bar_figure.tight_layout()
        
        # 重绘图表
        self.category_pie_canvas.draw()
        self.category_bar_canvas.draw()
    
    def update_account_report(self, start_date, end_date):
        """更新账户余额报表"""
        # 查询账户余额数据
        account_data = execute_query(
            """
            WITH 
            -- 期初余额（开始日期之前的收支差额）
            opening_balance AS (
                SELECT
                    a.id,
                    a.name,
                    COALESCE(0.0 +
                    SUM(CASE WHEN t.transaction_type = 'income' THEN t.amount ELSE -t.amount END), 0.0) as balance
                FROM accounts a
                LEFT JOIN transactions t ON a.id = t.account_id AND t.transaction_date < ?
                GROUP BY a.id, a.name
            ),
            -- 期间变动
            period_changes AS (
                SELECT
                    a.id,
                    SUM(CASE WHEN t.transaction_type = 'income' THEN t.amount ELSE -t.amount END) as change
                FROM accounts a
                LEFT JOIN transactions t ON a.id = t.account_id AND t.transaction_date BETWEEN ? AND ?
                GROUP BY a.id
            )
            SELECT
                ob.name,
                COALESCE(ob.balance, 0.0) as opening_balance,
                COALESCE(ob.balance, 0.0) + COALESCE(pc.change, 0.0) as current_balance,
                COALESCE(pc.change, 0.0) as change_amount
            FROM opening_balance ob
            LEFT JOIN period_changes pc ON ob.id = pc.id
            ORDER BY ob.name
            """,
            (start_date, start_date, end_date),
            fetch_all=True
        )
        
        # 更新表格
        self.account_model.setRowCount(0)
        
        total_opening_balance = 0
        total_current_balance = 0
        total_change_amount = 0
        
        if account_data:
            for account in account_data:
                row_items = []
                
                # 账户名称
                row_items.append(QStandardItem(account['name']))
                row_items[-1].setEditable(False)
                
                # 期初余额
                opening_balance = account['opening_balance'] or 0
                row_items.append(QStandardItem(f"¥{opening_balance:.2f}"))
                row_items[-1].setEditable(False)
                row_items[-1].setTextAlignment(Qt.AlignRight)
                
                # 当前余额
                current_balance = account['current_balance'] or 0
                balance_item = QStandardItem(f"¥{current_balance:.2f}")
                balance_item.setEditable(False)
                balance_item.setTextAlignment(Qt.AlignRight)
                # 根据余额正负设置颜色
                if current_balance >= 0:
                    balance_item.setForeground(QColor("#28a745"))
                else:
                    balance_item.setForeground(QColor("#dc3545"))
                row_items.append(balance_item)
                
                # 变动金额
                change_amount = account['change_amount'] or 0
                change_item = QStandardItem(f"¥{change_amount:.2f}")
                change_item.setEditable(False)
                change_item.setTextAlignment(Qt.AlignRight)
                # 根据变动金额正负设置颜色
                if change_amount >= 0:
                    change_item.setForeground(QColor("#28a745"))
                else:
                    change_item.setForeground(QColor("#dc3545"))
                row_items.append(change_item)
                
                # 添加行到模型
                self.account_model.appendRow(row_items)
                
                # 计算总计
                total_opening_balance += opening_balance
                total_current_balance += current_balance
                total_change_amount += change_amount
            
            # 添加总计行
            total_row = [
                QStandardItem("总计"),
                QStandardItem(f"¥{total_opening_balance:.2f}"),
                QStandardItem(f"¥{total_current_balance:.2f}"),
                QStandardItem(f"¥{total_change_amount:.2f}")
            ]
            
            for item in total_row:
                item.setEditable(False)
                item.setFont(QFont("SimHei", 9, QFont.Bold))
                item.setBackground(QColor("#f8f9fa"))
            
            total_row[1].setTextAlignment(Qt.AlignRight)
            total_row[2].setTextAlignment(Qt.AlignRight)
            total_row[3].setTextAlignment(Qt.AlignRight)
            
            # 设置总计行颜色
            if total_current_balance >= 0:
                total_row[2].setForeground(QColor("#28a745"))
            else:
                total_row[2].setForeground(QColor("#dc3545"))
            
            if total_change_amount >= 0:
                total_row[3].setForeground(QColor("#28a745"))
            else:
                total_row[3].setForeground(QColor("#dc3545"))
            
            self.account_model.appendRow(total_row)
        
        # 更新图表
        self.account_figure.clear()
        ax = self.account_figure.add_subplot(111)
        
        if account_data:
            accounts = [account['name'] for account in account_data]
            current_balances = [account['current_balance'] for account in account_data]
            
            # 生成颜色（根据余额正负）
            colors = ['#28a745' if balance >= 0 else '#dc3545' for balance in current_balances]
            
            # 创建水平柱状图
            bars = ax.barh(accounts, current_balances, color=colors, alpha=0.8)
            
            # 添加数据标签
            for bar in bars:
                width = bar.get_width()
                if width >= 0:
                    ax.text(width + max(current_balances)*0.02, bar.get_y() + bar.get_height()/2.,
                            f'¥{width:.2f}', va='center', fontsize=9)
                else:
                    ax.text(width - max([abs(b) for b in current_balances])*0.02, bar.get_y() + bar.get_height()/2.,
                            f'¥{width:.2f}', va='center', ha='right', fontsize=9)
            
            # 添加零线
            ax.axvline(x=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
            
            # 设置图表属性
            ax.set_title(f'账户余额统计 ({start_date} 至 {end_date})')
            ax.set_xlabel('金额 (元)')
            ax.grid(axis='x', linestyle='--', alpha=0.7)
        else:
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title(f'账户余额统计 ({start_date} 至 {end_date})')
        
        # 自动调整布局
        self.account_figure.tight_layout()
        self.account_canvas.draw()
    
    def update_trend_report(self, start_date, end_date):
        """更新趋势分析报表"""
        try:
            # 获取时间粒度
            time_granularity = self.time_granularity_combo.currentText()
            
            if time_granularity == "按日":
                date_format = "%Y-%m-%d"
                date_group = "date(transaction_date)"
            elif time_granularity == "按月":
                date_format = "%Y-%m"
                date_group = "strftime('%Y-%m', transaction_date)"
            else:  # 按季度
                date_format = "%Y-Q%q"
                date_group = "strftime('%Y', transaction_date) || '-Q' || ((strftime('%m', transaction_date) - 1) / 3 + 1)"
            
            # 查询趋势数据
            print(f"正在执行趋势分析SQL查询，时间粒度: {time_granularity}")
            trend_data = execute_query(
                f"""
                WITH date_range AS (
                    SELECT 
                        {date_group} as period,
                        transaction_type,
                        amount
                    FROM transactions
                    WHERE transaction_date BETWEEN ? AND ?
                )
                SELECT 
                    period,
                    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expense
                FROM date_range
                GROUP BY period
                ORDER BY period
                """,
                (start_date, end_date),
                fetch_all=True
            )
            
            print(f"趋势分析查询结果类型: {type(trend_data)}, 内容: {trend_data}")
            
            # 更新图表
            self.trend_figure.clear()
            ax = self.trend_figure.add_subplot(111)
            
            if trend_data:
                periods = [data['period'] for data in trend_data]
                incomes = [data['income'] for data in trend_data]
                expenses = [data['expense'] for data in trend_data]
                
                # 创建折线图
                ax.plot(periods, incomes, 'o-', color='#28a745', label='收入', linewidth=2)
                ax.plot(periods, expenses, 's-', color='#dc3545', label='支出', linewidth=2)
                
                # 计算并绘制累计利润
                cumulative_profit = []
                current_profit = 0
                for i in range(len(incomes)):
                    current_profit += incomes[i] - expenses[i]
                    cumulative_profit.append(current_profit)
                
                ax.plot(periods, cumulative_profit, 'd-', color='#17a2b8', label='累计利润', linewidth=2)
                
                # 添加零线
                ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
                
                # 设置图表属性
                ax.set_title(f'收支趋势分析 ({start_date} 至 {end_date})')
                ax.set_xlabel(f'时间 ({time_granularity})')
                ax.set_ylabel('金额 (元)')
                ax.legend()
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # 旋转x轴标签避免重叠
                plt.xticks(rotation=45, ha='right')
            else:
                ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', transform=ax.transAxes, fontsize=12)
                ax.set_title(f'收支趋势分析 ({start_date} 至 {end_date})')
            
            # 自动调整布局
            self.trend_figure.tight_layout()
            self.trend_canvas.draw()
            print("趋势分析报表更新完成")
        except Exception as e:
            import traceback
            print("更新趋势分析报表失败:", str(e))
            print("错误堆栈:", traceback.format_exc())
            raise


if __name__ == "__main__":
    # 用于测试报表分析组件
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置应用程序字体
    font = QFont("SimHei", 9)
    app.setFont(font)
    
    # 创建用户信息（用于测试）
    test_user = {
        'id': 1,
        'username': 'admin',
        'fullname': '系统管理员',
        'role': 'admin'
    }
    
    # 创建并显示报表分析组件
    widget = ReportWidget(test_user)
    widget.setWindowTitle("报表分析测试")
    widget.resize(1000, 800)
    widget.show()
    
    sys.exit(app.exec_())