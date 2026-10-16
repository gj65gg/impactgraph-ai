
from neo4j import GraphDatabase
from app.config import setting


class DependencyGraph:

    def __init__(self):
        self.driver = GraphDatabase.driver(
            setting("NEO4J_URI"),
            auth=(
                setting("NEO4J_USER"),
                setting("NEO4J_PASSWORD")
            )
        )

    def close(self):
        self.driver.close()

    def initialize(self):
        self.driver.execute_query("""
            CREATE CONSTRAINT component_id
            IF NOT EXISTS
            FOR (c:Component)
            REQUIRE c.sys_id IS UNIQUE
        """)

    def save_component(self, item):
        self.driver.execute_query("""
            MERGE (c:Component {
                sys_id: $sys_id
            })

            SET c.name = $name,
                c.type = $type,
                c.scope = $scope,
                c.updated_at = $updated_at
        """,
            sys_id=item["sys_id"],
            name=item["name"],
            type=item["type"],
            scope=item.get("scope", ""),
            updated_at=item.get(
                "updated_at", ""
            )
        )

    def replace_outgoing_dependencies(
        self,
        source_id,
        dependencies
    ):
        # Remove old constructor-based edges
        # for the component being rescanned.
        self.driver.execute_query("""
            MATCH (source:Component {
                sys_id: $source_id
            })-[r:DEPENDS_ON {
                method: 'ast_constructor'
            }]->()

            DELETE r
        """, source_id=source_id)

        for edge in dependencies:
            self.driver.execute_query("""
                MATCH (a:Component {
                    sys_id: $source_id
                })

                MATCH (b:Component {
                    sys_id: $target_id
                })

                MERGE (a)-[r:DEPENDS_ON {
                    method: 'ast_constructor',
                    symbol: $symbol,
                    line: $line
                }]->(b)

                SET r.status = 'candidate'
            """, **edge)

    def get_impact(self, sys_id, depth=3):
        if not 1 <= depth <= 5:
            raise ValueError(
                "Depth must be between 1 and 5"
            )

        query = f"""
            MATCH p=(dependent:Component)
                -[:DEPENDS_ON*1..{depth}]->
                (target:Component {{
                    sys_id: $sys_id
                }})

            WHERE dependent.sys_id <> $sys_id

            RETURN
                dependent.sys_id AS sys_id,
                dependent.name AS name,
                dependent.type AS type,
                min(length(p)) AS distance

            ORDER BY distance, name

            LIMIT 200
        """

        records, _, _ = self.driver.execute_query(
            query,
            sys_id=sys_id
        )

        return [
            dict(record)
            for record in records
        ]
