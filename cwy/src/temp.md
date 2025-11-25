# Cell 5: CWY 的个人知识图谱（好玩版）

```python
import networkx as nx
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建有向图
G = nx.DiGraph()

# 构建三元组 - 关于 CWY 的知识
triples = [
    # 基本信息
    ("CWY", "就读于", "苏州大学"),
    ("CWY", "年级", "研一"),
    ("CWY", "专业", "计算机"),
    
    # 学习相关
    ("CWY", "正在学习", "知识图谱"),
    ("CWY", "正在学习", "大模型"),
    ("CWY", "使用工具", "DeepKE"),
    ("CWY", "使用工具", "OneKE"),
    
    # 项目经验
    ("CWY", "跑过", "实体抽取任务"),
    ("CWY", "跑过", "关系抽取任务"),
    ("CWY", "跑过", "事件抽取任务"),
    
    # 技能
    ("CWY", "会用", "Python"),
    ("CWY", "会用", "Jupyter"),
    ("CWY", "会用", "GPU训练"),
    
    # 成就（可以自己加）
    ("CWY", "搞定了", "CUDA环境问题"),
    ("CWY", "下载了", "OneKE模型"),
    
    # 关联
    ("苏州大学", "位于", "苏州"),
    ("DeepKE", "开发者", "浙江大学"),
    ("OneKE", "基于", "LLaMA"),
]

# 定义节点类型和颜色
node_colors = {}
for head, relation, tail in triples:
    # 中心节点
    if head == "CWY":
        node_colors[head] = '#FF6B6B'  # 红色 - 主角
    # 学校相关
    elif head in ["苏州大学", "浙江大学"] or tail in ["苏州大学", "浙江大学"]:
        node_colors[head] = '#4ECDC4'  # 青色
        node_colors[tail] = '#4ECDC4'
    # 技能/工具
    elif relation in ["会用", "使用工具"]:
        node_colors[tail] = '#95E1D3'  # 浅绿
    # 学习内容
    elif relation == "正在学习":
        node_colors[tail] = '#F9CA24'  # 黄色
    # 任务
    elif relation == "跑过":
        node_colors[tail] = '#A29BFE'  # 紫色
    # 成就
    elif relation in ["搞定了", "下载了"]:
        node_colors[tail] = '#FD79A8'  # 粉色
    # 其他
    else:
        if head not in node_colors:
            node_colors[head] = '#DFE6E9'
        if tail not in node_colors:
            node_colors[tail] = '#DFE6E9'

# 添加边
for head, relation, tail in triples:
    G.add_edge(head, tail, relation=relation)

# 准备节点颜色列表（按节点顺序）
colors = [node_colors.get(node, '#DFE6E9') for node in G.nodes()]

# 计算节点大小（中心节点大一点）
sizes = [4000 if node == "CWY" else 2000 for node in G.nodes()]

# 绘图
plt.figure(figsize=(16, 12))
pos = nx.spring_layout(G, k=3, iterations=100, seed=42)  # 固定随机种子，布局更稳定

# 画节点
nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=sizes, alpha=0.9, edgecolors='black', linewidths=2)

# 画边
nx.draw_networkx_edges(G, pos, edge_color='#B2BEC3', arrows=True, 
                       arrowsize=15, width=1.5, connectionstyle='arc3,rad=0.1', 
                       alpha=0.6, arrowstyle='->')

# 画节点标签
nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold')

# 画边的标签（关系）
edge_labels = nx.get_edge_attributes(G, 'relation')
nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=7, font_color='#E74C3C', 
                             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

plt.title("CWY 的知识图谱 🎓", fontsize=20, fontweight='bold', pad=20)
plt.axis('off')
plt.tight_layout()
plt.show()

# 打印统计信息
print(f"✅ {list(G.nodes())[0]} 的知识图谱构建完成！")
print(f"\n📊 图谱统计:")
print(f"  节点数: {G.number_of_nodes()}")
print(f"  关系数: {G.number_of_edges()}")

print(f"\n🎯 关于 CWY 的所有知识:")
for head, tail, data in G.edges(data=True):
    if head == "CWY":
        print(f"  • {data['relation']}: {tail}")

print(f"\n📚 所有三元组:")
for head, tail, data in G.edges(data=True):
    print(f"  ({head}, {data['relation']}, {tail})")
```

---

## 🎨 颜色说明
- 🔴 红色：你自己（主角）
- 🔵 青色：学校
- 🟢 浅绿：技能/工具
- 🟡 黄色：学习内容
- 🟣 紫色：完成的任务
- 🌸 粉色：成就

## 💡 自定义方法
在 `triples` 列表里加你想要的：
- 兴趣爱好：`("CWY", "喜欢", "打游戏")`
- 朋友：`("CWY", "认识", "某某某")`
- 目标：`("CWY", "想去", "大厂实习")`
- 技能等级：`("Python", "掌握程度", "熟练")`
