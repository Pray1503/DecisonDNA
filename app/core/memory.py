import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.models.artifact import Artifact
from app.models.relationship import Relationship
from app.models.decision import Decision


class DecisionMemory:
    """
    Persistent Decision Memory layer for DecisionDNA, built on SQLite.
    Stores and queries artifacts, relationships, and reconstructed decisions.
    """

    def __init__(self, db_path: Path = Path("data/decision_memory.db")):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """
        Create tables if they don't exist.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Artifacts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    source TEXT,
                    source_type TEXT,
                    external_id TEXT,
                    title TEXT,
                    content TEXT,
                    author TEXT,
                    timestamps TEXT,
                    url TEXT,
                    context TEXT,
                    metadata TEXT,
                    provenance TEXT
                )
            """)

            # 2. Relationships Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    relationship_id TEXT PRIMARY KEY,
                    source_id TEXT,
                    target_id TEXT,
                    relationship_type TEXT,
                    confidence REAL,
                    reasoning TEXT,
                    evidence TEXT,
                    provenance TEXT
                )
            """)

            # 3. Decisions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    title TEXT,
                    problem TEXT,
                    context TEXT,
                    constraints TEXT,
                    alternatives TEXT,
                    decision TEXT,
                    reasoning TEXT,
                    implementation TEXT,
                    outcomes TEXT,
                    lessons TEXT,
                    confidence REAL,
                    evidence_ids TEXT
                )
            """)
            conn.commit()

    # --------------------------------------------------
    # SAVE METHODS
    # --------------------------------------------------

    def save_artifact(self, art: Artifact) -> None:
        self.save_artifacts_batch([art])

    def save_artifacts_batch(self, artifacts: List[Artifact]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for art in artifacts:
                cursor.execute("""
                    INSERT OR REPLACE INTO artifacts (
                        artifact_id, source, source_type, external_id, title,
                        content, author, timestamps, url, context, metadata, provenance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    art.artifact_id,
                    art.source,
                    art.source_type,
                    art.external_id,
                    art.title,
                    art.content,
                    art.author,
                    json.dumps(art.timestamps, ensure_ascii=False),
                    art.url,
                    json.dumps(art.context, ensure_ascii=False),
                    json.dumps(art.metadata, ensure_ascii=False),
                    json.dumps(art.provenance, ensure_ascii=False)
                ))
            conn.commit()

    def save_relationship(self, rel: Relationship) -> None:
        self.save_relationships_batch([rel])

    def save_relationships_batch(self, relationships: List[Relationship]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for rel in relationships:
                cursor.execute("""
                    INSERT OR REPLACE INTO relationships (
                        relationship_id, source_id, target_id, relationship_type,
                        confidence, reasoning, evidence, provenance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rel.relationship_id,
                    rel.source_id,
                    rel.target_id,
                    rel.relationship_type,
                    rel.confidence,
                    rel.reasoning,
                    json.dumps(rel.evidence, ensure_ascii=False),
                    json.dumps(rel.provenance, ensure_ascii=False)
                ))
            conn.commit()

    def save_decision(self, dec: Decision) -> None:
        self.save_decisions_batch([dec])

    def save_decisions_batch(self, decisions: List[Decision]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for dec in decisions:
                cursor.execute("""
                    INSERT OR REPLACE INTO decisions (
                        decision_id, title, problem, context, constraints, alternatives,
                        decision, reasoning, implementation, outcomes, lessons, confidence, evidence_ids
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dec.decision_id,
                    dec.title,
                    dec.problem,
                    dec.context,
                    dec.constraints,
                    dec.alternatives,
                    dec.decision,
                    dec.reasoning,
                    dec.implementation,
                    dec.outcomes,
                    dec.lessons,
                    dec.confidence,
                    json.dumps(dec.evidence_ids, ensure_ascii=False)
                ))
            conn.commit()

    # --------------------------------------------------
    # GET & QUERY METHODS
    # --------------------------------------------------

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Artifact(
                artifact_id=row["artifact_id"],
                source=row["source"],
                source_type=row["source_type"],
                external_id=row["external_id"],
                title=row["title"],
                content=row["content"],
                author=row["author"],
                timestamps=json.loads(row["timestamps"] or "{}"),
                url=row["url"],
                context=json.loads(row["context"] or "{}"),
                metadata=json.loads(row["metadata"] or "{}"),
                provenance=json.loads(row["provenance"] or "{}")
            )

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Decision(
                decision_id=row["decision_id"],
                title=row["title"],
                problem=row["problem"],
                context=row["context"],
                constraints=row["constraints"],
                alternatives=row["alternatives"],
                decision=row["decision"],
                reasoning=row["reasoning"],
                implementation=row["implementation"],
                outcomes=row["outcomes"],
                lessons=row["lessons"],
                confidence=row["confidence"],
                evidence_ids=json.loads(row["evidence_ids"] or "[]")
            )

    def search_decisions(self, query_str: str) -> List[Decision]:
        """
        Perform a keyword-based search across decision titles, problem, decision chosen, and reasoning.
        """
        stop_words = {"why", "did", "the", "choose", "what", "is", "a", "for", "to", "in", "on", "how", "we", "they", "should", "use"}
        words = [w.strip().lower() for w in query_str.split()]
        keywords = [w for w in words if w and w not in stop_words and len(w) > 1]

        if not keywords:
            return []

        conditions = []
        params = []
        for kw in keywords:
            like_pattern = f"%{kw}%"
            conditions.append("(title LIKE ? OR problem LIKE ? OR decision LIKE ? OR reasoning LIKE ?)")
            params.extend([like_pattern, like_pattern, like_pattern, like_pattern])

        sql = f"SELECT * FROM decisions WHERE {' OR '.join(conditions)}"
        
        decisions = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            scored_rows = []
            for row in rows:
                score = 0
                title_lower = (row["title"] or "").lower()
                prob_lower = (row["problem"] or "").lower()
                dec_lower = (row["decision"] or "").lower()
                reas_lower = (row["reasoning"] or "").lower()
                
                text = f"{title_lower} {prob_lower} {dec_lower} {reas_lower}"
                for kw in keywords:
                    if kw in text:
                        score += 1
                        if kw in title_lower:
                            score += 2
                
                scored_rows.append((row, score))
                
            scored_rows.sort(key=lambda x: x[1], reverse=True)
            
            for row, score in scored_rows:
                if score > 0:
                    decisions.append(Decision(
                        decision_id=row["decision_id"],
                        title=row["title"],
                        problem=row["problem"],
                        context=row["context"],
                        constraints=row["constraints"],
                        alternatives=row["alternatives"],
                        decision=row["decision"],
                        reasoning=row["reasoning"],
                        implementation=row["implementation"],
                        outcomes=row["outcomes"],
                        lessons=row["lessons"],
                        confidence=row["confidence"],
                        evidence_ids=json.loads(row["evidence_ids"] or "[]")
                    ))
        return decisions
