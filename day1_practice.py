"""
Python 基础练习
"""

# 1. 变量和数据类型
name = "李天宇"
age = 28
height = 175.5
is_developer = True
skills = ["JavaScript", "React", "Vue"]
info = {"name": name, "age": age}

print("=== 变量和数据类型 ===")
print(f"姓名：{name}")
print(f"年龄：{age}")
print(f"技能：{skills}")
print(f"信息：{info}")

# 2. 函数
def greet(name, age=28):
    return f"你好，{name}，{age}岁"

print("\n=== 函数 ===")
print(greet("李天宇"))
print(greet("张三", 25))

# 3. 条件判断
print("\n=== 条件判断 ===")
if age > 30:
    print("中年")
elif age > 20:
    print("青年")
else:
    print("少年")

# 4. 循环
print("\n=== 循环 ===")
for i in range(3):
    print(f"第 {i} 次循环")

for skill in skills:
    print(f"技能：{skill}")

# 5. 列表操作
print("\n=== 列表操作 ===")
numbers = [1, 2, 3, 4, 5]
print(f"原列表：{numbers}")
print(f"第一个：{numbers[0]}")
print(f"最后一个：{numbers[-1]}")
print(f"切片 [1:3]: {numbers[1:3]}")
numbers.append(6)
print(f"添加后：{numbers}")

# 6. 字典操作
print("\n=== 字典操作 ===")
user = {"name": "李天宇", "age": 28}
print(f"姓名：{user['name']}")
print(f"键列表：{list(user.keys())}")
print(f"值列表：{list(user.values())}")

# 7. 异常处理
print("\n=== 异常处理 ===")
try:
    result = 10 / 0
except Exception as e:
    print(f"捕获异常：{e}")

print("\n=== 练习完成 ===")
