#!/usr/bin/env python3
"""
从ModelScope下载OneKE模型
目标目录: /home/wychen/llm_study/models
"""

import os
import sys
from datetime import datetime

def download_oneke():
    """下载OneKE模型从ModelScope"""
    
    # cache_dir = '/home/wychen/llm_study/models'  # 原路径
    cache_dir = '/data2/models/OneKE'  # 新路径
    
    print(f"[{datetime.now()}] 开始下载OneKE模型...")
    print(f"目标目录: {cache_dir}")
    
    try:
        from modelscope import snapshot_download
        
        # 设置下载目录
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"[{datetime.now()}] 正在从ModelScope下载模型...")
        print("模型ID: ZJUNLP/OneKE")
        print("预计大小: ~26GB")
        print("这可能需要一段时间，请耐心等待...")
        
        # 下载模型
        model_dir = snapshot_download(
            'ZJUNLP/OneKE',
            cache_dir=cache_dir,
            revision='master'
        )
        
        print(f"\n[{datetime.now()}] ✅ 下载完成!")
        print(f"模型路径: {model_dir}")
        
        return model_dir
        
    except ImportError:
        print(f"[{datetime.now()}] ❌ 错误: modelscope未安装")
        print("请先安装: pip install modelscope")
        sys.exit(1)
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ 下载失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("="*60)
    print("OneKE 模型下载脚本")
    print("="*60)
    
    model_path = download_oneke()
    
    print("\n" + "="*60)
    print("下载完成！使用方法：")
    print(f"--model_name_or_path '{model_path}'")
    print("="*60)

