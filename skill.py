"""
龙析代码质量分析工具 - AI Agent Skill 入口文件

该文件是项目的入口模块，符合AI Agent Skill的标准目录结构。
实际的实现代码位于 ./src/CdanalyzerAgentSkill.py
"""

import json
import asyncio
from src.CdanalyzerAgentSkill import CdanalyzerAgentSkill  # 确保导入路径正确

# 创建全局实例
cdanalyzer_agent = CdanalyzerAgentSkill()

def execute(inputs: dict) -> dict:
    """
    执行代码质量分析的主要方法
    
    Args:
        inputs: 输入参数字典
            - target_path: 目标路径
            - language_types: 语言类型列表
            - analysis_standard: 分析标准
            - exclude_patterns: 排除模式
            - report_format: 报告格式
            - report_path: 报告路径
            - ui_mode: UI模式
    
    Returns:
        包含执行结果的字典
    """
    return asyncio.run(cdanalyzer_agent.execute(inputs))

def run_skill(inputs: dict) -> dict:
    """
    同步执行技能的方法
    
    Args:
        inputs: 输入参数字典
    
    Returns:
        包含执行结果的字典
    """
    return cdanalyzer_agent.run_skill(inputs)

# 导出主要类和函数
__all__ = ['CdanalyzerAgentSkill', 'execute', 'run_skill', 'cdanalyzer_agent']