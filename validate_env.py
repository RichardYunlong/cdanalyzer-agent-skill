#!/usr/bin/env python3
"""
验证AI技能开发环境是否正确配置
"""

import sys
import os

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        return False
    print("✓ Python版本检查通过")
    return True

def check_dependencies():
    """检查依赖项"""
    try:
        import numpy
        import requests
        print("✓ 依赖项检查通过")
        return True
    except ImportError as e:
        print(f"错误: 缺少依赖项 {e}")
        return False

def check_structure():
    """检查项目结构"""
    required_files = ['skill.py', 'config.json', 'requirements.txt', '__init__.py']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"错误: 缺少文件 {missing_files}")
        return False
    
    print("✓ 项目结构检查通过")
    return True

def test_skill():
    """测试技能功能"""
    try:
        from skill import CdanalyzerAgentSkill
        skill = CdanalyzerAgentSkill()
        result = skill.run_skill({"query": "test"})
        print("✓ 技能功能测试通过")
        return True
    except Exception as e:
        print(f"错误: 技能测试失败 {e}")
        import traceback
        traceback.print_exc()  # 打印详细错误信息
        return False

def main():
    print("正在验证AI技能开发环境...")
    
    checks = [
        ("Python版本", check_python_version),
        ("依赖项", check_dependencies), 
        ("项目结构", check_structure),
        ("技能功能", test_skill)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n正在检查: {name}")
        if not check_func():
            all_passed = False
    
    print("\n" + "="*40)
    if all_passed:
        print("✓ 所有检查都通过！开发环境配置完成")
    else:
        print("✗ 有些检查未通过，请根据错误信息修复问题")

if __name__ == "__main__":
    main()