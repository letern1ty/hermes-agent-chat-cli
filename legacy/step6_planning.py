"""
第六步 - 高级概念示例 2：规划模式
==================================
Plan-and-Execute = 先规划步骤，再逐个执行

核心思想：把复杂任务拆解成可执行的小步骤

运行：python step6_planning.py
"""

from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========== 模拟工具 ==========

def read_file(path: str) -> str:
    """读取文件"""
    files = {
        "package.json": '{"name": "my-app", "version": "1.0.0", "dependencies": {"react": "^18.0.0"}}',
        "src/App.tsx": 'import React from "react";\nexport function App() { return <div>Hello</div>; }',
        "src/utils.ts": 'export const add = (a: number, b: number) => a + b;',
        "tests/App.test.tsx": 'import { App } from "../src/App";\ntest("renders", () => {...});'
    }
    return files.get(path, f"文件内容：{path}（模拟）")

def write_file(path: str, content: str) -> str:
    """写入文件"""
    return f"✅ 已写入文件：{path} ({len(content)} 字节)"

def run_command(cmd: str) -> str:
    """运行命令"""
    results = {
        "npm test": "✓ 5 tests passed",
        "npm run build": "✓ Build completed in 3.2s",
        "npm run lint": "✗ 2 linting errors found",
        "git status": "On branch main, nothing to commit"
    }
    return results.get(cmd, f"命令输出：{cmd}（模拟）")

def list_files(dir: str) -> str:
    """列出文件"""
    dirs = {
        ".": "package.json, src/, tests/, README.md",
        "src/": "App.tsx, utils.ts, index.tsx",
        "tests/": "App.test.tsx, utils.test.ts"
    }
    return dirs.get(dir, f"文件列表：{dir}（模拟）")

TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "list_files": list_files
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取文件内容",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入文件内容",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "运行 shell 命令",
            "parameters": {
                "type": "object",
                "properties": {"cmd": {"type": "string"}},
                "required": ["cmd"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出目录中的文件",
            "parameters": {
                "type": "object",
                "properties": {"dir": {"type": "string"}},
                "required": ["dir"]
            }
        }
    }
]

# ========== 规划模式 Agent ==========

class PlanningAgent:
    """
    规划模式 Agent
    
    两阶段流程：
    1. 规划阶段：LLM 生成任务计划（步骤列表）
    2. 执行阶段：逐个执行每个步骤
    """
    
    def __init__(self):
        self.planner_messages = []
        self.executor_messages = []
    
    def plan_and_execute(self, task: str) -> Dict:
        """
        规划并执行任务
        
        Args:
            task: 用户任务描述
        
        Returns:
            执行结果
        """
        print(f"\n{'='*60}")
        print(f"任务：{task}")
        print(f"{'='*60}\n")
        
        # ========== 阶段 1：规划 ==========
        print("📋 【阶段 1】生成计划\n")
        
        plan_prompt = f"""你是一个任务规划专家。请把以下任务拆解成具体的执行步骤。

任务：{task}

要求：
1. 步骤要具体、可执行
2. 每个步骤应该足够小，可以独立完成
3. 步骤之间可能有依赖关系，按顺序排列
4. 输出 JSON 格式：{{"steps": ["步骤 1", "步骤 2", ...]}}

只输出 JSON，不要其他内容。"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": plan_prompt}],
            response_format={"type": "json_object"}
        )
        
        plan_data = json.loads(response.choices[0].message.content)
        steps = plan_data.get("steps", [])
        
        print("✅ 生成的计划：")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
        print()
        
        # ========== 阶段 2：执行 ==========
        print("🚀 【阶段 2】执行计划\n")
        
        results = []
        executor_messages = [{
            "role": "system",
            "content": "你是一个任务执行助手。根据用户的步骤描述，调用合适的工具完成。"
        }]
        
        for i, step in enumerate(steps, 1):
            print(f"--- 执行步骤 {i}/{len(steps)} ---")
            print(f"步骤：{step}\n")
            
            executor_messages.append({
                "role": "user",
                "content": f"执行这个步骤：{step}\n\n可用工具：read_file, write_file, run_command, list_files"
            })
            
            # 执行单个步骤
            step_result = self._execute_step(step, executor_messages)
            
            results.append({
                "step": step,
                "result": step_result,
                "status": "completed"
            })
            
            print(f"结果：{step_result}\n")
        
        # ========== 总结 ==========
        print("📊 【总结】\n")
        
        summary_prompt = f"""任务：{task}
计划步骤：{steps}
执行结果：{results}

请总结任务完成情况，包括：
1. 是否成功完成
2. 关键成果
3. 任何需要注意的事项

用简洁的中文回答。"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        
        summary = response.choices[0].message.content
        print(summary)
        print(f"\n{'='*60}\n")
        
        return {
            "task": task,
            "plan": steps,
            "results": results,
            "summary": summary
        }
    
    def _execute_step(self, step: str, messages: List) -> str:
        """执行单个步骤"""
        while True:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOL_DEFINITIONS
            )
            
            message = response.choices[0].message
            messages.append(message)
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    print(f"  🔧 {tool_name}({tool_args})")
                    
                    result = TOOLS[tool_name](**tool_args)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
            else:
                return message.content


# ========== 测试 ==========

if __name__ == "__main__":
    agent = PlanningAgent()
    
    # 测试 1：项目初始化
    print("\n【测试 1】初始化一个 React 项目")
    agent.plan_and_execute("帮我初始化一个 React 项目，创建基本的文件结构")
    
    # 测试 2：代码检查
    print("\n【测试 2】检查项目状态")
    agent2 = PlanningAgent()
    agent2.plan_and_execute("检查当前项目的文件结构和测试状态")
