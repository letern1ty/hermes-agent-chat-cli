# Python 快速入门（前端工程师版）

> 用 JavaScript 类比，1 小时掌握 Python 核心语法

---

## 1. 变量和数据类型

| Python | JavaScript | 说明 |
|--------|------------|------|
| `name = "李天宇"` | `const name = "李天宇"` | 字符串 |
| `age = 28` | `const age = 28` | 数字 |
| `price = 3.14` | `const price = 3.14` | 浮点数 |
| `is_ok = True` | `const isOk = true` | 布尔值 |
| `items = [1, 2, 3]` | `const items = [1, 2, 3]` | 列表（数组） |
| `user = {"name": "李"}` | `const user = {name: "李"}` | 字典（对象） |

**关键区别**：
- Python 不用 `const/let/var`
- Python 用 `True/False`（首字母大写）
- Python 用缩进，不用 `{}`

---

## 2. 函数定义

```python
# Python
def greet(name, age=28):
    return f"你好，{name}，{age}岁"

result = greet("李天宇")
print(result)
```

```javascript
// JavaScript
const greet = (name, age = 28) => {
    return `你好，${name}，${age}岁`
}

const result = greet("李天宇")
console.log(result)
```

**关键区别**：
- Python 用 `def` 关键字
- Python 用 `self` 代替 `this`（类方法中）
- Python 用缩进，不用 `{}`

---

## 3. 条件判断

```python
# Python
age = 28
if age > 30:
    print("中年")
elif age > 20:
    print("青年")
else:
    print("少年")
```

```javascript
// JavaScript
const age = 28
if (age > 30) {
    console.log("中年")
} else if (age > 20) {
    console.log("青年")
} else {
    console.log("少年")
}
```

**关键区别**：
- Python 用 `elif` 不是 `else if`
- Python 条件后面加 `:`
- Python 用缩进，不用 `{}`

---

## 4. 循环

### for 循环

```python
# Python
for i in range(5):  # 0, 1, 2, 3, 4
    print(i)

# 遍历列表
items = ["苹果", "香蕉", "橙子"]
for item in items:
    print(item)
```

```javascript
// JavaScript
for (let i = 0; i < 5; i++) {
    console.log(i)
}

// 遍历数组
const items = ["苹果", "香蕉", "橙子"]
for (const item of items) {
    console.log(item)
}
```

### while 循环

```python
# Python
count = 0
while count < 5:
    print(count)
    count += 1
```

```javascript
// JavaScript
let count = 0
while (count < 5) {
    console.log(count)
    count++
}
```

---

## 5. 文件读写

```python
# Python - 读取文件
with open("file.txt", "r") as f:
    content = f.read()
    print(content)

# Python - 写入文件
with open("output.txt", "w") as f:
    f.write("你好，世界")
```

```javascript
// Node.js - 读取文件
const fs = require('fs')
const content = fs.readFileSync("file.txt", "utf-8")
console.log(content)

// Node.js - 写入文件
fs.writeFileSync("output.txt", "你好，世界")
```

---

## 6. 导入模块

```python
# Python - 导入整个模块
import os
os.getcwd()

# Python - 导入特定函数
from datetime import datetime
now = datetime.now()

# Python - 导入并重命名
import requests as req
req.get("https://api.github.com")
```

```javascript
// JavaScript - 导入整个模块
import * as os from 'os'

// JavaScript - 导入特定函数
import { datetime } from 'datetime'

// JavaScript - 导入并重命名
import requests as req
```

---

## 7. 类（Class）

```python
# Python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def greet(self):
        return f"你好，我是{self.name}"

p = Person("李天宇", 28)
print(p.greet())
```

```javascript
// JavaScript
class Person {
    constructor(name, age) {
        this.name = name
        this.age = age
    }
    
    greet() {
        return `你好，我是${this.name}`
    }
}

const p = new Person("李天宇", 28)
console.log(p.greet())
```

**关键区别**：
- Python 类定义后加 `:`
- Python 构造函数叫 `__init__`
- Python 用 `self` 代替 `this`

---

## 8. 异常处理

```python
# Python
try:
    result = 10 / 0
except Exception as e:
    print(f"出错了：{e}")
finally:
    print("执行完毕")
```

```javascript
// JavaScript
try {
    const result = 10 / 0
} catch (e) {
    console.log(`出错了：${e}`)
} finally {
    console.log("执行完毕")
}
```

---

## 9. 列表操作

```python
# Python
numbers = [1, 2, 3, 4, 5]

# 访问
print(numbers[0])      # 第一个：1
print(numbers[-1])     # 最后一个：5
print(numbers[1:3])    # 切片：[2, 3]

# 修改
numbers.append(6)      # 添加：[1, 2, 3, 4, 5, 6]
numbers.insert(0, 0)   # 插入：[0, 1, 2, 3, 4, 5, 6]
numbers.remove(3)      # 删除第一个 3
numbers.pop()          # 弹出最后一个

# 其他
len(numbers)           # 长度
numbers.sort()         # 排序
numbers.reverse()      # 反转
```

```javascript
// JavaScript
const numbers = [1, 2, 3, 4, 5]

// 访问
console.log(numbers[0])      // 第一个：1
console.log(numbers.at(-1))  // 最后一个：5
console.log(numbers.slice(1, 3))  // 切片：[2, 3]

// 修改
numbers.push(6)        // 添加
numbers.unshift(0)     // 插入开头
numbers.splice(numbers.indexOf(3), 1)  // 删除
numbers.pop()          // 弹出最后一个

// 其他
numbers.length         // 长度
numbers.sort()         // 排序
numbers.reverse()      // 反转
```

