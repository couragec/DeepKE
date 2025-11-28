#!/bin/bash
# OneKE 知识抽取 - 后台启动脚本

SCRIPT_DIR="/root/projects/cwy/DeepKE/cwy/src"
PYTHON="/data2/hjq/env/deepke-llm/bin/python"
LOG_DIR="${SCRIPT_DIR}/full_book_results"

# 创建输出目录
mkdir -p ${LOG_DIR}

# 生成时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
NOHUP_LOG="${LOG_DIR}/nohup_${TIMESTAMP}.log"

echo "========================================"
echo "OneKE 知识抽取 - 整本书后台启动"
echo "========================================"
echo "任务: 处理整本《非暴力沟通》PDF"
echo "脚本: ${SCRIPT_DIR}/extract_full_book.py"
echo "日志: ${NOHUP_LOG}"
echo "========================================"

# 后台运行
cd ${SCRIPT_DIR}
nohup ${PYTHON} extract_full_book.py > ${NOHUP_LOG} 2>&1 &

PID=$!
echo "✅ 已启动！进程 PID: ${PID}"
echo ""
echo "查看进度："
echo "  tail -f ${NOHUP_LOG}"
echo ""
echo "查看GPU占用："
echo "  watch -n 1 nvidia-smi"
echo ""
echo "停止进程："
echo "  kill ${PID}"
echo ""
echo "========================================"

