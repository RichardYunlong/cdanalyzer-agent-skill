import json
import asyncio
import os
import fnmatch
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict
import re
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

class CdanalyzerAgentSkill:
    def __init__(self):
        """
        初始化代码质量分析工具
        """
        self.name = "CdanalyzerAgentSkill"
        self.version = "1.0.0"
        self.default_standards = {
            "python": "pylint",
            "javascript": "eslint",
            "java": "checkstyle",
            "cpp": "cppcheck",
            "csharp": "roslyn-analyzers",
            "go": "golangci-lint",
            "typescript": "typescript-eslint"
        }
        self.risk_levels = {
            "critical": {"weight": 4, "color": "#ff0000", "label": "致命"},      # 红色
            "high": {"weight": 3, "color": "#ff9500", "label": "高级"},         # 深橙红色，与中级黄色更好区分
            "medium": {"weight": 2, "color": "#ffff66", "label": "中级"},       # 浅黄绿色，与高级颜色形成对比
            "low": {"weight": 1, "color": "#ccffcc", "label": "普通"}           # 浅绿色
        }
        # 大模型API配置
        self.llm_configs = {}
        # 控制是否使用大模型的配置项，默认为0（即访问大模型）
        self.use_llm_config = 0

    def show_llm_configs(self):
        """
        显示当前大模型配置信息
        """
        print(f"=== 大模型配置状态 ===")
        print(f"当前配置的大模型数量: {len(self.llm_configs)}")
        if self.llm_configs:
            for provider, config in self.llm_configs.items():
                print(f"提供商: {provider}")
                print(f"模型: {config['model']}")
                print(f"API Base URL: {config['base_url']}")
                print(f"Top_p: {config['top_p']}")
                print(f"API Key: {'*' * 20}{config['api_key'][-4:] if config['api_key'] and len(config['api_key']) >= 4 else ''}")
                print(f"---------------------")
        else:
            print("状态: 未配置任何大模型")
        print(f"=====================")

    def set_llm_config(self, provider: str, api_key: str = None, base_url: str = None, model: str = None, top_p: float = 0.7):
        """
        设置大模型API配置
        """
        import os

        if not provider:
            raise ValueError("LLM提供商不能为空")
        
        # 统一转换为小写处理
        provider_lower = provider.lower()

        # 如果没有提供api_key，尝试从环境变量获取
        if not api_key:
            env_key = f'{provider_lower.upper()}_API_KEY'
            api_key = os.getenv(env_key, '')

        # 对于需要API Key的提供商进行检查
        if provider_lower not in ['ollama'] and not api_key:
            print(f"⚠ 警告：{provider}需要API Key，但未提供")
            # 不抛出异常，只是跳过配置
            return

        # 如果没有提供base_url，尝试从环境变量获取
        if not base_url:
            env_url = f'{provider_lower.upper()}_BASE_URL'
            base_url = os.getenv(env_url) or os.getenv('LLM_BASE_URL')
        
        # 如果没有提供model，尝试从环境变量获取
        if not model:
            env_model = f'{provider_lower.upper()}_MODEL'
            model = os.getenv(env_model) or os.getenv('LLM_MODEL')

        # 设置默认值
        base_url = base_url or "https://api.openai.com/v1"
        model = model or "gpt-3.5-turbo"
        
        self.llm_configs[provider_lower] = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "top_p": top_p
        }

        # 打印大模型连接信息
        print(f"=== 大模型连接信息 ===")
        print(f"提供商: {provider}")
        print(f"模型: {model}")
        print(f"API Base URL: {base_url}")
        print(f"Top_p: {top_p}")
        print(f"API Key: {'*' * 20}{api_key[-4:] if api_key and len(api_key) >= 4 else ''}")  # 隐藏大部分API密钥
        print(f"=====================")

    async def _call_llm_api(self, provider: str, prompt: str) -> str:
        """
        调用大模型API获取建议
        """
        # 使用小写provider作为键名
        provider_lower = provider.lower()
        if provider_lower not in self.llm_configs:
            return "未配置大模型API"

        config = self.llm_configs[provider]
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }

        # 根据不同的提供商构建payload和确定API端点
        if provider.lower() in ['qwen', '通义千问', 'aliyun', 'dashscope']:
            # 阿里云通义千问API兼容模式
            payload = {
                "model": config['model'],
                "messages": [{"role": "user", "content": prompt}],
                "top_p": config.get('top_p', 0.8)
            }
            api_endpoint = f"{config['base_url']}/chat/completions"
        elif provider.lower() in ['zhipu', '智谱AI']:
            # 智谱AI API
            payload = {
                "model": config['model'],
                "messages": [{"role": "user", "content": prompt}],
                "top_p": config.get('top_p', 0.7)
            }
            api_endpoint = f"{config['base_url']}/chat/completions"
        elif provider.lower() in ['ollama']:
            # Ollama API
            payload = {
                "model": config['model'],
                "prompt": prompt,
                "stream": False
            }
            # Ollama使用不同的API端点
            api_endpoint = f"{config['base_url']}/api/generate"
            # Ollama不需要Authorization头部
            headers = {"Content-Type": "application/json"}
        else:
            # 默认为OpenAI格式
            payload = {
                "model": config['model'],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            api_endpoint = f"{config['base_url']}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_endpoint,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                # 根据不同提供商解析响应
                if provider.lower() in ['ollama']:
                    # Ollama响应格式不同
                    return result.get("response", "无法解析Ollama响应")
                else:
                    # 其他提供商使用标准格式
                    return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"调用大模型API失败: {str(e)}")
            return f"获取AI建议失败: {str(e)}"

    async def _get_ai_suggestions(self, issues: List[Dict[str, Any]]) -> List[str]:
        """
        为每个问题获取AI建议
        """
        # 如果use_llm_config为1，则直接返回"无"
        if self.use_llm_config == 1:
            return ["无" for _ in issues]

        suggestions = []

        # 根据配置选择合适的LLM提供商（使用第一个配置的提供商）
        if self.llm_configs:
            provider = next(iter(self.llm_configs.keys()))
            print(f"使用大模型提供商: {provider}")
            
            tasks = []
            for issue in issues:
                prompt = (
                    f"分析以下代码问题并提供修正建议：\n"
                    f"问题类型：{issue['type']}\n"
                    f"严重程度：{issue['severity']}\n"
                    f"问题描述：{issue['message']}\n"
                    f"解决方案：{issue['solution']}\n"
                    f"请提供一个简洁的热门原因解释和修正方案。"
                )
                task = self._call_llm_api(provider, prompt)
                tasks.append(task)

            suggestions = await asyncio.gather(*tasks)
            return suggestions
        else:
            return ["未配置大模型API" for _ in issues]

    async def _estimate_development_cost(self, total_files: int, total_lines: int) -> float:
        """
        估算开发成本（人/日）
        """
        if self.use_llm_config == 1:
            return 0.00  # 如果不使用大模型，则返回0
        
        if not self.llm_configs:
            print("未配置大模型，无法估算开发成本")
            return 0.00
        
        # 构建估算提示
        prompt = (
            f"根据以下项目信息估算其在2020年之前传统手工开发模式下的开发成本：\n"
            f"文件数量：{total_files}\n"
            f"代码行数：{total_lines}\n"
            f"请基于2020年之前没有AI辅助工具的开发效率，考虑编码、调试、测试等因素，"
            f"估算该项目所需的人力开发时间（单位：人/日），结果精确到小数点后两位，"
            f"如果估算结果大于10，则很有可能估算错误，请重新估算。"
        )
        
        # 获取估算结果
        try:
            provider = next(iter(self.llm_configs.keys()))
            result = await self._call_llm_api(provider, prompt)
            
            # 从结果中提取数字
            import re
            numbers = re.findall(r'\d+\.?\d*', result)
            if numbers:
                return round(float(numbers[0]), 2)
            else:
                # 如果AI没有返回数字，返回一个默认值
                return round((total_lines / 100) + (total_files * 0.5), 2)  # 估算公式：每100行代码需要1人日，每个文件需要0.5人日
        except Exception as e:
            print(f"估算开发成本时出错: {e}")
            # 出错时使用默认估算公式
            return round((total_lines / 100) + (total_files * 0.5), 2)

    async def _get_maintenance_recommendation(self, total_files: int, total_lines: int, 
                                       language_breakdown: dict, cost_estimate: float) -> dict:
        """
        获取维护建议
        """
        if self.use_llm_config == 1:
            return {
                "worth_maintaining": "否",
                "reasoning": "由于未启用大模型，无法进行智能分析，保守起见建议不继续维护。"
            }
        
        if not self.llm_configs:
            print("未配置大模型，无法提供维护建议")
            return {
                "worth_maintaining": "否",
                "reasoning": "由于未配置大模型，无法进行智能分析，保守起见建议不继续维护。"
            }
        
        # 构建维护建议提示
        tech_stack = ", ".join(language_breakdown.keys())
        prompt = (
            f"根据以下项目信息，分析该项目是否值得继续维护：\n"
            f"文件数量：{total_files}\n"
            f"代码行数：{total_lines}\n"
            f"技术栈：{tech_stack}\n"
            f"估算开发成本（人/日）：{cost_estimate}\n"
            f"请分析此项目是否值得继续维护，只回答'是'或'否'，并提供不超过500字的理由说明。"
            f"返回格式：\n"
            f"{{\n"
            f'  "worth_maintaining": "是" 或 "否",\n'
            f'  "reasoning": "理由说明"\n'
            f"}}"
        )
        
        try:
            provider = next(iter(self.llm_configs.keys()))
            result = await self._call_llm_api(provider, prompt)
            
            # 尝试解析返回的JSON
            import json
            try:
                parsed_result = json.loads(result)
                return {
                    "worth_maintaining": parsed_result.get("worth_maintaining", "否"),
                    "reasoning": parsed_result.get("reasoning", "无法解析AI返回的建议")
                }
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试从文本中提取信息
                lines = result.split('\n')
                worth_maintaining = "否"  # 默认值
                reasoning = "未能从AI响应中提取到明确的维护建议"
                
                for line in lines:
                    if "【此项目是否值得继续维护】" in line or "worth_maintaining" in line:
                        if "是" in line:
                            worth_maintaining = "是"
                        elif "否" in line:
                            worth_maintaining = "否"
                    elif "【原因说明】" in line or "reasoning" in line:
                        reasoning = line.replace("【原因生明】:", "").replace("reasoning:", "").strip()
                
                return {
                    "worth_maintaining": worth_maintaining,
                    "reasoning": reasoning
                }
        except Exception as e:
            print(f"获取维护建议时出错: {e}")
            return {
                "worth_maintaining": "否",
                "reasoning": f"获取AI建议时发生错误: {str(e)}"
            }

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行代码质量分析的主要方法
        
        Args:
            inputs: 输入参数字典
            
        Returns:
            包含执行结果的字典
        """
        try:
            target_path = inputs.get("target_path", "")
            language_types = inputs.get("language_types", [])
            analysis_standard = inputs.get("analysis_standard", {})
            exclude_patterns = inputs.get("exclude_patterns", [".svn", ".git", "__pycache__", "*.gitignore"])
            report_format = inputs.get("report_format", ["html", "pdf", "txt"])
            report_path = inputs.get("report_path", "./reports")
            ui_mode = inputs.get("ui_mode", False)

            # 获取大模型配置参数
            llm_provider = inputs.get("llm_provider")
            llm_api_key = inputs.get("llm_api_key")
            llm_base_url = inputs.get("llm_base_url")
            llm_model = inputs.get("llm_model")
            llm_top_p = inputs.get("llm_top_p", 0.7)  # 默认top_p值
            
            # 获取是否使用大模型的配置项
            use_llm = inputs.get("use_llm_config")
            if use_llm is not None:
                self.use_llm_config = int(use_llm)
            
            # 如果没有通过参数提供配置，尝试从环境变量获取
            import os
            if not llm_provider:
                llm_provider = os.getenv('LLM_PROVIDER') or os.getenv('DEFAULT_LLM_PROVIDER')
            if not llm_api_key:
                # 根据提供商从对应环境变量获取
                env_key = f'{llm_provider.upper()}_API_KEY' if llm_provider else 'OPENAI_API_KEY'
                llm_api_key = os.getenv(env_key) or os.getenv('LLM_API_KEY')
            if not llm_base_url:
                env_url = f'{llm_provider.upper()}_BASE_URL' if llm_provider else 'OPENAI_BASE_URL'
                llm_base_url = os.getenv(env_url) or os.getenv('LLM_BASE_URL')
            if not llm_model:
                env_model = f'{llm_provider.upper()}_MODEL' if llm_provider else 'OPENAI_MODEL'
                llm_model = os.getenv(env_model) or os.getenv('LLM_MODEL')

            # 如果提供了大模型配置，则设置
            # 特别处理Ollama这类不需要API Key的提供商
            if llm_provider and self.use_llm_config == 0:  # 只有当use_llm_config为0时才设置大模型配置
                if llm_provider.lower() == 'ollama':
                    # Ollama通常不需要API Key，所以即使没有api_key也可以设置
                    self.set_llm_config(llm_provider, llm_api_key or '', llm_base_url, llm_model, llm_top_p)
                    print(f"✓ 已配置Ollama大模型")
                else:
                    if llm_api_key:
                        # 对于其他提供商，需要API Key
                        self.set_llm_config(llm_provider, llm_api_key, llm_base_url, llm_model, llm_top_p)
                        print(f"✓ 已配置{llm_provider}大模型")
                    else:
                        print(f"⚠ 警告：{llm_provider}需要API Key，但未提供，跳过配置")

                # 打印大模型连接信息
                if llm_provider in self.llm_configs:
                    print(f"=== 大模型连接信息 ===")
                    print(f"提供商: {llm_provider}")
                    print(f"模型: {llm_model or 'default'}")
                    print(f"API Base URL: {llm_base_url or 'default'}")
                    print(f"Top_p: {llm_top_p}")
                    print(f"API Key: {'*' * 20}{llm_api_key[-4:] if llm_api_key and len(llm_api_key) >= 4 else ''}")  # 隐藏大部分API密钥
                    print(f"=====================")

            # 验证输入参数
            if not target_path or not os.path.exists(target_path):
                raise ValueError(f"目标路径不存在: {target_path}")

            # 显示当前大模型配置信息
            self.show_llm_configs()

            # 确认被测件
            file_list, detected_languages = self._identify_target_files(target_path, exclude_patterns)
            
            # 如果没有明确指定语言类型，使用检测到的语言类型
            if not language_types:
                language_types = detected_languages

            # 确认分析标准
            standards_to_use = self._confirm_analysis_standards(language_types, analysis_standard)

            print(f"\nDEBUG: 执行完成，返回结果: unknown")
            print(f"配置的大模型数量: {len(self.llm_configs)}")
            if self.llm_configs:
                print(f"已配置的大模型: {list(self.llm_configs.keys())}")
            else:
                print("警告: 没有配置任何大模型")

            # 创建临时目录存储中间结果
            with tempfile.TemporaryDirectory() as temp_dir:
                # 执行代码质量分析
                analysis_results = await self._perform_analysis(
                    file_list, 
                    standards_to_use, 
                    temp_dir
                )

                # 计算新增功能的数据
                total_files = len(analysis_results['files_analyzed'])
                total_lines = sum(stat['lines'] for stat in analysis_results['language_stats'].values())
                
                # 计算研发历史投入估算和维护建议
                cost_estimate = 0.00
                maintenance_recommendation = None
                if self.use_llm_config == 0:  # 只有在启用大模型时才进行计算
                    cost_estimate = await self._estimate_development_cost(total_files, total_lines)
                    maintenance_recommendation = await self._get_maintenance_recommendation(
                        total_files, total_lines, analysis_results["language_stats"], cost_estimate
                    )

                # 生成报告
                report_paths = self._generate_reports(
                    analysis_results, 
                    report_path, 
                    report_format, 
                    target_path,
                    cost_estimate,
                    maintenance_recommendation
                )

            # 返回结果
            summary = self._create_summary(analysis_results, file_list, target_path)
             
            return {
                "success": True,
                "report_paths": report_paths,
                "summary": summary,
                "message": "代码质量分析完成"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "代码质量分析失败"
            }

    def _identify_target_files(self, target_path: str, exclude_patterns: List[str]) -> Tuple[List[str], List[str]]:
        """
        识别目标文件并检测编程语言类型
        """
        file_list = []
        language_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php'
        }
        detected_languages = set()

        target_path_obj = Path(target_path)
        
        if target_path_obj.is_file():
            # 单个文件
            ext = target_path_obj.suffix.lower()
            if ext in language_extensions:
                detected_languages.add(language_extensions[ext])
                file_list.append(str(target_path_obj))
        else:
            # 项目目录
            for root, dirs, files in os.walk(target_path):
                # 过滤排除的目录
                dirs[:] = [d for d in dirs if not self._should_exclude(d, exclude_patterns)]
                
                for file in files:
                    if not self._should_exclude(file, exclude_patterns):
                        file_path = os.path.join(root, file)
                        ext = Path(file_path).suffix.lower()
                        
                        if ext in language_extensions:
                            detected_languages.add(language_extensions[ext])
                            file_list.append(file_path)

        return file_list, list(detected_languages)

    def _should_exclude(self, name: str, exclude_patterns: List[str]) -> bool:
        """
        检查是否应该排除某个文件或目录
        """
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    def _confirm_analysis_standards(self, language_types: List[str], custom_standards: Dict[str, str]) -> Dict[str, str]:
        """
        确认分析标准
        """
        standards_to_use = {}
        
        for lang in language_types:
            if lang in custom_standards:
                standards_to_use[lang] = custom_standards[lang]
            elif lang in self.default_standards:
                standards_to_use[lang] = self.default_standards[lang]
            else:
                # 对于未知语言，使用通用文本分析
                standards_to_use[lang] = "generic"

        return standards_to_use

    async def _perform_analysis(
        self, 
        file_list: List[str], 
        standards: Dict[str, str], 
        temp_dir: str
    ) -> Dict[str, Any]:
        """
        执行代码质量分析
        """
        analysis_results = {
            "files_analyzed": file_list,
            "issues_found": [],
            "language_stats": defaultdict(lambda: {"lines": 0, "files": 0})
        }

        # 输出待分析文件总数
        total_files = len(file_list)
        print(f"【共发现 {total_files} 个待分析的文件】")
        
        # 统计各语言代码行数
        for file_path in file_list:
            ext = Path(file_path).suffix.lower()
            lang = self._get_language_from_extension(ext)
            
            if lang:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    analysis_results["language_stats"][lang]["lines"] += lines
                    analysis_results["language_stats"][lang]["files"] += 1

        # 模拟分析过程（实际应用中这里会调用具体的分析工具）
        for i, file_path in enumerate(file_list):
            ext = Path(file_path).suffix.lower()
            lang = self._get_language_from_extension(ext)
            
            if lang in standards:
                # 这里模拟分析结果，实际应用中需要替换为真实的分析工具调用
                fake_issues = self._generate_fake_issues(file_path, lang, i)
                analysis_results["issues_found"].extend(fake_issues)

            # 显示进度
            percent_complete = (i + 1) / total_files * 100
            print(f"\r【已分析 {i + 1} 个文件】 - 进度: {percent_complete:.1f}%", end="", flush=True)

        # 在分析完成后换行，以便后续输出更整洁
        print("") 

        # 为每个问题获取AI建议
        if analysis_results["issues_found"]:
            ai_suggestions = await self._get_ai_suggestions(analysis_results["issues_found"])
            
            # 将AI建议添加到问题中
            for idx, issue in enumerate(analysis_results["issues_found"]):
                issue["ai_suggestion"] = ai_suggestions[idx] if idx < len(ai_suggestions) else "获取AI建议失败"

        return analysis_results

    def _get_language_from_extension(self, ext: str) -> str:
        """
        根据文件扩展名获取语言类型
        """
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php'
        }
        return ext_map.get(ext)

    def _generate_fake_issues(self, file_path: str, language: str, index: int) -> List[Dict[str, Any]]:
        """
        生成模拟的问题数据（实际应用中应替换为真实分析结果）
        """
        issues = []
        
        # 根据索引和语言类型生成一些模拟问题
        base_issues = [
            {
                "file": file_path,
                "line": 10 + index,
                "severity": "medium",
                "type": "potential_bug",
                "message": f"可能存在的潜在错误 ({language})",
                "solution": "仔细检查变量使用和边界条件"
            },
            {
                "file": file_path,
                "line": 25 + index,
                "severity": "low",
                "type": "style_issue",
                "message": "代码风格不符合规范",
                "solution": "遵循PEP8或其他语言特定的代码规范"
            }
        ]
        
        # 随机添加更多问题
        import random
        if random.random() > 0.5:
            base_issues.append({
                "file": file_path,
                "line": 5 + index * 2,
                "severity": "high",
                "type": "security_vulnerability",
                "message": "安全漏洞：未经验证的输入",
                "solution": "对所有用户输入进行验证和清理"
            })
        
        if index % 3 == 0:
            base_issues.append({
                "file": file_path,
                "line": 40 + index,
                "severity": "critical",
                "type": "critical_error",
                "message": "严重错误：可能导致程序崩溃",
                "solution": "检查空指针引用和资源释放"
            })
        
        return base_issues

    def _create_summary(self, analysis_results: Dict[str, Any], file_list: List[str], target_path: str) -> Dict[str, Any]:
        """
        创建分析摘要，包含目标路径信息
        """
        risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for issue in analysis_results["issues_found"]:
            severity = issue["severity"]
            if severity in risk_counts:
                risk_counts[severity] += 1

        total_lines = sum(lang_stat["lines"] for lang_stat in analysis_results["language_stats"].values())

        return {
            "target_path": target_path,  # 添加目标路径到摘要
            "total_files": len(file_list),
            "total_lines": total_lines,
            "language_breakdown": dict(analysis_results["language_stats"]),
            "risk_counts": risk_counts
        }

    def _generate_reports(self, analysis_results: Dict[str, Any], report_path: str, formats: List[str], target_path: str, cost_estimate: float = 0.00, maintenance_recommendation: dict = None) -> List[str]:
        """
        生成报告，传递目标路径信息和新增功能数据
        """
        os.makedirs(report_path, exist_ok=True)
        
        report_paths = []
        timestamp = str(int(asyncio.get_event_loop().time()))
        
        for fmt in formats:
            if fmt == "html":
                path = os.path.join(report_path, f"analysis_report_{timestamp}.html")
                self._generate_html_report(analysis_results, path, target_path, cost_estimate, maintenance_recommendation)
                report_paths.append(path)
            elif fmt == "pdf":
                path = os.path.join(report_path, f"analysis_report_{timestamp}.pdf")
                self._generate_pdf_report(analysis_results, path, target_path, cost_estimate, maintenance_recommendation)
                report_paths.append(path)
            elif fmt == "txt":
                path = os.path.join(report_path, f"analysis_report_{timestamp}.txt")
                self._generate_text_report(analysis_results, path, target_path, cost_estimate, maintenance_recommendation)
                report_paths.append(path)
        
        return report_paths

    def _generate_html_report(self, analysis_results: Dict[str, Any], output_path: str, target_path: str, cost_estimate: float = 0.00, maintenance_recommendation: dict = None):
        """
        生成HTML格式的报告，包含目标路径信息和新增功能
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('<!DOCTYPE html>\n<html>\n<head>\n')
            f.write('<meta charset="UTF-8">\n')
            f.write('<title>龙析——代码质量分析报告</title>\n')
            f.write('<style>\n')
            f.write('body { font-family: "Microsoft YaHei", Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }\n')
            f.write('.header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }\n')
            f.write('.logo { float: left; margin-top: -10px; }\n')
            f.write('.container { max-width: 1200px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }\n')
            f.write('h1 { margin: 0; font-size: 2em; }\n')
            f.write('h2 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 5px; }\n')
            f.write('table { border-collapse: collapse; width: 100%; margin: 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }\n')
            f.write('th, td { border: 1px solid #ddd; padding: 12px; text-align: left; vertical-align: top; }\n')
            f.write('th { background-color: #f2f2f2; cursor: pointer; font-weight: bold; }\n')
            f.write('th:hover { background-color: #e0e0e0; }\n')
            f.write('.critical { background-color: #ffece8; }\n')
            f.write('.high { background-color: #fef5e7; }\n')
            f.write('.medium { background-color: #fff8e1; }\n')
            f.write('.low { background-color: #f5f5f5; }\n')
            f.write('.filter-container { margin: 20px 0; }\n')
            f.write('.filter-input { margin-right: 10px; padding: 10px; width: 300px; border: 1px solid #ddd; border-radius: 4px; }\n')
            f.write('#searchInput { width: 100%; }\n')
            f.write('.summary-box { background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #667eea; }\n')
            f.write('.summary-item { margin: 5px 0; }\n')
            f.write('.section { margin: 25px 0; }\n')
            f.write('.highlight { background-color: #ffffcc; padding: 2px 4px; border-radius: 3px; }\n')
            f.write('</style>\n')
            f.write('</head>\n<body>\n')
            f.write('<div class="header">\n')
            f.write('<img src="../cdico_64_64.jpg" alt="龙析 Logo" class="logo" width="64" height="64">\n')
            f.write('<h1>龙析——代码质量分析报告</h1>\n')
            f.write('</div>\n')
            f.write('<div class="container">\n')

            # 写入摘要信息，包含目标路径
            f.write('<div class="section"><h2>📊 分析摘要</h2>\n')
            f.write('<div class="summary-box">\n')
            f.write('<div class="summary-item">📁 <strong>分析目标:</strong> {}</div>\n'.format(target_path))
            f.write('<div class="summary-item">📄 <strong>分析文件数:</strong> {}</div>\n'.format(len(analysis_results["files_analyzed"])))
            f.write('<div class="summary-item">📝 <strong>总代码行数:</strong> {}</div>\n'.format(sum(stat["lines"] for stat in analysis_results["language_stats"].values())))
            
            # 风险统计
            risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for issue in analysis_results["issues_found"]:
                risk_counts[issue["severity"]] += 1
            
            f.write('<div class="summary-item">🐉 <strong>致命风险:</strong> <span class="highlight">{}</span></div>\n'.format(risk_counts["critical"]))
            f.write('<div class="summary-item">⚠️ <strong>高级风险:</strong> <span class="highlight">{}</span></div>\n'.format(risk_counts["high"]))
            f.write('<div class="summary-item">⚡ <strong>中级风险:</strong> <span class="highlight">{}</span></div>\n'.format(risk_counts["medium"]))
            f.write('<div class="summary-item">ℹ️ <strong>普通风险:</strong> <span class="highlight">{}</span></div>\n'.format(risk_counts["low"]))
            f.write('</div></div>\n')

            # 添加研发历史投入估算（如果启用大模型）
            if self.use_llm_config == 0 and cost_estimate > 0:
                f.write('<div class="section"><h2>💰 研发历史投入估算</h2>\n')
                f.write('<div class="summary-box">\n')
                f.write('<div class="summary-item">【研发历史投入估算（不使用任何ai工具、采用较为传统的纯手工开发）：成本（人/日）】：{}</div>\n'.format(cost_estimate))
                f.write('</div></div>\n')
            
            # 添加继续维护建议（如果启用大模型）
            if self.use_llm_config == 0 and maintenance_recommendation:
                f.write('<div class="section"><h2>💡 继续维护建议</h2>\n')
                f.write('<div class="summary-box">\n')
                f.write('<div class="summary-item">【此项目是否值得继续维护】：<strong>{}</strong></div>\n'.format(maintenance_recommendation["worth_maintaining"]))
                f.write('<div class="summary-item">【原生说明】：{}</div>\n'.format(maintenance_recommendation["reasoning"]))
                f.write('</div></div>\n')

            # 语言分布
            f.write('<div class="section"><h2>🌐 语言分布</h2>\n')
            f.write('<table>\n')
            f.write('<tr><th>语言</th><th>文件数</th><th>代码行数</th><th>占比</th></tr>\n')
            
            total_lines = sum(stat["lines"] for stat in analysis_results["language_stats"].values())
            for lang, stats in analysis_results["language_stats"].items():
                percentage = (stats["lines"] / total_lines * 100) if total_lines > 0 else 0
                f.write('<tr><td>{}</td><td>{}</td><td>{}</td><td>{:.2f}%</td></tr>\n'.format(lang, stats["files"], stats["lines"], percentage))
            
            f.write('</table></div>\n')

            # 问题详情表格
            f.write('<div class="section"><h2>🔍 问题详情</h2>\n')
            f.write('<div class="filter-container">\n')
            f.write('<input type="text" id="searchInput" placeholder="🔍 输入关键字过滤问题..." class="filter-input">\n')
            f.write('</div>\n')
            f.write('<table id="issuesTable">\n')
            f.write('<thead>\n')
            f.write('<tr>\n')
            f.write('<th onclick="sortTable(0)">文件 📄</th>\n<th onclick="sortTable(1)">行号 #️⃣</th>\n<th onclick="sortTable(2)">严重程度 ⚠️</th>\n<th onclick="sortTable(3)">类型 🏷️</th>\n<th onclick="sortTable(4)">问题描述 📝</th>\n<th onclick="sortTable(5)">解决方案 💡</th>\n<th onclick="sortTable(6)">AI建议 🤖</th>\n')
            f.write('</tr>\n')
            f.write('</thead>\n')
            f.write('<tbody>\n')
            
            for issue in analysis_results["issues_found"]:
                severity_class = issue["severity"]
                severity_label = self.risk_levels[issue["severity"]]["label"]
                ai_suggestion = issue.get("ai_suggestion", "未获取到AI建议")
                f.write('<tr class="{}">\n'.format(severity_class))
                f.write('<td>{}</td>\n<td>{}</td>\n<td>{}</td>\n<td>{}</td>\n<td>{}</td>\n<td>{}</td>\n<td>{}</td>\n'.format(
                    issue["file"], issue["line"], severity_label, issue["type"], 
                    issue["message"], issue["solution"], ai_suggestion))
                f.write('</tr>\n')
            
            f.write('</tbody>\n')
            f.write('</table></div>\n')

            # 添加JavaScript功能
            f.write('<script>\n')
            f.write('''
function sortTable(columnIndex) {
    const table = document.getElementById("issuesTable");
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].innerText.trim();
        const bVal = b.cells[columnIndex].innerText.trim();
        
        // 检查是否为数字
        if (!isNaN(aVal) && !isNaN(bVal)) {
            return parseFloat(aVal) - parseFloat(bVal);
        } else {
            return aVal.localeCompare(bVal);
        }
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

document.getElementById('searchInput').addEventListener('keyup', function() {
    const searchTerm = this.value.toLowerCase();
    const rows = document.querySelectorAll('#issuesTable tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
});
</script>
''')
            f.write('</div>\n</body>\n</html>')

    def _generate_pdf_report(self, analysis_results: Dict[str, Any], output_path: str, target_path: str, cost_estimate: float = 0.00, maintenance_recommendation: dict = None):
        """
        生成PDF格式的报告，包含目标路径信息和新增功能
        """
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import platform

        # 首先尝试注册中文字体
        system = platform.system()
        font_path = ""
        font_name = "CustomChineseFont"
        
        # 增加更多字体选项以提高兼容性
        if system == "Windows":
            # 尝试多个常见的中文字体路径
            possible_paths = [
                "C:/Windows/Fonts/simsun.ttc",      # 宋体
                "C:/Windows/Fonts/simhei.ttf",      # 黑体
                "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
                "C:/Windows/Fonts/msyhbd.ttc",      # 微软雅黑粗体
                "C:/Windows/Fonts/simsunb.ttf",     # 宋体粗体
                "C:/Windows/Fonts/Arial Unicode.ttf",  # Arial Unicode
                "C:/Windows/Fonts/mingliu.ttc",     # 细明体
                "C:/Windows/Fonts/msjh.ttc"         # 微软正黑体
            ]
        elif system == "Darwin":  # macOS
            possible_paths = [
                "/System/Library/Fonts/STHeiti Light.ttc",  # 黑体-简
                "/System/Library/Fonts/STHeiti Medium.ttc", # 黑体-简
                "/System/Library/Fonts/STSong.ttc",         # 宋体-简
                "/System/Library/Fonts/PingFang.ttc",       # 苹果
                "/System/Library/Fonts/Helvetica.ttc",      # Helvetica
                "/System/Library/Fonts/Menlo.ttc",          # Menlo
                "/Library/Fonts/Songti.ttc",                # 宋体
                "/Library/Fonts/Heiti.ttc"                  # 黑体
            ]
        else:  # Linux
            possible_paths = [
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",   # 文泉驿微米黑
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",     # 文泉驿正黑
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", # Noto Sans CJK
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # DejaVu Sans
                "/usr/share/fonts/TTF/SourceHanSansCN-Regular.otf", # 思源黑体
                "/usr/share/fonts/google-noto-cjk/SourceHanSansCN-Regular.ttc", # Google Noto CJK
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", # Liberation Sans
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" # Noto Sans CJK
            ]
        
        # 尝试找到可用的字体文件
        for path in possible_paths:
            if os.path.exists(path):
                font_path = path
                break

        # 注册中文字体
        if font_path and os.path.exists(font_path):
            try:
                # 先尝试注册字体
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                
                # 验证字体是否注册成功
                registered_fonts = pdfmetrics.getRegisteredFontNames()
                if font_name in registered_fonts:
                    print(f"成功注册字体: {font_path}")
                else:
                    print(f"字体注册失败: {font_path}")
                    font_name = "Helvetica"  # 回退到默认字体
            except Exception as e:
                print(f"字体注册异常: {e}")
                font_name = "Helvetica"  # 回退到默认字体
        else:
            print(f"未找到合适的中文字体，使用默认字体")
            # 如果找不到合适的字体，使用默认字体
            font_name = "Helvetica"

        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # 自定义样式使用中文字体
        chinese_style = ParagraphStyle(
            'ChineseStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            leading=14
        )
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=20,
            spaceAfter=30,
            alignment=1,  # 居中对齐
            textColor=colors.HexColor('#667eea')
        )
        
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#764ba2'),
            borderWidth=2,
            borderColor=colors.HexColor('#667eea'),
            borderPadding=5,
            backColor=colors.lightgrey
        )
        
        story = []

        # 标题和Logo
        # 尝试多个可能的图片路径
        logo_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cdico_64_64.jpg"),  # 项目根目录
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "cdico_64_64.jpg"),      # 当前目录
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cdico_64_64.jpg"),  # 项目根目录
            "cdico_64_64.jpg"  # 当前工作目录
        ]
        
        logo_path = None
        for path in logo_paths:
            if os.path.exists(path):
                logo_path = path
                break
        
        if logo_path:
            # 创建一个包含居中图片的表格
            logo_img = Image(logo_path, width=64, height=64)
            
            # 创建一个三列的表格，图片放在中间列，实现居中
            logo_data = [['', logo_img, '']]
            # 计算左右两侧的宽度，使图片居中
            side_padding = (A4[0] - 64) / 2
            logo_table = Table(logo_data, colWidths=[side_padding * 0.5, 64, side_padding * 0.5], style=[
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # 图片列居中对齐
                ('VALIGN', (1, 0), (1, 0), 'TOP'),   # 图片顶部对齐
                ('BOX', (0, 0), (-1, -1), 0, colors.white),  # 隐藏外边框
                ('TOPPADDING', (0, 0), (-1, -1), 20),  # 上边距
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),  # 下边距
            ])
            
            story.append(logo_table)
        else:
            # 如果图片不存在，添加一点空白区域作为占位
            story.append(Spacer(1, 84))  # 64的高度加上一些间距
        
        # 添加标题
        title = Paragraph("龙析——代码质量分析报告", title_style)
        story.append(title)
        story.append(Spacer(1, 12))

        # 摘要部分
        summary_data = [
            ["<b>分析目标:</b>", Paragraph(target_path, chinese_style)],
            ["<b>分析文件数:</b>", str(len(analysis_results["files_analyzed"]))],
            ["<b>总代码行数:</b>", str(sum(stat["lines"] for stat in analysis_results["language_stats"].values()))]
        ]

        # 风险统计
        risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in analysis_results["issues_found"]:
            risk_counts[issue["severity"]] += 1

        summary_data.extend([
            ["致命风险:", str(risk_counts["critical"])],
            ["高级风险:", str(risk_counts["high"])],
            ["中级风险:", str(risk_counts["medium"])],
            ["普通风险:", str(risk_counts["low"])]
        ])
        
        # 添加摘要表格
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f2f2f2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))

        # 添加研发历史投入估算（如果启用大模型）
        if self.use_llm_config == 0 and cost_estimate > 0:
            story.append(Paragraph(f"【研发历史投入估算（不使用任何ai工具、采用较为传统的纯手工开发）：成本（人/日）】：{cost_estimate}", heading2_style))
            story.append(Paragraph("（不使用任何ai工具、采用较为传统的纯手工开发，估算可能存在偏差，请谨慎参考）", chinese_style))
            story.append(Spacer(1, 12))

        # 添加继续维护建议（如果启用大模型）
        if self.use_llm_config == 0 and maintenance_recommendation:
            story.append(Paragraph("【继续维护建议】", heading2_style))
            story.append(Paragraph(f"【此项目是否值得继续维护】：{maintenance_recommendation['worth_maintaining']}", chinese_style))
            story.append(Paragraph(f"【原因说明】：{maintenance_recommendation['reasoning']}", chinese_style))
            story.append(Spacer(1, 12))

        # 语言分布标题
        lang_title = Paragraph("语言分布", heading2_style)
        story.append(lang_title)

        total_lines = sum(stat["lines"] for stat in analysis_results["language_stats"].values())
        lang_data = [[Paragraph("<b>语言</b>", chinese_style), Paragraph("<b>文件数</b>", chinese_style), 
                     Paragraph("<b>代码行数</b>", chinese_style), Paragraph("<b>占比</b>", chinese_style)]]
        for lang, stats in analysis_results["language_stats"].items():
            percentage = (stats["lines"] / total_lines * 100) if total_lines > 0 else 0
            lang_data.append([
                Paragraph(lang, chinese_style), 
                str(stats["files"]), 
                str(stats["lines"]), 
                f"{percentage:.2f}%"
            ])

        lang_table = Table(lang_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch])
        lang_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(lang_table)
        story.append(Spacer(1, 12))

        # 问题详情标题
        issues_title = Paragraph("问题详情", heading2_style)
        story.append(issues_title)

        # 问题详情表格 - 现在包含AI建议列
        headers = [
            Paragraph("<b>文件</b>", chinese_style), 
            Paragraph("<b>行号</b>", chinese_style), 
            Paragraph("<b>严重程度</b>", chinese_style), 
            Paragraph("<b>类型</b>", chinese_style), 
            Paragraph("<b>问题描述</b>", chinese_style), 
            Paragraph("<b>解决方案</b>", chinese_style),
            Paragraph("<b>AI建议</b>", chinese_style)
        ]
        issues_data = [headers]
        
        for issue in analysis_results["issues_found"]:
            severity_label = self.risk_levels[issue["severity"]]["label"]
            # 截断过长的文本以适应PDF表格
            file_path = issue["file"][-30:] if len(issue["file"]) > 30 else issue["file"]
            message = issue["message"][:40] + "..." if len(issue["message"]) > 40 else issue["message"]
            solution = issue["solution"][:40] + "..." if len(issue["solution"]) > 40 else issue["solution"]
            ai_suggestion = issue.get("ai_suggestion", "未获取到AI建议")
            ai_suggestion_short = ai_suggestion[:40] + "..." if len(ai_suggestion) > 40 else ai_suggestion
            
            issues_data.append([
                Paragraph(file_path, chinese_style),
                str(issue["line"]),
                Paragraph(severity_label, chinese_style),
                Paragraph(issue["type"], chinese_style),
                Paragraph(message, chinese_style),
                Paragraph(solution, chinese_style),
                Paragraph(ai_suggestion_short, chinese_style)
            ])

        # 创建表格并设置样式（增加一列，调整列宽）
        issues_table = Table(issues_data, colWidths=[1.2*inch, 0.5*inch, 0.7*inch, 0.7*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        issues_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # 根据严重程度设置背景色
            *[('BACKGROUND', (0, i+1), (-1, i+1), 
               colors.HexColor('#ffece8') if analysis_results["issues_found"][i]["severity"] == "critical" else
               colors.HexColor('#fef5e7') if analysis_results["issues_found"][i]["severity"] == "high" else
               colors.HexColor('#fff8e1') if analysis_results["issues_found"][i]["severity"] == "medium" else
               colors.HexColor('#f5f5f5'))
              for i in range(min(len(analysis_results["issues_found"]), 100))]  # 限制颜色设置数量以提高性能
        ]))

        story.append(issues_table)

        # 构建PDF
        doc.build(story)

    def _generate_text_report(self, analysis_results: Dict[str, Any], output_path: str, target_path: str, cost_estimate: float = 0.00, maintenance_recommendation: dict = None):
        """
        生成文本格式的报告，包含目标路径信息和新增功能
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("==========================================\n")
            f.write("         龙析——代码质量分析报告\n")
            f.write("==========================================\n")
            f.write(f"分析目标: {target_path}\n")
            f.write(f"分析时间: {asyncio.get_event_loop().time()}\n")
            f.write(f"分析文件数: {len(analysis_results['files_analyzed'])}\n")
            f.write(f"总代码行数: {sum(stat['lines'] for stat in analysis_results['language_stats'].values())}\n\n")
            
            # 风险统计
            risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for issue in analysis_results["issues_found"]:
                risk_counts[issue["severity"]] += 1
            
            f.write("风险统计:\n")
            f.write(f"- 致命风险: {risk_counts['critical']}\n")
            f.write(f"- 高级风险: {risk_counts['high']}\n")
            f.write(f"- 中级风险: {risk_counts['medium']}\n")
            f.write(f"- 普通风险: {risk_counts['low']}\n\n")
            
            f.write("语言分布:\n")
            total_lines = sum(stat["lines"] for stat in analysis_results["language_stats"].values())
            for lang, stats in analysis_results["language_stats"].items():
                percentage = (stats["lines"] / total_lines * 100) if total_lines > 0 else 0
                f.write(f"- {lang}: {stats['files']} 文件, {stats['lines']} 行 ({percentage:.2f}%)\n")
            
            # 添加研发历史投入估算（如果启用大模型）
            if self.use_llm_config == 0 and cost_estimate > 0:
                f.write(f"\n【研发历史投入估算（不使用任何ai工具、采用较为传统的纯手工开发）：成本（人/日）】：{cost_estimate}\n")
            
            # 添加继续维护建议（如果启用大模型）
            if self.use_llm_config == 0 and maintenance_recommendation:
                f.write(f"\n【继续维护建议】\n")
                f.write(f"【此项目是否值得继续维护】：{maintenance_recommendation['worth_maintaining']}\n")
                f.write(f"【原生说明】：{maintenance_recommendation['reasoning']}\n")
            
            f.write("\n问题详情:\n")
            f.write("=" * 80 + "\n")
            for i, issue in enumerate(analysis_results["issues_found"], 1):
                severity_label = self.risk_levels[issue["severity"]]["label"]
                ai_suggestion = issue.get("ai_suggestion", "未获取到AI建议")
                f.write(f"{i}. 文件: {issue['file']} (第{issue['line']}行)\n")
                f.write(f"   严重程度: {severity_label}\n")
                f.write(f"   类型: {issue['type']}\n")
                f.write(f"   问题: {issue['message']}\n")
                f.write(f"   解决方案: {issue['solution']}\n")
                f.write(f"   AI建议: {ai_suggestion}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("报告生成完毕\n")

    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        """
        验证输入参数的有效性
        """
        required_fields = ["target_path"]
        for field in required_fields:
            if field not in inputs or not inputs[field]:
                raise ValueError(f"缺少必需参数: {field}")
        
        if not os.path.exists(inputs["target_path"]):
            raise ValueError(f"目标路径不存在: {inputs['target_path']}")
        
        return True

    def run_skill(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步执行技能的方法
        """
        return asyncio.run(self.execute(inputs))