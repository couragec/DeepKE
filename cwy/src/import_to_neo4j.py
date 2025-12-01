#!/usr/bin/env python3
"""将知识图谱数据导入 Neo4j 数据库"""

import json
from neo4j import GraphDatabase

# Neo4j 连接配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"

# 数据文件路径
DATA_FILE = "/root/projects/cwy/DeepKE/cwy/src/full_book_results/kg_result_20251127_192319.json"


def import_knowledge_graph():
    """导入知识图谱到 Neo4j"""
    
    # 1. 读取数据
    print("📖 读取知识图谱数据...")
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entities = data['entities']
    relations = data['relations']
    
    print(f"   实体数: {sum(len(v) for v in entities.values())}")
    print(f"   关系数: {len(relations)}")
    
    # 2. 连接 Neo4j
    print("\n🔌 连接 Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # 3. 清空现有数据（可选）
        print("\n🗑️  清空现有数据...")
        session.run("MATCH (n) DETACH DELETE n")
        
        # 4. 创建索引（加速查询）
        print("\n📇 创建索引...")
        for entity_type in entities.keys():
            session.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{entity_type}) ON (n.name)")
        
        # 5. 导入实体节点
        print("\n📦 导入实体节点...")
        for entity_type, entity_list in entities.items():
            for entity_name in entity_list:
                session.run(
                    f"MERGE (n:{entity_type} {{name: $name}})",
                    name=entity_name
                )
            print(f"   ✓ {entity_type}: {len(entity_list)} 个")
        
        # 6. 导入关系
        print("\n🔗 导入关系...")
        relation_count = 0
        for rel in relations:
            # 关系是字典格式：{'subject': ..., 'relation': ..., 'object': ...}
            head = rel.get('subject')
            relation = rel.get('relation')
            tail = rel.get('object')
            
            if not (head and relation and tail):
                continue
            
            # 创建关系（不指定节点类型，自动匹配）
            session.run("""
                MATCH (h {name: $head})
                MATCH (t {name: $tail})
                MERGE (h)-[r:RELATION {type: $relation}]->(t)
            """, head=head, relation=relation, tail=tail)
            relation_count += 1
            
            if relation_count % 50 == 0:
                print(f"   已导入 {relation_count}/{len(relations)} 条关系...")
        
        print(f"   ✓ 完成: {relation_count} 条关系")
        
        # 7. 统计信息
        print("\n📊 数据库统计:")
        result = session.run("MATCH (n) RETURN count(n) as node_count")
        node_count = result.single()['node_count']
        
        result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
        rel_count = result.single()['rel_count']
        
        print(f"   节点总数: {node_count}")
        print(f"   关系总数: {rel_count}")
    
    driver.close()
    
    print("\n✅ 导入完成！")


if __name__ == "__main__":
    try:
        import_knowledge_graph()
    except Exception as e:
        print(f"\n❌ 错误: {e}")

