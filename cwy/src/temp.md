# PDF 长文本知识抽取 - Jupyter Notebook

## Cell 1: 安装依赖 + 加载 OneKE 模型

```python
# 安装依赖（如果没装）
# !pip install pdfplumber networkx matplotlib -q

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import torch
from transformers import AutoConfig, AutoTokenizer, AutoModelForCausalLM
import json
import pdfplumber
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 加载 OneKE 模型
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_path = '/data2/models/OneKE/ZJUNLP/OneKE'

print(f"使用设备: {device}")
print("加载 OneKE 模型...")

config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    config=config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
)
model.eval()
print("✅ 模型加载完成！")
```

---

## Cell 2: 定义核心函数

```python
# 1. OneKE 抽取函数
def extract_knowledge(instruction, schema, text):
    """使用 OneKE 抽取知识"""
    system = '<<SYS>>\nYou are a helpful assistant. 你是一个乐于助人的助手。\n<</SYS>>\n\n'
    prompt = '[INST] ' + system + json.dumps({
        "instruction": instruction, 
        "schema": schema, 
        "input": text
    }, ensure_ascii=False) + '[/INST]'
    
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(device)
    output = model.generate(
        input_ids=input_ids, 
        max_new_tokens=512,
        pad_token_id=tokenizer.eos_token_id
    )
    result = tokenizer.decode(output.sequences[0][input_ids.size(1):], skip_special_tokens=True)
    return result

# 2. PDF 提取函数
def extract_text_from_pdf(pdf_path, max_pages=10):
    """从 PDF 提取文本（默认前10页）"""
    print(f"正在读取 PDF: {pdf_path}")
    paragraphs = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = min(len(pdf.pages), max_pages)
        print(f"将处理前 {total_pages} 页...")
        
        for i, page in enumerate(pdf.pages[:total_pages]):
            text = page.extract_text()
            if text:
                # 按换行符分段，过滤短段落
                segments = [s.strip() for s in text.split('\n') if len(s.strip()) > 20]
                paragraphs.extend(segments)
                
        print(f"✅ 提取完成！共 {len(paragraphs)} 个段落")
    return paragraphs

# 3. 批量抽取函数
def batch_extract(paragraphs, schema_config, max_chunks=20):
    """批量抽取知识（默认处理前20个段落）"""
    results = {
        "entities": defaultdict(list),
        "relations": []
    }
    
    # NER Schema
    ner_instruction = "你是命名实体识别专家。请从input中抽取出符合schema定义的实体，不存在的实体类型返回空列表。请按照JSON字符串的格式回答。"
    ner_schema = schema_config["entities"]
    
    # RE Schema
    re_instruction = "你是关系抽取专家。请从input中抽取出符合schema定义的关系三元组，不存在的关系类型返回空列表。请按照JSON字符串的格式回答。"
    re_schema = schema_config["relations"]
    
    print(f"\n开始批量抽取（共 {min(len(paragraphs), max_chunks)} 个段落）...")
    
    for idx, para in enumerate(paragraphs[:max_chunks]):
        print(f"\n处理第 {idx+1}/{min(len(paragraphs), max_chunks)} 段...")
        print(f"文本预览: {para[:50]}...")
        
        # 抽取实体
        try:
            ner_result = extract_knowledge(ner_instruction, ner_schema, para)
            ner_data = json.loads(ner_result)
            for entity_type, entities in ner_data.items():
                results["entities"][entity_type].extend(entities)
            print(f"  实体: {ner_result[:100]}...")
        except Exception as e:
            print(f"  ⚠️ NER 失败: {e}")
        
        # 抽取关系
        try:
            re_result = extract_knowledge(re_instruction, re_schema, para)
            re_data = json.loads(re_result)
            for rel_type, triples in re_data.items():
                if isinstance(triples, list):
                    for triple in triples:
                        if isinstance(triple, dict) and 'subject' in triple and 'object' in triple:
                            results["relations"].append((triple['subject'], rel_type, triple['object']))
            print(f"  关系: {re_result[:100]}...")
        except Exception as e:
            print(f"  ⚠️ RE 失败: {e}")
    
    # 去重
    for entity_type in results["entities"]:
        results["entities"][entity_type] = list(set(results["entities"][entity_type]))
    results["relations"] = list(set(results["relations"]))
    
    print(f"\n✅ 批量抽取完成！")
    print(f"   实体总数: {sum(len(v) for v in results['entities'].values())}")
    print(f"   关系总数: {len(results['relations'])}")
    
    return results

print("✅ 函数定义完成！")
```

---

## Cell 3: 执行 PDF 抽取

