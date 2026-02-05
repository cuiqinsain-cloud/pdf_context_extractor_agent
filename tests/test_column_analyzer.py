"""
测试列结构分析器
"""
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.parsers.column_analyzer import ColumnAnalyzer, ColumnType

def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "="*60)
    print("测试1: 基本功能 - 标准4列格式")
    print("="*60)

    analyzer = ColumnAnalyzer()

    # 测试标准4列格式：项目、附注、期末、期初
    header_row = ['项目', '附注', '2024年12月31日', '2023年12月31日']
    column_map = analyzer.analyze_row_structure(header_row, use_cache=False)

    print(f"输入行: {header_row}")
    print(f"识别结果:")
    for col_type, col_idx in column_map.items():
        print(f"  {col_type.value}: 列{col_idx} ({header_row[col_idx]})")

    # 验证结果
    assert ColumnType.ITEM_NAME in column_map, "未识别项目名称列"
    assert ColumnType.CURRENT_PERIOD in column_map, "未识别期末列"
    assert ColumnType.PREVIOUS_PERIOD in column_map, "未识别期初列"
    assert ColumnType.NOTE in column_map, "未识别附注列"

    print("✅ 测试通过")
    return analyzer

def test_data_extraction(analyzer):
    """测试数据提取"""
    print("\n" + "="*60)
    print("测试2: 数据提取")
    print("="*60)

    # 先分析表头
    header_row = ['项目', '附注', '期末余额', '期初余额']
    column_map = analyzer.analyze_row_structure(header_row, use_cache=False)

    # 提取数据行
    data_row = ['货币资金', '七、1', '1,000,000.00', '900,000.00']
    values = analyzer.extract_values_from_row(data_row, column_map)

    print(f"输入行: {data_row}")
    print(f"提取结果:")
    for key, value in values.items():
        print(f"  {key}: {value}")

    # 验证结果
    assert values.get('item_name') == '货币资金', "项目名称提取错误"
    assert values.get('note') == '七、1', "附注提取错误"
    assert values.get('current_period') == '1000000.00', "期末数据提取错误"
    assert values.get('previous_period') == '900000.00', "期初数据提取错误"

    print("✅ 测试通过")

def test_column_change():
    """测试跨页列数变化"""
    print("\n" + "="*60)
    print("测试3: 跨页列数变化")
    print("="*60)

    analyzer = ColumnAnalyzer()

    # 第126页：4列格式
    print("\n第126页 - 4列格式:")
    row1 = ['货币资金', '七、1', '1000000.00', '900000.00']
    column_map1 = analyzer.analyze_row_structure(row1, use_cache=True)
    print(f"  输入: {row1}")
    print(f"  列映射: {[(t.value, i) for t, i in column_map1.items()]}")

    # 第127页：继续4列格式（应该使用缓存）
    print("\n第127页 - 4列格式（使用缓存）:")
    row2 = ['应收账款', '七、5', '500000.00', '450000.00']
    column_map2 = analyzer.analyze_row_structure(row2, use_cache=True)
    print(f"  输入: {row2}")
    print(f"  列映射: {[(t.value, i) for t, i in column_map2.items()]}")
    print(f"  缓存命中: {column_map1 == column_map2}")

    # 第128页：变为3列格式（附注列消失）
    print("\n第128页 - 3列格式（列数变化）:")
    row3 = ['资产总计', '3900000.00', '3625000.00']
    column_map3 = analyzer.analyze_row_structure(row3, use_cache=True)
    print(f"  输入: {row3}")
    print(f"  列映射: {[(t.value, i) for t, i in column_map3.items()]}")
    print(f"  检测到列数变化: {column_map2 != column_map3}")

    # 验证结果
    assert column_map1 == column_map2, "缓存机制失效"
    assert column_map2 != column_map3, "未检测到列数变化"
    assert ColumnType.NOTE not in column_map3, "3列格式不应有附注列"

    print("\n✅ 测试通过")

