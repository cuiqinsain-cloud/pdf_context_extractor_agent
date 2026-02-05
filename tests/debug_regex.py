import re

# 测试正则表达式
test_text = "2024年12月31日"

patterns = [
    r'期末',
    r'本期末',
    r'本年末',
    r'本期',
    r'2024年.*期末',
    r'2024年.*12月.*31日',
    r'当期',
    r'本年'
]

print(f"测试文本: '{test_text}'")
print("\n匹配结果:")
for pattern in patterns:
    match = re.search(pattern, test_text)
    print(f"  {pattern:30s} -> {bool(match)} {f'({match.group()})' if match else ''}")