---

## 10. 字典操作

```python
# Python
user = {"name": "李天宇", "age": 28, "city": "北京"}

# 访问
print(user["name"])        # 李天宇
print(user.get("age"))     # 28
print(user.get("email", "未知"))  # 未知（默认值）

# 修改
user["age"] = 29           # 修改
user["email"] = "xxx@qq.com"  # 新增

# 删除
del user["city"]           # 删除
user.pop("email")          # 弹出

# 遍历
for key, value in user.items():
    print(f"{key}: {value}")

# 获取所有键/值
list(user.keys())          # ['name', 'age']
list(user.values())        # ['李天宇', 29]
```

```javascript
// JavaScript
const user = {name: "李天宇", age: 28, city: "北京"}

// 访问
console.log(user.name)         // 李天宇
console.log(user["age"])       // 28
console.log(user.email ?? "未知")  // 未知（默认值）

// 修改
user.age = 29              // 修改
user.email = "xxx@qq.com"  // 新增

// 删除
delete user.city           // 删除

// 遍历
for (const [key, value] of Object.entries(user)) {
    console.log(`${key}: ${value}`)
}

// 获取所有键/值
Object.keys(user)          // ['name', 'age', 'city']
Object.values(user)        // ['李天宇', 28, '北京']
```

---

## 11. 字符串操作

```python
# Python
text = "Hello, World!"

print(text.lower())        # "hello, world!"
print(text.upper())        # "HELLO, WORLD!"
print(text.split(", "))    # ["Hello", "World!"]
print(text.replace("World", "Python"))  # "Hello, Python!"
print(text.startswith("Hello"))  # True
print(text.endswith("!"))  # True
print(len(text))           # 13
print(text.strip())        # 去除首尾空格
print(f"姓名：{'李天宇'}")  # f-string 格式化
```

```javascript
// JavaScript
const text = "Hello, World!"

console.log(text.toLowerCase())  // "hello, world!"
console.log(text.toUpperCase())  // "HELLO, WORLD!"
console.log(text.split(", "))    // ["Hello", "World!"]
console.log(text.replace("World", "Python"))  // "Hello, Python!"
console.log(text.startsWith("Hello"))  // true
console.log(text.endsWith("!"))  // true
console.log(text.length)       // 13
console.log(text.trim())       // 去除首尾空格
console.log(`姓名：李天宇`)     // 模板字符串
```

---

## 12. 常用内置函数

| Python | JavaScript | 说明 |
|--------|------------|------|
| `print("xxx")` | `console.log("xxx")` | 输出 |
| `len(items)` | `items.length` | 长度 |
| `range(5)` | `Array(5).keys()` | 范围 |
| `str(123)` | `String(123)` | 转字符串 |
| `int("123")` | `Number("123")` | 转数字 |
| `type(x)` | `typeof x` | 类型 |
| `help(func)` | `func.toString()` | 帮助 |

---

## 13. 实战示例

### 示例 1：计算器

```python
# Python
def calculator(a, b, op="+"):
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "*":
        return a * b
    elif op == "/":
        return a / b if b != 0 else "错误：除数不能为 0"
    else:
        return "未知操作符"

print(calculator(10, 5))      # 15
print(calculator(10, 5, "*")) # 50
```

```javascript
// JavaScript
const calculator = (a, b, op = "+") => {
    if (op === "+") {
        return a + b
    } else if (op === "-") {
        return a - b
    } else if (op === "*") {
        return a * b
    } else if (op === "/") {
        return b !== 0 ? a / b : "错误：除数不能为 0"
    } else {
        return "未知操作符"
    }
}

console.log(calculator(10, 5))      // 15
console.log(calculator(10, 5, "*")) // 50
```

### 示例 2：数据处理

```python
# Python
users = [
    {"name": "张三", "age": 25},
    {"name": "李四", "age": 30},
    {"name": "王五", "age": 35}
]

# 过滤
adults = [u for u in users if u["age"] >= 30]
print(adults)  # [{'name': '李四', 'age': 30}, ...]

# 映射
names = [u["name"] for u in users]
print(names)  # ['张三', '李四', '王五']

# 排序
sorted_users = sorted(users, key=lambda u: u["age"])
print(sorted_users)  # 按年龄排序
```

```javascript
// JavaScript
const users = [
    {name: "张三", age: 25},
    {name: "李四", age: 30},
    {name: "王五", age: 35}
]

// 过滤
const adults = users.filter(u => u.age >= 30)
console.log(adults)

// 映射
const names = users.map(u => u.name)
console.log(names)

// 排序
const sortedUsers = users.sort((a, b) => a.age - b.age)
console.log(sortedUsers)
```

---

## 14. 练习文件

项目中有以下练习文件：

| 文件 | 说明 |
|------|------|
| `day1_practice.py` | Python 基础语法练习 |
| `day1_test.py` | 第一个 LLM 调用 |
| `agent.py` | 完整 Agent 项目 |

---

## 15. 下一步

完成 Python 基础后：

1. 运行 `python day1_practice.py` 熟悉语法
2. 运行 `python day1_test.py` 调用 LLM
3. 运行 `python agent.py --test` 体验完整 Agent

---

## 快速参考表

```
# 注释
print()          # 输出
input()          # 输入
len()            # 长度
range()          # 范围
str/int/float()  # 类型转换
list/dict/set()  # 数据结构
for/while        # 循环
if/elif/else     # 条件
def/class        # 函数/类
try/except       # 异常
import/from      # 导入
```

---

祝你学习顺利！有问题随时问。