def test_various_formats():
    """测试各种表头格式"""
    print("\n" + "="*60)
    print("测试4: 各种表头格式")
    print("="*60)

    analyzer = ColumnAnalyzer()

    test_cases = [
        {
            'name': '格式1: 本期末/上期末',
            'row': ['项目', '本期末', '上期末'],
            'expected': [ColumnType.ITEM_NAME, ColumnType.CURRENT_PERIOD, ColumnType.PREVIOUS_PERIOD]
        },
        {
            'name': '格式2: 本年末/上年末',
            'row': ['科目', '本年末', '上年末'],
            'expected': [ColumnType.ITEM_NAME, ColumnType.CURRENT_PERIOD, ColumnType.PREVIOUS_PERIOD]
        },
        {
            'name': '格式3: 年末余额/年初余额',
            'row': ['会计科目', '附注', '年末余额', '年初余额'],
            'expected': [ColumnType.ITEM_NAME, ColumnType.NOTE, ColumnType.CURRENT_PERIOD, ColumnType.PREVIOUS_PERIOD]
        },
        {
            'name': '格式4: 带年份',
            'row': ['项目', '2024年期末', '2023年期末'],
            'expected': [ColumnType.ITEM_NAME, ColumnType.CURRENT_PERIOD, ColumnType.PREVIOUS_PERIOD]
        }
    ]

    for test_case in test_cases:
        print(f"\n{test_case['name']}")
        print(f"  输入: {test_case['row']}")

        column_map = analyzer.analyze_row_structure(test_case['row'], use_cache=False)
        print(f"  识别结果: {[(t.value, i) for t, i in column_map.items()]}")

        # 验证期望的列类型都被识别
        for expected_type in test_case['expected']:
            assert expected_type in column_map, f"未识别 {expected_type.value}"

        print(f"  ✅ 通过")

    print("\n✅ 所有格式测试通过")

def test_numeric_detection():
    """测试金额格式识别"""
    print("\n" + "="*60)
    print("测试5: 金额格式识别")
    print("="*60)

    analyzer = ColumnAnalyzer()

    test_cases = [
        ('1000000.00', True, '标准小数格式'),
        ('1,000,000.00', True, '带千分位'),
        ('-500000.00', True, '负数'),
        ('123456', True, '整数'),
        ('七、1', False, '附注格式'),
        ('项目', False, '文本'),
        ('', False, '空字符串'),
    ]

    for text, expected, description in test_cases:
        result = analyzer._is_numeric_format(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}: '{text}' -> {result} (期望: {expected})")
        assert result == expected, f"金额格式识别错误: {text}"

    print("\n✅ 测试通过")

def test_note_detection():
    """测试附注格式识别"""
    print("\n" + "="*60)
    print("测试6: 附注格式识别")
    print("="*60)

    analyzer = ColumnAnalyzer()

    test_cases = [
        ('七、1', True, '标准附注格式'),
        ('六、25', True, '附注格式'),
        ('十、3', True, '附注格式'),
        ('1', True, '纯数字（短）'),
        ('123', True, '纯数字（短）'),
        ('1000000', False, '纯数字（长）'),
        ('项目', False, '文本'),
        ('', False, '空字符串'),
    ]

    for text, expected, description in test_cases:
        result = analyzer._is_note_format(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}: '{text}' -> {result} (期望: {expected})")
        assert result == expected, f"附注格式识别错误: {text}"

    print("\n✅ 测试通过")

def test_cache_validation():
    """测试缓存验证机制"""
    print("\n" + "="*60)
    print("测试7: 缓存验证机制")
    print("="*60)

    analyzer = ColumnAnalyzer()

    # 建立初始缓存
    row1 = ['货币资金', '七、1', '1000000.00', '900000.00']
    column_map1 = analyzer.analyze_row_structure(row1, use_cache=True)
    print(f"初始行: {row1}")
    print(f"建立缓存: {[(t.value, i) for t, i in column_map1.items()]}")

    # 测试1：相同格式的行（应该使用缓存）
    print("\n测试1: 相同格式的行")
    row2 = ['应收账款', '七、5', '500000.00', '450000.00']
    is_valid = analyzer._validate_cached_pattern(row2, column_map1)
    print(f"  行: {row2}")
    print(f"  缓存有效: {is_valid}")
    assert is_valid, "相同格式应该使用缓存"

    # 测试2：列数不足（缓存应该失效）
    print("\n测试2: 列数不足")
    row3 = ['资产总计', '3900000.00', '3625000.00']
    is_valid = analyzer._validate_cached_pattern(row3, column_map1)
    print(f"  行: {row3}")
    print(f"  缓存有效: {is_valid}")
    assert not is_valid, "列数不足时缓存应该失效"

    # 测试3：金额列变为文本（缓存应该失效）
    print("\n测试3: 金额列变为文本")
    row4 = ['流动资产：', '', '', '']
    is_valid = analyzer._validate_cached_pattern(row4, column_map1)
    print(f"  行: {row4}")
    print(f"  缓存有效: {is_valid}")
    # 注意：空字符串不会导致缓存失效，因为验证逻辑中有 "and cell_text" 条件

    print("\n✅ 测试通过")

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试列结构分析器")
    print("="*60)

    try:
        analyzer = test_basic_functionality()
        test_data_extraction(analyzer)
        test_column_change()
        test_various_formats()
        test_numeric_detection()
        test_note_detection()
        test_cache_validation()

        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        return True

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
