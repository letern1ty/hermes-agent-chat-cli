"""
第六步 - 高级概念示例 3：多 Agent 协作
======================================
Multi-Agent Collaboration = 多个 specialized Agent 分工合作

核心思想：不同 Agent 负责不同领域，通过协调者整合结果

运行：python step6_multi_agent.py
"""

from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========== 模拟工具 ==========

def analyze_code(code: str) -> str:
    """代码分析"""
    return "分析结果：代码结构良好，发现 2 个潜在优化点"

def check_security(code: str) -> str:
    """安全检查"""
    return "安全扫描：发现 1 个中风险问题 - 未处理的异常"

def write_tests(spec: str) -> str:
    """生成测试"""
    return "已生成 5 个测试用例，覆盖率目标 80%"

def run_tests() -> str:
    """运行测试"""
    return "测试结果：5 passed, 0 failed"

def write_documentation(content: str) -> str:
    """编写文档"""
    return "文档已生成：API 参考 + 使用示例"

TOOLS = {
    "analyze_code": analyze_code,
    "check_security": check_security,
    "write_tests": write_tests,
    "run_tests": run_tests,
    "write_documentation": write_documentation
}

# ========== 专业 Agent 定义 ==========

class BaseAgent:
    """基础 Agent 类"""
    
    def __init__(self, name: str, role: str, expertise: str):
        self.name = name
        self.role = role
        self.expertise = expertise
        self.messages = [{
            "role": "system",
            "content": f"""你是 {name}，{role}。
专业领域：{expertise}

你的职责：
1. 专注于你的专业领域
2. 输出简洁、专业的结果
3. 必要时调用工具辅助"""
        }]
    
    def process(self, task: str, context: str = "") -> str:
        """处理任务"""
        self.messages.append({
            "role": "user",
            "content": f"{context}\n\n你的任务：{task}"
        })
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=self.messages
        )
        
        result = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": result})
        return result


class CodeReviewer(BaseAgent):
    """代码审查 Agent"""
    
    def __init__(self):
        super().__init__(
            name="CodeReviewer",
            role="资深代码审查专家",
            expertise="代码质量、性能优化、最佳实践"
        )
    
    def review(self, code: str) -> Dict:
        """审查代码"""
        analysis = TOOLS["analyze_code"](code)
        
        prompt = f"""审查以下代码：

```python
{code}
```

工具分析结果：{analysis}

请提供：
1. 代码优点
2. 需要改进的地方
3. 具体修改建议

用 JSON 格式输出：{{"strengths": [], "improvements": [], "suggestions": []}}"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)


class SecurityExpert(BaseAgent):
    """安全专家 Agent"""
    
    def __init__(self):
        super().__init__(
            name="SecurityExpert",
            role="应用安全专家",
            expertise="安全漏洞、注入攻击、认证授权"
        )
    
    def audit(self, code: str) -> Dict:
        """安全审计"""
        scan_result = TOOLS["check_security"](code)
        
        prompt = f"""对以下代码进行安全审计：

```python
{code}
```

安全扫描结果：{scan_result}

请识别：
1. 潜在安全漏洞
2. 风险等级（高/中/低）
3. 修复建议

用 JSON 格式输出：{{"vulnerabilities": [], "risk_level": "", "fixes": []}}"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)


class TestEngineer(BaseAgent):
    """测试工程师 Agent"""
    
    def __init__(self):
        super().__init__(
            name="TestEngineer",
            role="测试自动化专家",
            expertise="单元测试、集成测试、测试覆盖率"
        )
    
    def create_tests(self, feature_spec: str) -> Dict:
        """创建测试"""
        test_plan = TOOLS["write_tests"](feature_spec)
        
        prompt = f"""根据以下功能规格编写测试计划：

{feature_spec}

测试工具结果：{test_plan}

请提供：
1. 测试用例列表
2. 预期覆盖率
3. 关键测试场景

用 JSON 格式输出"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)


class Coordinator(BaseAgent):
    """协调者 Agent"""
    
    def __init__(self):
        super().__init__(
            name="Coordinator",
            role="项目协调者",
            expertise="任务分配、结果整合、进度管理"
        )
    
    def coordinate(self, task: str, agent_results: Dict) -> str:
        """整合各 Agent 的结果"""
        prompt = f"""你是项目协调者。任务：{task}

各专家的工作结果：
{json.dumps(agent_results, indent=2, ensure_ascii=False)}

请整合所有结果，生成一份完整的报告，包括：
1. 任务概述
2. 各专家的发现
3. 综合建议
4. 下一步行动

用清晰的 Markdown 格式输出。"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content


# ========== 多 Agent 协作系统 ==========

class MultiAgentSystem:
    """多 Agent 协作系统"""
    
    def __init__(self):
        self.code_reviewer = CodeReviewer()
        self.security_expert = SecurityExpert()
        self.test_engineer = TestEngineer()
        self.coordinator = Coordinator()
    
    def execute(self, task: str, code: str = "") -> str:
        """
        执行多 Agent 协作任务
        
        Args:
            task: 任务描述
            code: 待审查的代码（可选）
        """
        print(f"\n{'='*60}")
        print(f"🚀 启动多 Agent 协作")
        print(f"任务：{task}")
        print(f"{'='*60}\n")
        
        results = {}
        
        # Agent 1: 代码审查
        print("👤 CodeReviewer 开始工作...")
        if code:
            results["code_review"] = self.code_reviewer.review(code)
            print(f"   ✅ 完成：发现 {len(results['code_review']['improvements'])} 个改进点\n")
        else:
            results["code_review"] = {"note": "未提供代码"}
            print("   ⏭️  跳过：未提供代码\n")
        
        # Agent 2: 安全审计
        print("👤 SecurityExpert 开始工作...")
        if code:
            results["security_audit"] = self.security_expert.audit(code)
            print(f"   ✅ 完成：风险等级 {results['security_audit']['risk_level']}\n")
        else:
            results["security_audit"] = {"note": "未提供代码"}
            print("   ⏭️  跳过：未提供代码\n")
        
        # Agent 3: 测试计划
        print("👤 TestEngineer 开始工作...")
        results["test_plan"] = self.test_engineer.create_tests(task)
        print(f"   ✅ 完成：生成测试计划\n")
        
        # 协调者整合
        print("👤 Coordinator 整合结果...\n")
        final_report = self.coordinator.coordinate(task, results)
        
        print(final_report)
        print(f"\n{'='*60}\n")
        
        return final_report


# ========== 测试 ==========

if __name__ == "__main__":
    system = MultiAgentSystem()
    
    # 示例代码
    sample_code = '''
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    if result:
        return {"status": "success", "user": result}
    return {"status": "failed"}
'''
    
    print("\n【演示】代码审查 + 安全审计 + 测试计划")
    system.execute(
        task="审查这个登录功能的代码质量、安全性，并制定测试计划",
        code=sample_code
    )
