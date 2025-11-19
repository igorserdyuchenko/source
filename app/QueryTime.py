from neo4j import GraphDatabase
import time

# Neo4j connection details
NEO4J_URI = "neo4j://localhost:7687"  # Change to your Neo4j URI
USERNAME = "neo4j"  # Your username
PASSWORD = "password"  # Your password

driver = GraphDatabase.driver(NEO4J_URI, auth=(USERNAME, PASSWORD))


def run_query_with_timing(query, parameters=None):
    """
    Executes a Cypher query, measures execution time, and returns number of relationships created.
    :param query: Cypher query string
    :param parameters: Dictionary of query parameters (optional)
    :return: (execution_time, relationships_created)
    """
    with driver.session() as session:
        start_time = time.perf_counter()
        summary = session.run(query, parameters or {}).consume()  # Consume to get summary
        end_time = time.perf_counter()
        execution_time = end_time - start_time

        # Get number of relationships created from query statistics
        relationships_created = summary.counters.relationships_created

        return execution_time, relationships_created


# Example usage
queries = {
    "DEFINED_IN_NAMESPACE": """                 CALL (){
                                                    MATCH (m:Symbol {repository_url: "https://github.com/igorserdyuchenko/source.git"})
                                                    MATCH (t:Namespace {repository_url: "https://github.com/igorserdyuchenko/source.git"})
                                                    WHERE m.namespace = t.name
                                                      AND m.type IN ['TYPE', 'METHOD']
                                                    MERGE (m)-[:DEFINED_IN_NAMESPACE_TEST]->(t)
                                                    } IN TRANSACTIONS OF 1000 ROWS""",
    "DEFINED_IN_TYPE": """
                                            CALL (){
                                                MATCH (m:Symbol {repository_url: "https://github.com/igorserdyuchenko/source.git", type: 'METHOD'})
                                                WHERE m.defined_in_type IS NOT NULL
                                                WITH apoc.convert.fromJsonList(m.defined_in_type) AS typeNameList, m
                                                UNWIND typeNameList AS typeName
                                                MATCH (t:Symbol {repository_url: "https://github.com/igorserdyuchenko/source.git", type: 'TYPE', fq_name: typeName, file_path: m.file_path})
                                                MERGE (m)-[:DEFINED_IN_TYPE_TEST]->(t)
                                                } IN TRANSACTIONS OF 1000 ROWS""",
    "CALLS": """       CALL () {
                MATCH (s:Symbol {
                    type: 'METHOD',
                    repository_url: "https://github.com/igorserdyuchenko/source.git"
                })
                WITH apoc.convert.fromJsonList(s.method_calls) AS method_calls_list, s
                UNWIND method_calls_list AS method_call
                MATCH (d:Symbol {
                    type: 'METHOD',
                    repository_url: "https://github.com/igorserdyuchenko/source.git",
                    fq_name: method_call
                })
                MERGE (s)-[:CALLS_TEST]->(d)
                } IN TRANSACTIONS OF 1000 ROWS""",
    "DEFINES_SYMBOL": """   CALL () {
        MATCH (file:File {repository_url: "https://github.com/igorserdyuchenko/source.git"})
        MATCH (symbol:Symbol {repository_url: "https://github.com/igorserdyuchenko/source.git"})
        WHERE symbol.file_path = file.path
        MERGE (file)-[:DEFINES_SYMBOL_TEST]->(symbol)
        }   IN TRANSACTIONS OF 1000 ROWS""",

    "INCLUDES_FILE": """        CALL (){ 
            MATCH (repo:Repository {url: "https://github.com/igorserdyuchenko/source.git"})
            MATCH (file:File {repository_url: "https://github.com/igorserdyuchenko/source.git"})
            MERGE (repo)-[:INCLUDES_FILE_TEST]->(file)
        }  IN TRANSACTIONS OF 1000 ROWS"""
}

for key, q in queries.items():
    exec_time, rel_created = run_query_with_timing(q)
    print(f"Query: {key}")
    print(f"Execution time: {exec_time:.4f} seconds")
    print(f"Relationships created: {rel_created}\n")

driver.close()
