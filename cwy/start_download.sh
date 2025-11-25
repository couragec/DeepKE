#!/bin/bash
# OneKE模型后台下载脚本

# 配置路径
# SCRIPT_DIR="/home/wychen/llm_study/program/DeepKE/cwy"  # 原路径
SCRIPT_DIR="/root/projects/cwy/DeepKE/cwy"  # 新路径
LOG_DIR="${SCRIPT_DIR}/log"
LOG_FILE="${LOG_DIR}/download_$(date +%Y%m%d_%H%M%S).log"

# 确保日志目录存在
mkdir -p "${LOG_DIR}"

# 激活conda环境（如果需要特定环境，取消注释下面两行）
# source ~/anaconda3/etc/profile.d/conda.sh
# conda activate deepke-llm

echo "开始后台下载OneKE模型..."
echo "日志文件: ${LOG_FILE}"

# 后台运行下载脚本，输出重定向到日志文件
nohup python "${SCRIPT_DIR}/src/download.py" > "${LOG_FILE}" 2>&1 &

# 获取进程ID
PID=$!
echo "下载进程已启动，PID: ${PID}"
echo "查看日志: tail -f ${LOG_FILE}"
echo "查看进程: ps -p ${PID}"
echo ""
echo "如需停止下载: kill ${PID}"

