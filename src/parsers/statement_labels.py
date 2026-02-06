"""
财务报表科目标准名称映射
将解析器内部的英文键名映射为标准的中文财务科目名称
"""

# 资产负债表科目映射
BALANCE_SHEET_LABELS = {
    # 流动资产
    'cash': '货币资金',
    'trading_financial_assets': '交易性金融资产',
    'derivative_financial_assets': '衍生金融资产',
    'notes_receivable': '应收票据',
    'accounts_receivable': '应收账款',
    'receivables_financing': '应收款项融资',
    'prepayments': '预付款项',
    'other_receivables': '其他应收款',
    'inventory': '存货',
    'contract_assets': '合同资产',
    'held_for_sale_assets': '持有待售资产',
    'non_current_assets_due_within_one_year': '一年内到期的非流动资产',
    'other_current_assets': '其他流动资产',
    'current_assets_total': '流动资产合计',

    # 非流动资产
    'debt_investments': '债权投资',
    'other_debt_investments': '其他债权投资',
    'long_term_receivables': '长期应收款',
    'long_term_equity_investments': '长期股权投资',
    'other_equity_instruments': '其他权益工具投资',
    'other_non_current_financial_assets': '其他非流动金融资产',
    'investment_property': '投资性房地产',
    'fixed_assets': '固定资产',
    'construction_in_progress': '在建工程',
    'productive_biological_assets': '生产性生物资产',
    'oil_and_gas_assets': '油气资产',
    'right_of_use_assets': '使用权资产',
    'intangible_assets': '无形资产',
    'development_expenditure': '开发支出',
    'goodwill': '商誉',
    'long_term_prepaid_expenses': '长期待摊费用',
    'deferred_tax_assets': '递延所得税资产',
    'other_non_current_assets': '其他非流动资产',
    'non_current_assets_total': '非流动资产合计',
    'assets_total': '资产总计',

    # 流动负债
    'short_term_borrowings': '短期借款',
    'trading_financial_liabilities': '交易性金融负债',
    'derivative_financial_liabilities': '衍生金融负债',
    'notes_payable': '应付票据',
    'accounts_payable': '应付账款',
    'advance_receipts': '预收款项',
    'contract_liabilities': '合同负债',
    'employee_benefits_payable': '应付职工薪酬',
    'taxes_payable': '应交税费',
    'other_payables': '其他应付款',
    'held_for_sale_liabilities': '持有待售负债',
    'non_current_liabilities_due_within_one_year': '一年内到期的非流动负债',
    'other_current_liabilities': '其他流动负债',
    'current_liabilities_total': '流动负债合计',

    # 非流动负债
    'long_term_borrowings': '长期借款',
    'bonds_payable': '应付债券',
    'lease_liabilities': '租赁负债',
    'long_term_payables': '长期应付款',
    'long_term_employee_benefits_payable': '长期应付职工薪酬',
    'provisions': '预计负债',
    'deferred_income': '递延收益',
    'deferred_tax_liabilities': '递延所得税负债',
    'other_non_current_liabilities': '其他非流动负债',
    'non_current_liabilities_total': '非流动负债合计',
    'liabilities_total': '负债合计',

    # 所有者权益
    'share_capital': '股本',
    'other_equity_instruments_equity': '其他权益工具',
    'capital_reserve': '资本公积',
    'treasury_stock': '减：库存股',
    'other_comprehensive_income': '其他综合收益',
    'special_reserve': '专项储备',
    'surplus_reserve': '盈余公积',
    'retained_earnings': '未分配利润',
    'parent_equity_total': '归属于母公司所有者权益合计',
    'minority_interests': '少数股东权益',
    'equity_total': '所有者权益合计',
    'total_liabilities_and_equity': '负债和所有者权益总计',
}

