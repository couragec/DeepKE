## 11.25

DeepKE-cnSchema
/root/projects/cwy/DeepKE/example/triple/cnschema/


conda环境补：
1.modelscope的 下模型
2.ipynb的
pip install jupyter ipykernel && python -m ipykernel install --user --name deepke-llm --display-name "DeepKE-LLM"
pip install matplotlib networkx
# 安装中文字体包
sudo apt-get install -y fonts-wqy-zenhei fonts-wqy-microhei
# 清除matplotlib字体缓存
rm -rf ~/.cache/matplotlib


## 环境问题修复记录
### 问题：CUDA 12.4 与原始环境不兼容
- 原始环境：torch 2.0.0 + transformers 4.33.0 + bitsandbytes 0.39.1
- bitsandbytes 0.39.1 只支持 CUDA 11.x，不支持 CUDA 12.4
- transformers 4.33.0 强制依赖 bitsandbytes

### 解决方案（已验证可用）
```bash
conda activate deepke-llm

# 1. 升级 PyTorch 到 2.1.0（支持 CUDA 12.x）
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu121

# 2. 升级 transformers（不强制依赖 bitsandbytes）
pip install transformers==4.35.0

# 3. 升级 accelerate
pip install accelerate==0.24.0
```

### 最终环境版本
- torch: 2.1.0
- transformers: 4.35.0
- accelerate: 0.24.0
- Python: 3.9
- CUDA: 12.4


## 11.24
1.安装环境
他有两个版本 大模型/bert模型

# 1. 创建环境
conda create -n deepke-llm python=3.9 -y
# 2. 激活环境
conda activate deepke-llm
# 3. 进入LLM目录
cd /home/wychen/llm_study/program/DeepKE/example/llm
or
cd /root/projects/cwy/DeepKE/example/llm
# 4. 安装依赖（自动安装正确版本）
pip install -r requirements.txt
# 5. 验证
python -c "import torch; print('安装成功')"


2.学习
/home/wychen/llm_study/program/DeepKE/example/llm/InstructKGC/data
这个下面有具体数据