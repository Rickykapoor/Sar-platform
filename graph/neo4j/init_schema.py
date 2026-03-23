import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_schema():
    load_dotenv(".env.local")
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    queries = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Account) REQUIRE a.account_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Transaction) REQUIRE t.transaction_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:SARCase) REQUIRE s.case_id IS UNIQUE",
        "CREATE INDEX FOR (e:AuditEvent) ON (e.timestamp)",
        "CREATE INDEX FOR (r:RiskSignal) ON (r.risk_score)",
        "CREATE INDEX FOR (s:SARCase) ON (s.risk_score)"
    ]

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            for query in queries:
                session.run(query)
        driver.close()
        print("Schema initialized")
    except Exception as e:
        logger.error(f"Failed to initialize schema: {e}")

if __name__ == "__main__":
    init_schema()