```python
# 定义书籍通用 Schema
book_schema = {
    "entities": ["人物", "概念", "方法", "理论", "组织", "书籍"],
    "relations": ["提出", "包含", "应用", "来源", "解释", "相关"]
}

# PDF 路径
pdf_path = "/root/projects/cwy/DeepKE/cwy/data/家庭教育-亲子关系-链接力-核心能力《非暴力.pdf"

# 提取文本（前5页测试）
paragraphs = extract_text_from_pdf(pdf_path, max_pages=5)

# 批量抽取（前10段测试）
knowledge_graph = batch_extract(paragraphs, book_schema, max_chunks=10)

# 打印统计
print("\n" + "="*60)
print("📊 抽取结果统计:")
print("="*60)
for entity_type, entities in knowledge_graph["entities"].items():
    print(f"{entity_type}: {len(entities)} 个")
    if entities:
        print(f"  示例: {entities[:3]}")
print(f"\n关系三元组: {len(knowledge_graph['relations'])} 个")
if knowledge_graph['relations']:
    print("  示例:")
    for rel in knowledge_graph['relations'][:5]:
        print(f"    {rel}")
```

---

## Cell 4: 构建并可视化知识图谱

```python
# 构建知识图谱
G = nx.DiGraph()

# 添加关系边
for head, relation, tail in knowledge_graph["relations"]:
    G.add_edge(head, tail, relation=relation)

# 添加孤立实体节点
for entity_type, entities in knowledge_graph["entities"].items():
    for entity in entities:
        if entity not in G.nodes():
            G.add_node(entity, type=entity_type)

print(f"知识图谱统计:")
print(f"  节点数: {G.number_of_nodes()}")
print(f"  边数: {G.number_of_edges()}")

# 可视化
if G.number_of_nodes() > 0:
    plt.figure(figsize=(16, 12))
    
    # 布局
    pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
    
    # 节点颜色（按类型）
    node_colors = []
    color_map = {
        "人物": "red", "概念": "blue", "方法": "green",
        "理论": "orange", "组织": "purple", "书籍": "cyan"
    }
    for node in G.nodes():
        node_type = G.nodes[node].get('type', 'default')
        node_colors.append(color_map.get(node_type, 'lightgray'))
    
    # 画节点
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1000, alpha=0.9)
    
    # 画边
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, 
                          arrowsize=15, width=1.5, connectionstyle='arc3,rad=0.1')
    
    # 画标签
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold')
    
    # 画边标签
    edge_labels = nx.get_edge_attributes(G, 'relation')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=7, font_color='darkgreen')
    
    plt.title(f"📚《非暴力沟通》知识图谱（前{len(paragraphs[:10])}段）", fontsize=18, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.show()
    
    # 保存结果
    output_path = "/root/projects/cwy/DeepKE/cwy/src/kg_result.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "entities": dict(knowledge_graph["entities"]),
            "relations": knowledge_graph["relations"]
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存到: {output_path}")
else:
    print("⚠️ 未抽取到足够的知识，请检查 PDF 内容或增加处理页数")
```

---

## Cell 5: 分析和查询（可选）

```python
# 统计分析
print("="*60)
print("🔍 知识图谱深度分析")
print("="*60)

# 1. 最重要的节点（度中心性）
if G.number_of_nodes() > 0:
    degree_centrality = nx.degree_centrality(G)
    top_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\n📌 核心概念（度中心性 Top5）:")
    for node, score in top_nodes:
        print(f"  {node}: {score:.3f}")

    # 2. 子图社区
    if G.number_of_edges() > 0:
        undirected_G = G.to_undirected()
        communities = list(nx.connected_components(undirected_G))
        print(f"\n🌐 发现 {len(communities)} 个知识社区:")
        for i, community in enumerate(communities[:3]):
            print(f"  社区 {i+1}: {list(community)[:5]}")

    # 3. 简单查询
    print("\n💡 示例查询:")
    query_node = "非暴力沟通" if "非暴力沟通" in G.nodes() else list(G.nodes())[0]
    print(f"\n'{query_node}' 的相关知识:")
    
    # 出边（这个概念指向什么）
    out_edges = list(G.out_edges(query_node, data=True))
    if out_edges:
        print(f"  包含/指向:")
        for _, target, data in out_edges:
            print(f"    → {data['relation']} → {target}")
    
    # 入边（什么指向这个概念）
    in_edges = list(G.in_edges(query_node, data=True))
    if in_edges:
        print(f"  来源于:")
        for source, _, data in in_edges:
            print(f"    ← {source} ← {data['relation']}")

print("\n" + "="*60)
print("✅ 分析完成！")
```

---

## 使用说明

### 参数调整：
1. **`max_pages`**: 控制处理 PDF 页数（默认5页测试）
2. **`max_chunks`**: 控制处理段落数（默认10段测试）
3. **`book_schema`**: 自定义实体和关系类型

### 如果要处理全书：
```python
# Cell 3 中修改：
paragraphs = extract_text_from_pdf(pdf_path, max_pages=50)  # 处理50页
knowledge_graph = batch_extract(paragraphs, book_schema, max_chunks=100)  # 处理100段
```

### 如果GPU内存不足：
```python
# Cell 3 中每次只处理少量段落，分批运行
```
