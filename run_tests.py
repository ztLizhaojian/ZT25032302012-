#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试运行器
执行项目中的所有测试脚本
"""
import os
import sys
import time
import unittest
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import LoggerManager


def run_tests():
    """
    运行所有测试
    """
    # 设置日志
    LoggerManager.init_logging()
    logger = LoggerManager.get_logger('test_runner')
    
    print("\n" + "=" * 80)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行项目测试套件")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 发现并运行所有测试
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover('tests', pattern='test_*.py')
        
        # 运行测试
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 测试执行完成")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"测试统计: 运行 {result.testsRun} 个测试")
        print(f"          成功: {result.testsRun - len(result.failures) - len(result.errors)} 个")
        print(f"          失败: {len(result.failures)} 个")
        print(f"          错误: {len(result.errors)} 个")
        print(f"          跳过: {len(result.skipped)} 个")
        print("=" * 80)
        
        if result.wasSuccessful():
            print("\n🎉 所有测试通过！")
            return 0
        else:
            print("\n❌ 测试失败！")
            return 1
            
    except Exception as e:
        logger.error(f"执行测试时发生错误: {str(e)}")
        print(f"\n❌ 执行测试时发生错误: {str(e)}")
        return 2


def run_specific_test(test_name):
    """
    运行特定的测试
    
    Args:
        test_name: 测试名称，可以是测试类名或测试方法名
    """
    # 设置日志
    LoggerManager.init_logging()
    logger = LoggerManager.get_logger('test_runner')
    
    print("\n" + "=" * 80)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 运行特定测试: {test_name}")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 发现所有测试
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover('tests', pattern='test_*.py')
        
        # 筛选特定测试
        specific_suite = unittest.TestSuite()
        for test_case in test_suite:
            for test in test_case:
                # 检查测试名称是否匹配
                if test_name in str(test):
                    specific_suite.addTest(test)
        
        if not specific_suite.countTestCases():
            print(f"\n❌ 未找到匹配的测试: {test_name}")
            return 3
        
        # 运行特定测试
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(specific_suite)
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 特定测试执行完成")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"测试统计: 运行 {result.testsRun} 个测试")
        print(f"          成功: {result.testsRun - len(result.failures) - len(result.errors)} 个")
        print(f"          失败: {len(result.failures)} 个")
        print(f"          错误: {len(result.errors)} 个")
        print("=" * 80)
        
        if result.wasSuccessful():
            print("\n🎉 特定测试通过！")
            return 0
        else:
            print("\n❌ 特定测试失败！")
            return 1
            
    except Exception as e:
        logger.error(f"执行特定测试时发生错误: {str(e)}")
        print(f"\n❌ 执行特定测试时发生错误: {str(e)}")
        return 2


def main():
    """
    主函数
    """
    # 确保tests目录存在
    if not os.path.exists('tests'):
        print("❌ 未找到tests目录！")
        return 4
    
    # 检查是否有参数指定特定测试
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        return run_specific_test(test_name)
    else:
        # 运行所有测试
        return run_all_tests()


def run_all_tests():
    """
    运行所有测试的便捷函数
    """
    return run_tests()


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
