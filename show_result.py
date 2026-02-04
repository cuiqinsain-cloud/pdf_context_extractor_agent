#!/usr/bin/env python3
"""
检查金山办公测试结果的Excel文件
"""
import pandas as pd
import os

def show_test_result(file_path):
    """展示测试结果"""
    print(f"=== 合并资产负债表测试结果 ===")
    print(f"文件: {file_path}")
    print("=" * 60)

    try:
        # 读取Summary sheet
        summary_df = pd.read_excel(file_path, sheet_name='Summary')
        print("📋 提取概要信息:")
        print(f"  PDF文件: {summary_df.iloc[0]['pdf_path']}")
        print(f"  页面范围: {summary_df.iloc[0]['page_range']}")
        print(f"  提取时间: {summary_df.iloc[0]['extraction_time']}")
        print(f"  提取状态: {'✅ 成功' if summary_df.iloc[0]['success'] else '❌ 失败'}")
        print(f"  验证通过: {'✅ 是' if summary_df.iloc[0]['validation_passed'] else '❌ 否'}")
        print()

        # 读取资产负债表sheet
        df = pd.read_excel(file_path, sheet_name='资产负债表')
        print("📊 资产负债表数据结构:")
        print(f"  总行数: {len(df)}")
        print(f"  列结构: {list(df.columns)}")
        print()

        # 展示前20行数据结构
        print("🔍 前20行数据展示 (验证科目顺序):")
        display_df = df.head(20)[['部分', '类别', '项目名称', '本期末金额']].copy()
        # 格式化数值显示
        for idx, row in display_df.iterrows():
            amount = row['本期末金额']
            if pd.notna(amount) and str(amount) != 'nan':
                try:
                    amount_float = float(amount)
                    if amount_float > 0:
                        display_df.at[idx, '本期末金额'] = f"{amount_float:,.0f}"
                except:
                    pass
        print(display_df.to_string(index=False))
        print()

        # 验证负债和所有者权益总计
        print("🎯 关键验证 - 负债和所有者权益总计:")
        total_rows = df[df['项目名称'].str.contains('负债和所有者权益.*总计', na=False, regex=True)]
        if len(total_rows) > 0:
            for _, row in total_rows.iterrows():
                current = float(row['本期末金额']) if pd.notna(row['本期末金额']) else 0
                previous = float(row['上期末金额']) if pd.notna(row['上期末金额']) else 0
                print(f"  ✅ 项目名称: {row['项目名称']}")
                print(f"  💰 本期末金额: {current:,.0f} 元")
                print(f"  💰 上期末金额: {previous:,.0f} 元")
        else:
            print("  ❌ 未找到负债和所有者权益总计")
        print()

        # 统计各部分数据
        print("📈 数据统计:")
        sections = df['部分'].value_counts()
        categories = df['类别'].value_counts()
        has_amount = len(df[pd.notna(df['本期末金额']) & (df['本期末金额'] != '')])

        print(f"  主要部分: {dict(sections)}")
        print(f"  主要类别: {dict(categories)}")
        print(f"  有数值项目: {has_amount}个")
        print()

        # 展示资产总计和负债权益总计，验证平衡性
        print("⚖️  平衡性验证:")
        assets_total = df[df['项目名称'].str.contains('资产总计', na=False)]
        liab_equity_total = df[df['项目名称'].str.contains('负债和所有者权益.*总计', na=False, regex=True)]

        if len(assets_total) > 0 and len(liab_equity_total) > 0:
            assets_amount = float(assets_total.iloc[0]['本期末金额'])
            liab_equity_amount = float(liab_equity_total.iloc[0]['本期末金额'])

            print(f"  📊 资产总计: {assets_amount:,.0f} 元")
            print(f"  📊 负债和权益总计: {liab_equity_amount:,.0f} 元")

            if abs(assets_amount - liab_equity_amount) < 1:
                print(f"  ✅ 平衡检查: 通过 (差额: {abs(assets_amount - liab_equity_amount):.2f})")
            else:
                print(f"  ⚠️  平衡检查: 存在差额 {abs(assets_amount - liab_equity_amount):,.2f}")
        else:
            print("  ❌ 无法进行平衡性验证")

    except Exception as e:
        print(f"❌ 读取Excel文件时出错: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "output/海尔智家_合并资产负债表.xlsx"

    if os.path.exists(file_path):
        show_test_result(file_path)
    else:
        print(f"❌ 文件不存在: {file_path}")