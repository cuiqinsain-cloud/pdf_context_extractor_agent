#!/bin/bash
# 监控完整测试进度

LOG_FILE="/tmp/full_notes_test.log"

echo "监控福耀玻璃完整注释提取进度"
echo "================================"
echo ""

while true; do
    clear
    echo "福耀玻璃完整注释提取 - 实时进度"
    echo "================================"
    echo ""

    # 统计已处理的页数
    processed_pages=$(grep -c "开始提取第.*页的注释内容" "$LOG_FILE" 2>/dev/null || echo "0")
    echo "已处理页数: $processed_pages / 50"

    # 计算进度百分比
    if [ "$processed_pages" -gt 0 ]; then
        progress=$((processed_pages * 100 / 50))
        echo "进度: $progress%"
    fi

    # 显示最后几行日志
    echo ""
    echo "最近日志:"
    echo "--------"
    tail -10 "$LOG_FILE" 2>/dev/null | grep -E "(INFO|WARNING|ERROR|开始提取|提取结果)" || echo "等待日志..."

    echo ""
    echo "按 Ctrl+C 退出监控"

    sleep 5
done
