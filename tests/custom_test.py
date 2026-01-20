import unittest
import sys
import os
import tempfile

from skill import CdanalyzerAgentSkill

class CustomTest(unittest.TestCase):
    def setUp(self):
        self.skill = CdanalyzerAgentSkill()
    
    def test_custom_scenario_explicit_formats(self): 
        # 显式请求多种格式的报告
        result = self.skill.run_skill({
            "target_path": "D:\\hewei\\pyWorkspace\\cdanalyzer-agent-skill\\temp",
            "report_format": ["html", "txt", "pdf"]  # 显式指定三种格式
        })
        self.assertTrue(result["success"], msg=f"测试失败: {result.get('error', '未知错误')}")

if __name__ == '__main__':
    unittest.main()