# 利润表科目映射
INCOME_STATEMENT_LABELS = {
    # 营业收入
    'operating_revenue': '营业收入',
    'operating_total_revenue': '营业总收入',

    # 营业成本
    'operating_cost': '营业成本',
    'taxes_and_surcharges': '税金及附加',
    'selling_expenses': '销售费用',
    'administrative_expenses': '管理费用',
    'rd_expenses': '研发费用',
    'financial_expenses': '财务费用',
    'operating_total_cost': '营业总成本',

    # 其他损益
    'other_income': '其他收益',
    'investment_income': '投资收益',
    'fair_value_change': '公允价值变动收益',
    'credit_impairment': '信用减值损失',
    'asset_impairment': '资产减值损失',
    'asset_disposal': '资产处置收益',

    # 利润
    'operating_profit': '营业利润',
    'non_operating_income': '营业外收入',
    'non_operating_expenses': '营业外支出',
    'total_profit': '利润总额',
    'income_tax': '所得税费用',
    'net_profit': '净利润',
    'continuing_operations_profit': '持续经营净利润',
    'discontinued_operations_profit': '终止经营净利润',
    'parent_net_profit': '归属于母公司所有者的净利润',
    'minority_profit': '少数股东损益',

    # 综合收益
    'other_comprehensive_income': '其他综合收益的税后净额',
    'total_comprehensive_income': '综合收益总额',
    'parent_comprehensive_income': '归属于母公司所有者的综合收益总额',
    'minority_comprehensive_income': '归属于少数股东的综合收益总额',

    # 每股收益
    'basic_eps': '基本每股收益（元/股）',
    'diluted_eps': '稀释每股收益（元/股）',
}

# 现金流量表科目映射
CASH_FLOW_LABELS = {
    # 经营活动
    'sales_goods_cash': '销售商品、提供劳务收到的现金',
    'tax_refund': '收到的税费返还',
    'other_operating_inflow': '收到其他与经营活动有关的现金',
    'operating_inflow_subtotal': '经营活动现金流入小计',
    'purchase_goods_cash': '购买商品、接受劳务支付的现金',
    'employee_cash': '支付给职工以及为职工支付的现金',
    'tax_payment': '支付的各项税费',
    'other_operating_outflow': '支付其他与经营活动有关的现金',
    'operating_outflow_subtotal': '经营活动现金流出小计',
    'operating_net_cash_flow': '经营活动产生的现金流量净额',

    # 投资活动
    'investment_recovery': '收回投资收到的现金',
    'investment_income': '取得投资收益收到的现金',
    'disposal_assets_cash': '处置固定资产、无形资产和其他长期资产收回的现金净额',
    'disposal_subsidiary_cash': '处置子公司及其他营业单位收到的现金净额',
    'other_investing_inflow': '收到其他与投资活动有关的现金',
    'investing_inflow_subtotal': '投资活动现金流入小计',
    'purchase_assets_cash': '购建固定资产、无形资产和其他长期资产支付的现金',
    'investment_payment': '投资支付的现金',
    'acquire_subsidiary_cash': '取得子公司及其他营业单位支付的现金净额',
    'other_investing_outflow': '支付其他与投资活动有关的现金',
    'investing_outflow_subtotal': '投资活动现金流出小计',
    'investing_net_cash_flow': '投资活动产生的现金流量净额',

    # 筹资活动
    'investment_received': '吸收投资收到的现金',
    'minority_investment': '其中：子公司吸收少数股东投资收到的现金',
    'borrowing_received': '取得借款收到的现金',
    'other_financing_inflow': '收到其他与筹资活动有关的现金',
    'financing_inflow_subtotal': '筹资活动现金流入小计',
    'debt_repayment': '偿还债务支付的现金',
    'dividend_interest_payment': '分配股利、利润或偿付利息支付的现金',
    'minority_dividend': '其中：子公司支付给少数股东的股利、利润',
    'other_financing_outflow': '支付其他与筹资活动有关的现金',
    'financing_outflow_subtotal': '筹资活动现金流出小计',
    'financing_net_cash_flow': '筹资活动产生的现金流量净额',

    # 其他项目
    'exchange_rate_effect': '汇率变动对现金及现金等价物的影响',
    'net_increase_cash': '现金及现金等价物净增加额',
    'beginning_cash_balance': '期初现金及现金等价物余额',
    'ending_cash_balance': '期末现金及现金等价物余额',
}


def get_label(key: str, statement_type: str) -> str:
    """
    获取财务科目的标准中文名称

    Args:
        key: 英文键名
        statement_type: 报表类型 ('balance_sheet', 'income_statement', 'cash_flow')

    Returns:
        str: 标准中文名称，如果找不到则返回原键名
    """
    if statement_type == 'balance_sheet':
        return BALANCE_SHEET_LABELS.get(key, key)
    elif statement_type == 'income_statement':
        return INCOME_STATEMENT_LABELS.get(key, key)
    elif statement_type == 'cash_flow':
        return CASH_FLOW_LABELS.get(key, key)
    else:
        return key
