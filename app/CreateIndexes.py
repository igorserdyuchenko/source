from neo4j import GraphDatabase
import time

# Neo4j connection details
NEO4J_URI = "neo4j://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password"

driver = GraphDatabase.driver(NEO4J_URI, auth=(USERNAME, PASSWORD))


def create_indexes():
    """
    Creates all necessary indexes for optimal query performance.
    Uses composite indexes with prefix matching to minimize total index count.
    """

    indexes = {
        # ============================================
        # SYMBOL NODE INDEXES (4 total)
        # ============================================
        "idx_symbol_calls_lookup": """
            CREATE INDEX idx_symbol_calls_lookup IF NOT EXISTS
            FOR (s:Symbol) ON (s.repository_url, s.type, s.fq_name)
        """,

        "idx_symbol_type_lookup": """
            CREATE INDEX idx_symbol_type_lookup IF NOT EXISTS
            FOR (s:Symbol) ON (s.repository_url, s.type, s.fq_name, s.file_path)
        """,

        "idx_symbol_file_path": """
            CREATE INDEX idx_symbol_file_path IF NOT EXISTS
            FOR (s:Symbol) ON (s.repository_url, s.file_path)
        """,

        "idx_symbol_namespace": """
            CREATE INDEX idx_symbol_namespace IF NOT EXISTS
            FOR (s:Symbol) ON (s.namespace)
        """,

        # ============================================
        # NAMESPACE NODE INDEXES
        # ============================================
        "idx_namespace_repo_name": """
            CREATE INDEX idx_namespace_repo_name IF NOT EXISTS
            FOR (n:Namespace) ON (n.repository_url, n.name)
        """,

        # ============================================
        # FILE NODE INDEXES
        # ============================================
        "idx_file_repo_path": """
            CREATE INDEX idx_file_repo_path IF NOT EXISTS
            FOR (f:File) ON (f.repository_url, f.path)
        """,

        # ============================================
        # REPOSITORY NODE INDEXES
        # ============================================
        "idx_repository_url": """
            CREATE INDEX idx_repository_url IF NOT EXISTS
            FOR (r:Repository) ON (r.url)
        """
    }

    print("Creating indexes for optimal query performance...\n")

    with driver.session() as session:
        for index_name, index_query in indexes.items():
            try:
                start_time = time.perf_counter()
                session.run(index_query)
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                print(f"✓ Created {index_name} ({execution_time:.3f}s)")
            except Exception as e:
                print(f"✗ Failed to create {index_name}: {str(e)}")

    print("\n" + "="*60)
    print("Verifying created indexes...")
    print("="*60 + "\n")

    # Show all indexes
    with driver.session() as session:
        result = session.run("SHOW INDEXES")
        for record in result:
            print(f"Index: {record['name']}")
            print(f"  Type: {record['type']}")
            print(f"  Labels: {record.get('labelsOrTypes', 'N/A')}")
            print(f"  Properties: {record.get('properties', 'N/A')}")
            print(f"  State: {record['state']}")
            print()


if __name__ == "__main__":
    try:
        create_indexes()
        print("✓ Index creation completed successfully!")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    finally:
        driver.close()
