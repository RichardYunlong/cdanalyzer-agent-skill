# 🐉【龙析】AI代码质量分析工具

<div align="center">
  <img src="cdico_64_64.jpg" alt="龙析 Logo" width="128" height="128">
  
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
  [![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)
  
  🔍 **智能代码审查** | 🤖 **AI驱动分析** | 📊 **详细报告生成**
</div>

---

## 📖 项目简介

**【龙析】** 是一款先进的AI驱动代码质量分析工具，专为开发者设计，旨在帮助您识别代码中的潜在风险、改进代码质量并提升开发效率。通过集成大语言模型技术，龙析不仅能发现传统静态分析工具检测的问题，还能提供智能化的修复建议。

### ✨ 主要特性

- 🧠 **AI驱动分析** - 利用大语言模型提供深度代码分析
- 🌐 **多语言支持** - 支持Python、JavaScript、Java、C++等多种编程语言
- 📋 **详细报告** - 生成HTML、PDF、TXT等多种格式的详细报告
- 🔍 **风险分级** - 按照风险等级分类问题（致命、高级、中级、普通）
- ⚙️ **灵活配置** - 可自定义分析标准和排除规则
- 🚀 **高效性能** - 针对大型项目优化的分析算法

---

## 🛠️ 系统要求

- 🐍 **Python版本**: 3.8 或更高版本
- 💻 **操作系统**: Windows 10/11、Linux 或 macOS
- 💾 **内存**: 至少 4GB RAM（推荐 8GB+）
- 💿 **磁盘空间**: 至少 100MB 可用空间
- 🌐 **网络**: 访问大语言模型 API（可选）

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd cdanalyzer-agent-skill
```

### 2. 创建虚拟环境

```powershell
# Windows PowerShell
python -m venv ai-skill-env
.\ai-skill-env\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv ai-skill-env
source ai-skill-env/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量（可选）

创建 `.env` 文件配置大模型API密钥：

```env
# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 阿里云通义千问配置
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# 智谱AI配置
ZHIPU_API_KEY=your_zhipu_api_key
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4

# Ollama配置（本地模型）
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3
```

---

## 📁 项目结构

```
cdanalyzer-agent-skill/
├── skill.py              # 项目入口文件
├── config.json           # 配置文件
├── requirements.txt      # 依赖列表
├── README.md            # 项目说明文档
├── .env                 # 环境变量配置文件（本地）
├── cdico_64_64.jpg      # Logo 图片
├── __init__.py          # Python包初始化文件
├── validate_env.py      # 环境验证脚本
├── src/                 # 源代码目录
│   └── CdanalyzerAgentSkill.py  # 核心实现代码
├── tests/               # 测试文件目录
│   ├── custom_test.py   # 自定义测试文件
│   └── __init__.py      # 测试包初始化文件
├── reports/             # 报告输出目录
└── temp/                # 临时文件目录
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量（可选）

创建 `.env` 文件配置大模型API密钥：

```env
# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 阿里云通义千问配置
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# 智谱AI配置
ZHIPU_API_KEY=your_zhipu_api_key
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4

# Ollama配置（本地模型）
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3
```

---

## ⚙️ 配置说明

### 配置参数详解

| 参数 | 类型 | 必需 | 描述 | 示例 |
|------|------|------|------|------|
| `target_path` | String | ✅ | 待分析的项目路径或文件路径 | `"./my-project"` |
| `language_types` | Array | ❌ | 编程语言类型清单 | `["python", "javascript"]` |
| `analysis_standard` | Object | ❌ | 各种语言的分析标准配置 | `{"python": "pylint"}` |
| `exclude_patterns` | Array | ❌ | 排除的文件或文件夹模式 | `[".git", "__pycache__"]` |
| `report_format` | Array | ❌ | 报告输出格式 | `["html", "pdf", "txt"]` |
| `report_path` | String | ❌ | 分析报告保存路径 | `"./reports"` |
| `ui_mode` | Boolean | ❌ | 是否使用UI界面运行 | `false` |
| `llm_provider` | String | ❌ | 大模型提供商 | `"openai"` |
| `llm_api_key` | String | ❌ | 大模型API密钥 | `"sk-..."` |
| `llm_base_url` | String | ❌ | 大模型API基础URL | `"https://api.openai.com/v1"` |
| `llm_model` | String | ❌ | 大模型名称 | `"gpt-3.5-turbo"` |
| `llm_top_p` | Number | ❌ | top_p参数，控制输出多样性 | `0.7` |

### 默认配置

- 🚫 **自动排除**: `.git`, `.svn`, `__pycache__`, `.gitignore` 等版本控制相关文件
- 🌐 **支持的语言及默认分析标准**:
  - 🐍 **Python**: pylint
  - ⚡ **JavaScript**: eslint
  - ☕ **Java**: checkstyle
  - 🅰️ **C++**: cppcheck
  - #️⃣ **C#**: roslyn-analyzers
  - 🐹 **Go**: golangci-lint
  - 🌟 **TypeScript**: typescript-eslint

---

## 🛠️ 使用方法

### 基本使用

```python
from skill import CdanalyzerAgentSkill

skill = CdanalyzerAgentSkill()

# 基础分析
result = skill.run_skill({
    "target_path": "/path/to/your/project",
    "report_format": ["html", "txt"]
})

print(result)
```

### 完整配置示例

```python
from skill import CdanalyzerAgentSkill

skill = CdanalyzerAgentSkill()

# 配置大模型（可选）
skill.set_llm_config(
    provider="openai",           # 或 "qwen", "zhipu", "ollama"
    api_key="your-api-key",      # 如已在环境变量中配置，可省略
    model="gpt-3.5-turbo",       # 或其他模型名称
    top_p=0.7
)

result = skill.run_skill({
    "target_path": "/path/to/your/project",
    "language_types": ["python", "javascript"],
    "analysis_standard": {
        "python": "pylint",
        "javascript": "eslint"
    },
    "exclude_patterns": [".git", "__pycache__", "node_modules", "*.log"],
    "report_format": ["html", "pdf", "txt"],
    "report_path": "./reports",
    "ui_mode": False,
    "llm_provider": "openai",
    "llm_model": "gpt-3.5-turbo"
})

print(result)
```

### 分析单个文件

```python
result = skill.run_skill({
    "target_path": "/path/to/your/file.py",
    "report_format": ["html"]
})
print(result)
```

---

## 🧪 测试说明

### 运行单元测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/custom_test.py -v
```

### 自定义测试示例

创建 `tests/custom_test.py`：

```python
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
```

运行测试：python -m pytest tests\custom_test.py::CustomTest::test_custom_scenario_explicit_formats -s
         或者
         python -m pytest tests\custom_test.py

### 测试覆盖范围

- 📁 目标文件识别功能
- 🔍 排除模式匹配
- 📋 分析标准确认
- 🌐 语言类型检测
- 📊 报告生成功能

---

## 📊 报告说明

### 报告类型

- 🌐 **HTML报告**: 包含交互式界面，可排序、筛选和搜索分析结果
- 📄 **PDF报告**: 便于分享和打印，支持中文字体渲染
- 📝 **文本报告**: 适用于命令行环境和自动化处理

### 风险等级

| 等级 | 颜色 | 说明 |
|------|------|------|
| 🐲 **致命** 🔴 | 红色 | 可能导致程序崩溃或严重安全问题 |
| ⚠️ **高级** 🟠 | 橙色 | 严重的逻辑错误或安全隐患 |
| ⚡ **中级** 🟡 | 黄色 | 潜在的问题或不良实践 |
| ℹ️ **普通** 🟨 | 浅黄 | 代码风格或小的潜在问题 |

### 报告内容

每份报告包含：

1. 📈 **项目概览**
   - 分析文件数量
   - 总代码行数
   - 各语言代码占比

2. 📊 **风险统计**
   - 各级别风险数量统计
   - 风险分布图表

3. 📋 **详细问题列表**
   - 风险说明
   - 出现位置（文件路径和行号）
   - 影响范围
   - 原因分析
   - 危害说明
   - 解决方案（提供多种选择）
   - 🧠 **AI建议** - 由大语言模型生成的修复建议

---

## 🤖 大模型集成

龙析支持多种大语言模型提供商：

### 支持的提供商

- 🤖 **OpenAI**: GPT系列模型
- 🌐 **阿里云通义千问**: Qwen系列模型
- 🤖 **智谱AI**: GLM系列模型
- 🏠 **Ollama**: 本地模型（无需API密钥）

### AI分析功能

- 🔍 **问题识别**: 识别代码中的潜在错误和安全漏洞
- 💡 **修复建议**: 提供具体的修复方案
- 📚 **原因解释**: 解释问题的根本原因
- 🎯 **最佳实践**: 推荐行业最佳实践

---

## 🔧 故障排除

### 常见问题

#### ❗ 路径不存在错误
- **问题**: `ValueError: 目标路径不存在`
- **解决方案**: 检查提供的路径是否正确，确保路径存在且具有访问权限

#### 🌐 语言类型未识别
- **问题**: 无法识别某些代码文件的语言类型
- **解决方案**: 确保文件有正确的扩展名，或手动指定语言类型

#### 📦 依赖库缺失
- **问题**: 导入模块时出错
- **解决方案**: 确保已正确安装所有依赖项
  ```bash
  pip install -r requirements.txt
  ```

### 调试方法

#### 环境检查
运行环境验证脚本：
```python
from validate_env import main
main()
```

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🚀 性能优化建议

- ⏱️ **分批分析**: 对大型项目分批分析以减少内存占用
- 🗂️ **排除模式**: 使用适当的排除模式减少不必要的文件分析
- 📄 **选择格式**: 选择性生成报告格式以节省资源
- 🗑️ **定期清理**: 定期清理旧的报告和日志文件

---

## 🛠️ 扩展功能

### 添加新语言支持

修改 `src/CdanalyzerAgentSkill.py` 中的 `language_extensions` 字典和 `_get_language_from_extension` 方法：

```python
language_extensions = {
    # ... 现有语言 ...
    '.new_ext': 'new_language'  # 新增语言支持
}

def _get_language_from_extension(self, ext: str) -> str:
    ext_map = {
        # ... 现有映射 ...
        '.new_ext': 'new_language'  # 新增语言映射
    }
    return ext_map.get(ext)
```

### 自定义分析标准

通过 `analysis_standard` 参数指定自定义分析标准：

```python
{
    "analysis_standard": {
        "python": "custom_pylint_config",
        "javascript": "custom_eslint_config"
    }
}
```

---

## 📄 许可证

该项目遵循 MIT 许可证。更多信息请参见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献

欢迎提交 Pull Request 来改进项目！对于重大更改，请先开 Issue 讨论您想要更改的内容。

### 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## ❤️ 致谢

感谢所有为本项目做出贡献的人！

- 阿里云通义千问团队提供技术支持
- OpenAI 提供 GPT 模型 API
- 社区开发者提供的反馈和建议

---

<div align="center">
  <p>Made with ❤️ by the龙析团队</p>
  <p>如果您觉得这个项目有用，请给我们一个 ⭐ Star!</p>
</div>