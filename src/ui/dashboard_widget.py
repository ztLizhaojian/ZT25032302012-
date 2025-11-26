#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪表盘组件模块
实现系统的仪表盘和数据可视化界面
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QDateEdit, QGroupBox, QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor, QPainter, QPen

# 导入可视化控制器
try:
    from src.controllers.visualization_controller import visualization_controller
    CONTROLLER_READY = True
except ImportError as e:
    logging.error(f"导入可视化控制器失败: {str(e)}")
    CONTROLLER_READY = False

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs', 'dashboard.log')),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("DashboardWidget")


class ChartWidget(QWidget):
    """
    图表显示组件
    用于显示各类可视化图表
    """
    
    def __init__(self, title="图表", parent=None):
        """
        初始化图表组件
        
        Args:
            title: 图表标题
            parent: 父组件
        """
        super().__init__(parent)
        self.title = title
        
        # 设置组件布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建标题标签
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)
        
        # 创建图表显示标签
        self.chart_label = QLabel()
        self.chart_label.setAlignment(Qt.AlignCenter)
        self.chart_label.setMinimumHeight(200)
        self.chart_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.chart_label)
        
        # 设置样式
        self.setStyleSheet("""
            ChartWidget {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }
            QLabel {
                color: #333;
            }
        """)
    
    def set_chart_data(self, chart_data):
        """
        设置图表数据
        
        Args:
            chart_data: 图表字节数据
        """
        try:
            if chart_data:
                # 从字节数据创建QPixmap
                image = QImage.fromData(chart_data)
                pixmap = QPixmap.fromImage(image)
                
                # 缩放图片以适应标签
                scaled_pixmap = pixmap.scaled(
                    self.chart_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                self.chart_label.setPixmap(scaled_pixmap)
            else:
                # 如果没有数据，显示提示信息
                self.chart_label.setText("暂无图表数据")
                self.chart_label.setPixmap(QPixmap())
                
        except Exception as e:
            logger.error(f"设置图表数据失败: {str(e)}")
            self.chart_label.setText(f"图表加载失败: {str(e)}")
    
    def resizeEvent(self, event):
        """
        窗口大小改变事件处理
        """
        super().resizeEvent(event)
        
        # 重新缩放图表
        if hasattr(self.chart_label, 'pixmap') and self.chart_label.pixmap():
            scaled_pixmap = self.chart_label.pixmap().scaled(
                self.chart_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.chart_label.setPixmap(scaled_pixmap)


class StatCardWidget(QWidget):
    """
    统计卡片组件
    用于显示关键指标和统计数据
    """
    
    def __init__(self, title="统计", value="0", subtitle="", color="#17a2b8", parent=None):
        """
        初始化统计卡片
        
        Args:
            title: 卡片标题
            value: 统计值
            subtitle: 副标题
            color: 卡片颜色
            parent: 父组件
        """
        super().__init__(parent)
        
        # 设置组件布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建标题标签
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Arial", 10))
        self.title_label.setStyleSheet(f"color: {color};")
        self.layout.addWidget(self.title_label)
        
        # 创建值标签
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.value_label.setStyleSheet("color: #333;")
        self.layout.addWidget(self.value_label)
        
        # 创建副标题标签
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setFont(QFont("Arial", 9))
        self.subtitle_label.setStyleSheet("color: #666;")
        self.layout.addWidget(self.subtitle_label)
        
        # 设置样式
        self.setStyleSheet("""
            StatCardWidget {
                background-color: white;
                border-radius: 8px;
                border-left: 4px solid %s;
            }
        """ % color)
        
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    
    def set_value(self, value):
        """
        设置统计值
        
        Args:
            value: 新的统计值
        """
        self.value_label.setText(value)
    
    def set_title(self, title):
        """
        设置标题
        
        Args:
            title: 新的标题
        """
        self.title_label.setText(title)
    
    def set_subtitle(self, subtitle):
        """
        设置副标题
        
        Args:
            subtitle: 新的副标题
        """
        self.subtitle_label.setText(subtitle)
    
    def set_color(self, color):
        """
        设置卡片颜色
        
        Args:
            color: 新的颜色
        """
        self.title_label.setStyleSheet("color: %s;" % color)
        self.setStyleSheet("""
            StatCardWidget {
                background-color: white;
                border-radius: 8px;
                border-left: 4px solid %s;
            }
        """ % color)


class DateRangeSelector(QWidget):
    """
    日期范围选择器组件
    用于选择数据统计的时间范围
    """
    
    # 信号定义
    dateRangeChanged = pyqtSignal(datetime, datetime)
    
    def __init__(self, parent=None):
        """
        初始化日期范围选择器
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        # 设置组件布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建快速选择组合框
        self.quick_select_combo = QComboBox()
        self.quick_select_combo.addItems([
            "最近7天",
            "最近30天",
            "最近90天",
            "本月",
            "上月",
            "本季度",
            "本年",
            "自定义范围"
        ])
        self.quick_select_combo.currentIndexChanged.connect(self._on_quick_select_changed)
        self.layout.addWidget(QLabel("时间范围:"))
        self.layout.addWidget(self.quick_select_combo)
        
        # 添加分隔符
        self.layout.addSpacing(10)
        
        # 创建开始日期选择器
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.dateChanged.connect(self._on_date_changed)
        self.layout.addWidget(QLabel("开始日期:"))
        self.layout.addWidget(self.start_date_edit)
        
        # 添加分隔符
        self.layout.addSpacing(10)
        
        # 创建结束日期选择器
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.dateChanged.connect(self._on_date_changed)
        self.layout.addWidget(QLabel("结束日期:"))
        self.layout.addWidget(self.end_date_edit)
        
        # 添加分隔符
        self.layout.addStretch()
        
        # 设置样式
        self.setStyleSheet("""
            QComboBox, QDateEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLabel {
                color: #333;
            }
        """)
    
    def _on_quick_select_changed(self, index):
        """
        快速选择时间范围变更处理
        
        Args:
            index: 选择的索引
        """
        current_date = QDate.currentDate()
        
        if index == 0:  # 最近7天
            start_date = current_date.addDays(-6)
            end_date = current_date
        elif index == 1:  # 最近30天
            start_date = current_date.addDays(-29)
            end_date = current_date
        elif index == 2:  # 最近90天
            start_date = current_date.addDays(-89)
            end_date = current_date
        elif index == 3:  # 本月
            start_date = current_date.addDays(1 - current_date.day())
            end_date = current_date
        elif index == 4:  # 上月
            last_month = current_date.addMonths(-1)
            start_date = last_month.addDays(1 - last_month.day())
            # 计算上月最后一天
            end_date = current_date.addDays(1 - current_date.day()).addDays(-1)
        elif index == 5:  # 本季度
            quarter = (current_date.month() - 1) // 3
            start_month = quarter * 3 + 1
            start_date = QDate(current_date.year(), start_month, 1)
            end_date = current_date
        elif index == 6:  # 本年
            start_date = QDate(current_date.year(), 1, 1)
            end_date = current_date
        else:  # 自定义范围
            # 不做任何操作，保持用户选择的日期
            return
        
        # 更新日期选择器
        self.start_date_edit.setDate(start_date)
        self.end_date_edit.setDate(end_date)
        
        # 发送日期范围变更信号
        self._emit_date_range_changed()
    
    def _on_date_changed(self):
        """
        日期变更处理
        """
        # 如果用户手动修改了日期，将快速选择设为"自定义范围"
        self.quick_select_combo.setCurrentIndex(7)
        
        # 确保开始日期不晚于结束日期
        if self.start_date_edit.date() > self.end_date_edit.date():
            self.end_date_edit.setDate(self.start_date_edit.date())
        
        # 发送日期范围变更信号
        self._emit_date_range_changed()
    
    def _emit_date_range_changed(self):
        """
        发送日期范围变更信号
        """
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        self.dateRangeChanged.emit(start_date, end_date)
    
    def get_date_range(self):
        """
        获取当前选择的日期范围
        
        Returns:
            tuple: (开始日期, 结束日期)
        """
        return (
            self.start_date_edit.date().toPyDate(),
            self.end_date_edit.date().toPyDate()
        )


class DashboardWidget(QWidget):
    """
    仪表盘主组件
    整合所有可视化元素，提供数据概览
    """
    
    def __init__(self, parent=None):
        """
        初始化仪表盘
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        # 设置组件布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # 创建日期范围选择器
        self.date_selector = DateRangeSelector()
        self.date_selector.dateRangeChanged.connect(self._on_date_range_changed)
        self.main_layout.addWidget(self.date_selector)
        
        # 创建统计卡片网格布局
        self.stats_layout = QGridLayout()
        self.stats_layout.setSpacing(10)
        
        # 创建统计卡片
        self.total_income_card = StatCardWidget(
            title="总收入",
            value="¥0.00",
            subtitle="所选时间段",
            color="#28a745"
        )
        
        self.total_expense_card = StatCardWidget(
            title="总支出",
            value="¥0.00",
            subtitle="所选时间段",
            color="#dc3545"
        )
        
        self.net_amount_card = StatCardWidget(
            title="净收支",
            value="¥0.00",
            subtitle="所选时间段",
            color="#17a2b8"
        )
        
        self.total_balance_card = StatCardWidget(
            title="账户总余额",
            value="¥0.00",
            subtitle="所有账户",
            color="#ffc107"
        )
        
        # 添加统计卡片到网格布局
        self.stats_layout.addWidget(self.total_income_card, 0, 0)
        self.stats_layout.addWidget(self.total_expense_card, 0, 1)
        self.stats_layout.addWidget(self.net_amount_card, 0, 2)
        self.stats_layout.addWidget(self.total_balance_card, 0, 3)
        
        self.main_layout.addLayout(self.stats_layout)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 创建滚动区域内容部件
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(15)
        
        # 创建图表区域1：收支对比和分类饼图
        self.charts_row1_layout = QHBoxLayout()
        self.charts_row1_layout.setSpacing(15)
        
        self.income_expense_chart = ChartWidget("收支对比图表")
        self.category_pie_chart = ChartWidget("支出分类占比")
        
        self.charts_row1_layout.addWidget(self.income_expense_chart)
        self.charts_row1_layout.addWidget(self.category_pie_chart)
        
        self.scroll_layout.addLayout(self.charts_row1_layout)
        
        # 创建图表区域2：趋势图
        self.trend_chart = ChartWidget("收支趋势图")
        self.scroll_layout.addWidget(self.trend_chart)
        
        # 创建图表区域3：账户余额和利润分析
        self.charts_row3_layout = QHBoxLayout()
        self.charts_row3_layout.setSpacing(15)
        
        self.account_balance_chart = ChartWidget("账户余额分布")
        self.profit_analysis_chart = ChartWidget("利润分析")
        
        self.charts_row3_layout.addWidget(self.account_balance_chart)
        self.charts_row3_layout.addWidget(self.profit_analysis_chart)
        
        self.scroll_layout.addLayout(self.charts_row3_layout)
        
        # 添加底部间距
        self.scroll_layout.addStretch()
        
        # 设置滚动区域
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area, 1)
        
        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
            QScrollArea {
                border: none;
            }
        """)
        
        # 初始化加载数据
        self._load_dashboard_data()
    
    def _on_date_range_changed(self, start_date, end_date):
        """
        日期范围变更处理
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        """
        logger.info(f"日期范围变更: {start_date} 至 {end_date}")
        self._load_dashboard_data()
    
    def _load_dashboard_data(self):
        """
        加载仪表盘数据
        """
        if not CONTROLLER_READY:
            logger.warning("可视化控制器未就绪，显示模拟数据")
            self._show_mock_data()
            return
        
        try:
            # 获取选择的日期范围
            start_date, end_date = self.date_selector.get_date_range()
            
            # 加载收支对比图表
            logger.info("正在加载收支对比图表...")
            income_expense_result = visualization_controller.generate_income_expense_chart(start_date, end_date)
            if income_expense_result["success"]:
                self.income_expense_chart.set_chart_data(income_expense_result["chart_data"])
                
                # 更新统计卡片
                summary = income_expense_result.get("summary", {})
                self.total_income_card.set_value(f"¥{summary.get('total_income', 0):,.2f}")
                self.total_expense_card.set_value(f"¥{summary.get('total_expense', 0):,.2f}")
                
                net_amount = summary.get('net_amount', 0)
                self.net_amount_card.set_value(f"¥{net_amount:,.2f}")
                # 根据净收支调整颜色
                if net_amount >= 0:
                    self.net_amount_card.set_color("#28a745")  # 绿色表示盈利
                else:
                    self.net_amount_card.set_color("#dc3545")  # 红色表示亏损
            else:
                logger.error(f"加载收支对比图表失败: {income_expense_result.get('error')}")
            
            # 加载分类饼图
            logger.info("正在加载支出分类饼图...")
            category_pie_result = visualization_controller.generate_category_pie_chart(start_date, end_date, 'expense')
            if category_pie_result["success"]:
                self.category_pie_chart.set_chart_data(category_pie_result["chart_data"])
            else:
                logger.error(f"加载分类饼图失败: {category_pie_result.get('error')}")
            
            # 加载趋势图
            logger.info("正在加载收支趋势图...")
            trend_result = visualization_controller.generate_trend_chart(start_date, end_date, 'month')
            if trend_result["success"]:
                self.trend_chart.set_chart_data(trend_result["chart_data"])
            else:
                logger.error(f"加载趋势图失败: {trend_result.get('error')}")
            
            # 加载账户余额图表
            logger.info("正在加载账户余额图表...")
            account_balance_result = visualization_controller.generate_account_balance_chart()
            if account_balance_result["success"]:
                self.account_balance_chart.set_chart_data(account_balance_result["chart_data"])
                self.total_balance_card.set_value(f"¥{account_balance_result.get('total_balance', 0):,.2f}")
            else:
                logger.error(f"加载账户余额图表失败: {account_balance_result.get('error')}")
            
            # 加载利润分析图表
            logger.info("正在加载利润分析图表...")
            profit_analysis_result = visualization_controller.generate_profit_analysis_chart(start_date, end_date)
            if profit_analysis_result["success"]:
                self.profit_analysis_chart.set_chart_data(profit_analysis_result["chart_data"])
            else:
                logger.error(f"加载利润分析图表失败: {profit_analysis_result.get('error')}")
            
            logger.info("仪表盘数据加载完成")
            
        except Exception as e:
            logger.error(f"加载仪表盘数据失败: {str(e)}")
            self._show_mock_data()
    
    def _show_mock_data(self):
        """
        显示模拟数据（当控制器未就绪或加载失败时）
        """
        # 更新统计卡片
        self.total_income_card.set_value("¥500,000.00")
        self.total_expense_card.set_value("¥350,000.00")
        self.net_amount_card.set_value("¥150,000.00")
        self.total_balance_card.set_value("¥605,000.00")
        
        # 显示提示信息
        self.income_expense_chart.chart_label.setText("[模拟数据] 收支对比图表")
        self.category_pie_chart.chart_label.setText("[模拟数据] 支出分类占比")
        self.trend_chart.chart_label.setText("[模拟数据] 收支趋势图")
        self.account_balance_chart.chart_label.setText("[模拟数据] 账户余额分布")
        self.profit_analysis_chart.chart_label.setText("[模拟数据] 利润分析")
    
    def refresh_data(self):
        """
        刷新仪表盘数据
        """
        logger.info("刷新仪表盘数据")
        self._load_dashboard_data()


if __name__ == "__main__":
    # 测试仪表盘组件
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建仪表盘窗口
    dashboard = DashboardWidget()
    dashboard.setWindowTitle("企业财务仪表盘")
    dashboard.resize(1200, 800)
    dashboard.show()
    
    sys.exit(app.exec_())