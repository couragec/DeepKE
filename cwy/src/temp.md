# Neo4j 知识图谱使用指南

## ✅ 已完成的准备工作

1. **Neo4j 已启动**
   - 容器名称: `neo4j-kg`
   - Web界面: http://localhost:7474
   - 用户名: `neo4j`
   - 密码: `password123`

2. **数据已导入**
   - 节点总数: 1138
   - 关系总数: 233
   - 实体类型: 人物、概念、方法、理论、组织、书籍、情绪、行为

---

## 📦 Cell 1: 安装依赖（如果还没装）

```python
!pip install neo4j -q
```

---

## 🔌 Cell 2: 连接 Neo4j 并测试

```python
from neo4j import GraphDatabase
import pandas as pd

# 连接配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"

# 创建驱动
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 测试连接
with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as total")
    total = result.single()['total']
    print(f"✅ 连接成功！数据库中有 {total} 个节点")

driver.close()
```

---

## 📊 Cell 3: 查看数据统计

```python
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    # 统计各类型实体数量
    result = session.run("""
        MATCH (n)
        RETURN labels(n)[0] as type, count(n) as count
        ORDER BY count DESC
    """)
    
    data = [{"类型": record["type"], "数量": record["count"]} for record in result]
    df = pd.DataFrame(data)
    print("📊 实体类型统计:")
    print(df.to_string(index=False))
    
    # 统计关系数量
    result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
    rel_count = result.single()['total']
    print(f"\n🔗 关系总数: {rel_count}")

driver.close()
```

---

## 🔍 Cell 4: 查找核心概念（度数最高的节点）

```python
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    result = session.run("""
        MATCH (n)-[r]-()
        RETURN labels(n)[0] as type, n.name as name, count(r) as degree
        ORDER BY degree DESC
        LIMIT 20
    """)
    
    data = [{"类型": r["type"], "名称": r["name"], "连接数": r["degree"]} for r in result]
    df = pd.DataFrame(data)
    print("🌟 核心节点 Top 20:")
    print(df.to_string(index=False))

driver.close()
```

---

## 🔎 Cell 5: 搜索特定概念

```python
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 修改这里的搜索关键词
search_keyword = "沟通"

with driver.session() as session:
    result = session.run("""
        MATCH (n)
        WHERE n.name CONTAINS $keyword
        RETURN labels(n)[0] as type, n.name as name
        LIMIT 20
    """, keyword=search_keyword)
    
    data = [{"类型": r["type"], "名称": r["name"]} for r in result]
    df = pd.DataFrame(data)
    print(f"🔍 包含 '{search_keyword}' 的节点:")
    print(df.to_string(index=False))

driver.close()
```

---

## 🕸️ Cell 6: 查看某个节点的所有关系

```python
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 修改这里的节点名称
node_name = "非暴力沟通"

with driver.session() as session:
    result = session.run("""
        MATCH (n {name: $name})-[r]->(m)
        RETURN n.name as from, r.type as relation, m.name as to
        UNION
        MATCH (n {name: $name})<-[r]-(m)
        RETURN m.name as from, r.type as relation, n.name as to
    """, name=node_name)
    
    data = [{"起点": r["from"], "关系": r["relation"], "终点": r["to"]} for r in result]
    df = pd.DataFrame(data)
    print(f"🕸️ '{node_name}' 的所有关系:")
    print(df.to_string(index=False))

driver.close()
```

---

## 🎯 Cell 7: 查找两个概念之间的最短路径

```python
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 修改这里的起点和终点
start_node = "非暴力沟通"
end_node = "同理心"

with driver.session() as session:
    result = session.run("""
        MATCH path = shortestPath((a {name: $start})-[*..5]-(b {name: $end}))
        RETURN [node in nodes(path) | node.name] as path_nodes,
               [rel in relationships(path) | rel.type] as relations,
               length(path) as distance
        LIMIT 1
    """, start=start_node, end=end_node)
    
    record = result.single()
    if record:
        print(f"🎯 从 '{start_node}' 到 '{end_node}' 的最短路径:")
        print(f"   距离: {record['distance']} 步")
        print(f"   路径: {' -> '.join(record['path_nodes'])}")
        print(f"   关系: {' -> '.join(record['relations'])}")
    else:
        print(f"❌ 未找到从 '{start_node}' 到 '{end_node}' 的路径")

driver.close()
```

---

## 📈 Cell 8: 可视化子图（使用 NetworkX）

```python
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 选择一个核心节点及其邻居
center_node = "非暴力沟通"

with driver.session() as session:
    # 获取中心节点的1跳邻居
    result = session.run("""
        MATCH (center {name: $name})-[r]-(neighbor)
        RETURN center.name as from, r.type as relation, neighbor.name as to
        LIMIT 30
    """, name=center_node)
    
    # 构建图
    G = nx.Graph()
    for record in result:
        G.add_edge(record["from"], record["to"], relation=record["relation"])
    
    # 可视化
    plt.figure(figsize=(14, 10))
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # 画节点
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                          node_size=2000, alpha=0.9)
    
    # 画边
    nx.draw_networkx_edges(G, pos, edge_color='gray', 
                          width=2, alpha=0.6)
    
    # 画标签
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
    
    # 画边标签
    edge_labels = nx.get_edge_attributes(G, 'relation')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)
    
    plt.title(f"'{center_node}' 的关系网络", fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.show()
    
    print(f"📊 子图统计: {G.number_of_nodes()} 个节点, {G.number_of_edges()} 条边")

driver.close()
```

---

## 🌐 Cell 9: 在浏览器中查看（推荐）

```python
print("🌐 在浏览器中打开 Neo4j Browser 查看完整图谱:")
print("   URL: http://localhost:7474")
print("   用户名: neo4j")
print("   密码: password123")
print("\n💡 推荐的 Cypher 查询:")
print("   1. 查看所有节点: MATCH (n) RETURN n LIMIT 50")
print("   2. 查看概念网络: MATCH (n:概念)-[r]-(m) RETURN n,r,m LIMIT 100")
print("   3. 查看人物关系: MATCH (n:人物)-[r]-(m) RETURN n,r,m")
```

---

## 🛑 Cell 10: 停止 Neo4j 容器（用完后）

```python
import subprocess

# 停止容器
result = subprocess.run(['docker', 'stop', 'neo4j-kg'], 
                       capture_output=True, text=True)
print("🛑 Neo4j 容器已停止")

# 如果想重新启动
# subprocess.run(['docker', 'start', 'neo4j-kg'])
```

---

## 📝 常用 Cypher 查询备忘

在 Neo4j Browser (http://localhost:7474) 中可以直接运行这些查询：

```cypher
// 1. 查看数据库概览
CALL db.schema.visualization()

// 2. 查找特定类型的节点
MATCH (n:概念) RETURN n LIMIT 25

// 3. 查找包含关键词的节点
MATCH (n) WHERE n.name CONTAINS "情感" RETURN n

// 4. 查找度数最高的节点
MATCH (n)-[r]-() 
RETURN n.name, count(r) as degree 
ORDER BY degree DESC LIMIT 10

// 5. 查找两跳内的关系
MATCH path = (a {name: "非暴力沟通"})-[*..2]-(b)
RETURN path LIMIT 50

// 6. 按类型统计
MATCH (n) 
RETURN labels(n)[0] as type, count(n) as count 
ORDER BY count DESC
```

