#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OneKE 知识抽取 - 整本书细粒度分析
处理整本《非暴力沟通》PDF，提取实体和关系，构建知识图谱
"""

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import torch
from transformers import AutoConfig, AutoTokenizer, AutoModelForCausalLM
import json
import pdfplumber
from collections import defaultdict
from datetime import datetime
import logging
import pickle
import time

# ==================== 配置 ====================
PDF_PATH = "/root/projects/cwy/DeepKE/cwy/data/家庭教育-亲子关系-链接力-核心能力《非暴力.pdf"
MODEL_PATH = '/data2/models/OneKE/ZJUNLP/OneKE'
OUTPUT_DIR = "/root/projects/cwy/DeepKE/cwy/src/full_book_results"

# 处理参数
MAX_PAGES = -1         # -1 表示处理整本书所有页
MAX_CHUNKS = -1        # -1 表示处理所有段落
BATCH_SIZE = 5         # 每次合并5个段落一起处理（加速5倍）
SAVE_INTERVAL = 50     # 每50批保存一次

# Schema定义
BOOK_SCHEMA = {
    "entities": ["人物", "概念", "方法", "理论", "组织", "书籍", "情绪", "行为"],
    "relations": ["提出", "包含", "应用", "来源", "解释", "相关", "导致", "影响"]
}

# ==================== 初始化日志 ====================
os.makedirs(OUTPUT_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(OUTPUT_DIR, f"extract_{timestamp}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 加载模型 ====================
def load_model():
    """加载 OneKE 模型"""
    logger.info("="*80)
    logger.info("开始加载 OneKE 模型...")
    logger.info(f"模型路径: {MODEL_PATH}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"使用设备: {device}")
    
    config = AutoConfig.from_pretrained(MODEL_PATH, trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        config=config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True
    )
    model.eval()
    
    logger.info("✅ 模型加载完成！")
    logger.info("="*80)
    return model, tokenizer, device

# ==================== 核心函数 ====================
def extract_knowledge(model, tokenizer, device, instruction, schema, text):
    """使用 OneKE 抽取知识"""
    system = '<<SYS>>\nYou are a helpful assistant. 你是一个乐于助人的助手。\n<</SYS>>\n\n'
    prompt = '[INST] ' + system + json.dumps({
        "instruction": instruction, 
        "schema": schema, 
        "input": text
    }, ensure_ascii=False) + '[/INST]'
    
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.generate(
            input_ids=input_ids, 
            max_new_tokens=512,
            pad_token_id=tokenizer.eos_token_id
        )
    result = tokenizer.decode(output[0][input_ids.size(1):], skip_special_tokens=True)
    return result

def extract_text_from_pdf(pdf_path, max_pages=-1):
    """从 PDF 提取文本"""
    logger.info("="*80)
    logger.info(f"开始读取 PDF: {pdf_path}")
    paragraphs = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages) if max_pages == -1 else min(len(pdf.pages), max_pages)
        logger.info(f"PDF 总页数: {len(pdf.pages)}")
        logger.info(f"将处理 {total_pages} 页（整本书）..." if max_pages == -1 else f"将处理前 {total_pages} 页...")
        
        for i, page in enumerate(pdf.pages[:total_pages], 1):
            text = page.extract_text()
            if text:
                segments = [s.strip() for s in text.split('\n') if len(s.strip()) > 20]
                paragraphs.extend(segments)
                
            if i % 10 == 0:
                logger.info(f"已处理 {i}/{total_pages} 页，累计段落: {len(paragraphs)}")
                
        logger.info(f"✅ 提取完成！共 {len(paragraphs)} 个段落")
        logger.info("="*80)
    return paragraphs

def batch_extract(model, tokenizer, device, paragraphs, schema_config, max_chunks=-1):
    """批量抽取知识（使用段落合并加速）"""
    paragraphs_to_process = paragraphs if max_chunks == -1 else paragraphs[:max_chunks]
    total_batches = (len(paragraphs_to_process) + BATCH_SIZE - 1) // BATCH_SIZE
    
    results = {
        "entities": defaultdict(list),
        "relations": [],
        "metadata": {
            "start_time": datetime.now().isoformat(),
            "total_paragraphs": len(paragraphs_to_process),
            "total_batches": total_batches,
            "batch_size": BATCH_SIZE,
            "schema": schema_config
        }
    }
    
    # NER Schema
    ner_instruction = "你是命名实体识别专家。请从input中抽取出符合schema定义的实体，不存在的实体类型返回空列表。请按照JSON字符串的格式回答。"
    ner_schema = schema_config["entities"]
    
    # RE Schema
    re_instruction = "你是关系抽取专家。请从input中抽取出符合schema定义的关系三元组，不存在的关系类型返回空列表。请按照JSON字符串的格式回答。"
    re_schema = schema_config["relations"]
    
    logger.info("="*80)
    logger.info(f"开始批量抽取（共 {len(paragraphs_to_process)} 个段落，{total_batches} 批）...")
    logger.info(f"批处理大小: {BATCH_SIZE} 个段落/批（加速5倍）")
    logger.info(f"每 {SAVE_INTERVAL} 批保存一次中间结果")
    logger.info("="*80)
    
    start_time = time.time()
    success_count = 0
    error_count = 0
    
    # 批处理循环
    for batch_idx in range(0, len(paragraphs_to_process), BATCH_SIZE):
        batch_num = batch_idx // BATCH_SIZE + 1
        batch_paras = paragraphs_to_process[batch_idx : batch_idx + BATCH_SIZE]
        
        # 合并段落
        combined_text = "\n\n".join(batch_paras)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"处理第 {batch_num}/{total_batches} 批 (段落 {batch_idx+1}-{batch_idx+len(batch_paras)})")
        logger.info(f"{'='*80}")
        logger.info(f"📄 本批段落数: {len(batch_paras)}")
        logger.info(f"📄 合并文本长度: {len(combined_text)} 字符")
        logger.info(f"📄 完整文本:\n{combined_text}")
        logger.info(f"{'-'*80}")
        
        # 抽取实体
        try:
            ner_result = extract_knowledge(model, tokenizer, device, ner_instruction, ner_schema, combined_text)
            ner_data = json.loads(ner_result)
            for entity_type, entities in ner_data.items():
                results["entities"][entity_type].extend(entities)
            
            entity_count = sum(len(v) for v in ner_data.values())
            logger.info(f"✅ 实体抽取成功: 共 {entity_count} 个实体")
            logger.info(f"   完整结果:\n{ner_result}")
            success_count += 1
        except Exception as e:
            logger.error(f"⚠️ NER 失败: {e}")
            error_count += 1
        
        # 抽取关系
        try:
            re_result = extract_knowledge(model, tokenizer, device, re_instruction, re_schema, combined_text)
            re_data = json.loads(re_result)
            relation_count = 0
            for rel_type, triples in re_data.items():
                if isinstance(triples, list):
                    for triple in triples:
                        if isinstance(triple, dict) and 'subject' in triple and 'object' in triple:
                            results["relations"].append({
                                "subject": triple['subject'],
                                "relation": rel_type,
                                "object": triple['object'],
                                "source_batch": batch_num
                            })
                            relation_count += 1
            
            logger.info(f"✅ 关系抽取成功: 共 {relation_count} 个关系")
            logger.info(f"   完整结果:\n{re_result}")
        except Exception as e:
            logger.error(f"⚠️ RE 失败: {e}")
        
        # 进度统计
        elapsed = time.time() - start_time
        avg_time = elapsed / batch_num
        remaining = avg_time * (total_batches - batch_num)
        processed_paras = min(batch_idx + BATCH_SIZE, len(paragraphs_to_process))
        logger.info(f"\n📊 进度统计:")
        logger.info(f"   已处理批次: {batch_num}/{total_batches} ({batch_num/total_batches*100:.1f}%)")
        logger.info(f"   已处理段落: {processed_paras}/{len(paragraphs_to_process)}")
        logger.info(f"   成功: {success_count}, 失败: {error_count}")
        logger.info(f"   已用时: {elapsed/60:.1f} 分钟")
        logger.info(f"   预计剩余: {remaining/60:.1f} 分钟")
        logger.info(f"   预计总时间: {(elapsed + remaining)/60:.1f} 分钟")
        
        # 定期保存
        if batch_num % SAVE_INTERVAL == 0:
            checkpoint_file = os.path.join(OUTPUT_DIR, f"checkpoint_{timestamp}_batch{batch_num}.pkl")
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(results, f)
            logger.info(f"💾 中间结果已保存: {checkpoint_file}")
    
    # 去重
    logger.info("\n" + "="*80)
    logger.info("正在去重...")
    for entity_type in results["entities"]:
        results["entities"][entity_type] = list(set(results["entities"][entity_type]))
    
    # 关系去重（转换为元组去重后再转回字典）
    unique_relations = []
    seen = set()
    for rel in results["relations"]:
        key = (rel['subject'], rel['relation'], rel['object'])
        if key not in seen:
            seen.add(key)
            unique_relations.append(rel)
    results["relations"] = unique_relations
    
    results["metadata"]["end_time"] = datetime.now().isoformat()
    results["metadata"]["total_time_seconds"] = time.time() - start_time
    results["metadata"]["success_count"] = success_count
    results["metadata"]["error_count"] = error_count
    results["metadata"]["actual_batches_processed"] = batch_num
    
    logger.info("✅ 批量抽取完成！")
    logger.info(f"   处理批次: {batch_num}/{total_batches}")
    logger.info(f"   处理段落: {len(paragraphs_to_process)}")
    logger.info(f"   实体总数: {sum(len(v) for v in results['entities'].values())}")
    logger.info(f"   关系总数: {len(results['relations'])}")
    logger.info(f"   总耗时: {(time.time()-start_time)/60:.1f} 分钟")
    logger.info(f"   加速比: 约 {BATCH_SIZE}x")
    logger.info("="*80)
    
    return results

def save_results(results, timestamp):
    """保存结果"""
    logger.info("\n" + "="*80)
    logger.info("保存结果...")
    
    # 保存完整结果（pickle）
    pkl_file = os.path.join(OUTPUT_DIR, f"full_results_{timestamp}.pkl")
    with open(pkl_file, 'wb') as f:
        pickle.dump(results, f)
    logger.info(f"✅ 完整结果已保存: {pkl_file}")
    
    # 保存 JSON（可读性）
    json_file = os.path.join(OUTPUT_DIR, f"kg_result_{timestamp}.json")
    json_data = {
        "entities": dict(results["entities"]),
        "relations": results["relations"],
        "metadata": results["metadata"]
    }
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ JSON 结果已保存: {json_file}")
    
    # 保存统计报告
    report_file = os.path.join(OUTPUT_DIR, f"report_{timestamp}.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("OneKE 知识抽取报告\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"开始时间: {results['metadata']['start_time']}\n")
        f.write(f"结束时间: {results['metadata']['end_time']}\n")

        f.write(f"总耗时: {results['metadata']['total_time_seconds']/60:.1f} 分钟\n")
        f.write(f"处理模式: 批处理（{results['metadata']['batch_size']} 段/批）\n")
        f.write(f"处理段落数: {results['metadata']['total_paragraphs']}\n")
        f.write(f"处理批次数: {results['metadata']['actual_batches_processed']}/{results['metadata']['total_batches']}\n")
        f.write(f"成功: {results['metadata']['success_count']}, 失败: {results['metadata']['error_count']}\n\n")
        
        f.write("-"*80 + "\n")
        f.write("实体统计:\n")
        f.write("-"*80 + "\n")
        for entity_type, entities in sorted(results["entities"].items()):
            f.write(f"{entity_type}: {len(entities)} 个\n")
            if entities:
                f.write(f"  示例: {entities[:5]}\n")
        
        f.write("\n" + "-"*80 + "\n")
        f.write(f"关系统计: 共 {len(results['relations'])} 个三元组\n")
        f.write("-"*80 + "\n")
        if results['relations']:
            f.write("前10个关系:\n")
            for rel in results['relations'][:10]:
                f.write(f"  ({rel['subject']}) --[{rel['relation']}]--> ({rel['object']})\n")
    
    logger.info(f"✅ 统计报告已保存: {report_file}")
    logger.info("="*80)

# ==================== 主函数 ====================
def main():
    """主函数"""
    logger.info("\n" + "="*80)
    logger.info("OneKE 知识抽取 - 整本书细粒度分析")
    logger.info("="*80)
    logger.info(f"PDF 路径: {PDF_PATH}")
    logger.info(f"输出目录: {OUTPUT_DIR}")
    logger.info(f"处理页数: {'全部' if MAX_PAGES == -1 else MAX_PAGES}")
    logger.info(f"处理段落: {'全部' if MAX_CHUNKS == -1 else MAX_CHUNKS}")
    logger.info("="*80)
    
    try:
        # 1. 加载模型
        model, tokenizer, device = load_model()
        
        # 2. 提取PDF文本
        paragraphs = extract_text_from_pdf(PDF_PATH, max_pages=MAX_PAGES)
        
        # 3. 批量抽取
        results = batch_extract(model, tokenizer, device, paragraphs, BOOK_SCHEMA, max_chunks=MAX_CHUNKS)
        
        # 4. 保存结果
        save_results(results, timestamp)
        
        logger.info("\n" + "="*80)
        logger.info("🎉 全部完成！")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ 发生错误: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

