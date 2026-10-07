import sqlite3
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from backend.config import TRACKER_DB_PATH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    source_ide TEXT NOT NULL,
    session_id TEXT NOT NULL,
    title TEXT,
    project_name TEXT,
    project_path TEXT,
    model_id TEXT,
    model_name TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    start_time TEXT,
    end_time TEXT,
    step_count INTEGER DEFAULT 0,
    has_caveman INTEGER DEFAULT 0,
    has_graphify INTEGER DEFAULT 0,
    raw_metadata TEXT,
    last_synced_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_source ON sessions(source_ide);
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_name);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_sessions_model ON sessions(model_name);

CREATE TABLE IF NOT EXISTS registered_projects (
    project_name TEXT PRIMARY KEY,
    project_path TEXT,
    description TEXT,
    created_at TEXT,
    budget_limit_usd REAL DEFAULT 0.0,
    token_limit INTEGER DEFAULT 0,
    color_tag TEXT,
    last_active_at TEXT
);

CREATE TABLE IF NOT EXISTS project_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    event_type TEXT DEFAULT 'command',
    description TEXT,
    command_text TEXT,
    model_name TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    timestamp TEXT,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_project ON project_events(project_name);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON project_events(timestamp);

CREATE TABLE IF NOT EXISTS sync_state (
    key TEXT PRIMARY KEY,
    val TEXT,
    updated_at TEXT
);
"""

def clean_project_name(raw_name: Optional[str], raw_path: Optional[str] = "") -> str:
    path_to_check = raw_path or raw_name or ""
    if path_to_check:
        m = re.search(r'0\.\s*Programacion[\\/]([^\\/]+)', path_to_check, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    
    if not raw_name or len(raw_name.strip()) == 0:
        return "General"
    
    raw = raw_name.strip()
    # Check if UUID
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', raw, re.IGNORECASE):
        return "General"
    
    return raw

class Database:
    def __init__(self, db_path=TRACKER_DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def upsert_session(self, record: Dict[str, Any]):
        total_tokens = (
            record.get("input_tokens", 0) + 
            record.get("output_tokens", 0) + 
            record.get("reasoning_tokens", 0)
        )
        record["total_tokens"] = total_tokens

        # Clean project name
        record["project_name"] = clean_project_name(
            record.get("project_name"),
            record.get("project_path")
        )

        sql = """
        INSERT INTO sessions (
            id, source_ide, session_id, title, project_name, project_path,
            model_id, model_name, input_tokens, output_tokens, reasoning_tokens,
            cache_read_tokens, cache_write_tokens, total_tokens, cost_usd,
            start_time, end_time, step_count, has_caveman, has_graphify,
            raw_metadata, last_synced_at
        ) VALUES (
            :id, :source_ide, :session_id, :title, :project_name, :project_path,
            :model_id, :model_name, :input_tokens, :output_tokens, :reasoning_tokens,
            :cache_read_tokens, :cache_write_tokens, :total_tokens, :cost_usd,
            :start_time, :end_time, :step_count, :has_caveman, :has_graphify,
            :raw_metadata, datetime('now')
        )
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            project_name=excluded.project_name,
            project_path=excluded.project_path,
            model_id=excluded.model_id,
            model_name=excluded.model_name,
            input_tokens=excluded.input_tokens,
            output_tokens=excluded.output_tokens,
            reasoning_tokens=excluded.reasoning_tokens,
            cache_read_tokens=excluded.cache_read_tokens,
            cache_write_tokens=excluded.cache_write_tokens,
            total_tokens=excluded.total_tokens,
            cost_usd=excluded.cost_usd,
            start_time=excluded.start_time,
            end_time=excluded.end_time,
            step_count=excluded.step_count,
            has_caveman=excluded.has_caveman,
            has_graphify=excluded.has_graphify,
            raw_metadata=excluded.raw_metadata,
            last_synced_at=datetime('now');
        """
        with self.get_connection() as conn:
            conn.execute(sql, record)
            conn.commit()

    def register_project(self, name: str, path: str, description: str = "", budget: float = 0.0, token_limit: int = 0):
        name = clean_project_name(name, path)
        sql = """
        INSERT INTO registered_projects (
            project_name, project_path, description, created_at, budget_limit_usd, token_limit, last_active_at
        ) VALUES (?, ?, ?, datetime('now'), ?, ?, datetime('now'))
        ON CONFLICT(project_name) DO UPDATE SET
            project_path=excluded.project_path,
            description=excluded.description,
            budget_limit_usd=excluded.budget_limit_usd,
            token_limit=excluded.token_limit,
            last_active_at=datetime('now');
        """
        with self.get_connection() as conn:
            conn.execute(sql, (name, path, description, budget, token_limit))
            conn.commit()

    def add_project_event(self, project_name: str, event_type: str, description: str, command_text: str = "", model_name: str = "", tokens_used: int = 0, cost_usd: float = 0.0, timestamp: Optional[str] = None, metadata: str = ""):
        project_name = clean_project_name(project_name)
        sql = """
        INSERT INTO project_events (
            project_name, event_type, description, command_text, model_name, tokens_used, cost_usd, timestamp, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(?, datetime('now')), ?)
        """
        with self.get_connection() as conn:
            conn.execute(sql, (project_name, event_type, description, command_text, model_name, tokens_used, cost_usd, timestamp, metadata))
            conn.commit()

    def get_sync_state(self, key: str) -> Optional[str]:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT val FROM sync_state WHERE key = ?", (key,))
            row = cur.fetchone()
            return row["val"] if row else None

    def set_sync_state(self, key: str, val: str):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO sync_state (key, val, updated_at) VALUES (?, ?, datetime('now')) ON CONFLICT(key) DO UPDATE SET val=excluded.val, updated_at=datetime('now')",
                (key, val)
            )
            conn.commit()

    def get_summary_stats(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Calcula estadísticas consolidadas, soportando filtro de rango de fechas (start_date, end_date)
        y ofreciendo desglose histórico completo (lifetime) y del día actual (today).
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            # 1. Lifetime Totals (Histórico Completo)
            cur.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                    COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                    COALESCE(SUM(reasoning_tokens), 0) as total_reasoning_tokens,
                    COALESCE(SUM(cost_usd), 0.0) as total_cost_usd
                FROM sessions
            """)
            lifetime = dict(cur.fetchone())

            # 2. Date Bounds (Fechas extremas y hoy)
            cur.execute("""
                SELECT 
                    COALESCE(MIN(SUBSTR(start_time, 1, 10)), date('now')) as min_date,
                    COALESCE(MAX(SUBSTR(start_time, 1, 10)), date('now')) as max_date,
                    date('now') as today_utc,
                    date('now', 'localtime') as today_local
                FROM sessions
                WHERE start_time IS NOT NULL AND start_time != ''
            """)
            bounds_row = cur.fetchone()
            today_utc = bounds_row["today_utc"] if bounds_row else "2026-10-07"
            today_local = bounds_row["today_local"] if bounds_row else "2026-10-06"
            date_bounds = {
                "min_date": bounds_row["min_date"] if bounds_row else "2026-01-01",
                "max_date": bounds_row["max_date"] if bounds_row else "2026-10-07",
                "today": today_local,
                "today_local": today_local,
                "today_utc": today_utc
            }

            # 3. Today's Specific Stats (Día presente / actual)
            today_target = date_bounds["today"]
            cur.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                    COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                    COALESCE(SUM(reasoning_tokens), 0) as total_reasoning_tokens,
                    COALESCE(SUM(cost_usd), 0.0) as total_cost_usd
                FROM sessions
                WHERE SUBSTR(start_time, 1, 10) = ? OR SUBSTR(start_time, 1, 10) = ?
            """, (date_bounds["today_local"], date_bounds["today_utc"]))
            today_stats = dict(cur.fetchone())

            # 4. Build Filtered Query where clause
            where_conditions = []
            params = []

            if start_date:
                where_conditions.append("start_time IS NOT NULL AND start_time != '' AND SUBSTR(start_time, 1, 10) >= ?")
                params.append(start_date)
            if end_date:
                where_conditions.append("start_time IS NOT NULL AND start_time != '' AND SUBSTR(start_time, 1, 10) <= ?")
                params.append(end_date)

            where_sql = ("WHERE " + " AND ".join(where_conditions)) if where_conditions else ""

            # Filtered Period Totals
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total_sessions,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                    COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                    COALESCE(SUM(reasoning_tokens), 0) as total_reasoning_tokens,
                    COALESCE(SUM(cost_usd), 0.0) as total_cost_usd
                FROM sessions
                {where_sql}
            """, params)
            overall = dict(cur.fetchone())

            # IDE Breakdown (Filtered)
            cur.execute(f"""
                SELECT 
                    source_ide,
                    COUNT(*) as sessions,
                    COALESCE(SUM(total_tokens), 0) as tokens,
                    COALESCE(SUM(input_tokens), 0) as input_tokens,
                    COALESCE(SUM(output_tokens), 0) as output_tokens,
                    COALESCE(SUM(cost_usd), 0.0) as cost_usd
                FROM sessions
                {where_sql}
                GROUP BY source_ide
            """, params)
            by_ide = [dict(r) for r in cur.fetchall()]

            # Model Breakdown (Filtered)
            cur.execute(f"""
                SELECT 
                    model_name,
                    COUNT(*) as sessions,
                    COALESCE(SUM(total_tokens), 0) as tokens,
                    COALESCE(SUM(cost_usd), 0.0) as cost_usd
                FROM sessions
                {where_sql}
                GROUP BY model_name
                ORDER BY tokens DESC
            """, params)
            by_model = [dict(r) for r in cur.fetchall()]

            # Project Breakdown (Filtered)
            cur.execute(f"""
                SELECT 
                    project_name,
                    COUNT(*) as sessions,
                    COALESCE(SUM(total_tokens), 0) as tokens,
                    COALESCE(SUM(cost_usd), 0.0) as cost_usd
                FROM sessions
                {where_sql}
                GROUP BY project_name
                ORDER BY tokens DESC
                LIMIT 15
            """, params)
            by_project = [dict(r) for r in cur.fetchall()]

            # Timeline (Daily)
            timeline_where = where_sql
            if not timeline_where:
                timeline_where = "WHERE start_time IS NOT NULL AND start_time != ''"
            else:
                timeline_where += " AND start_time IS NOT NULL AND start_time != ''"

            cur.execute(f"""
                SELECT 
                    SUBSTR(start_time, 1, 10) as date,
                    COUNT(*) as sessions,
                    COALESCE(SUM(total_tokens), 0) as tokens,
                    COALESCE(SUM(cost_usd), 0.0) as cost_usd
                FROM sessions
                {timeline_where}
                GROUP BY SUBSTR(start_time, 1, 10)
                ORDER BY date ASC
                LIMIT 90
            """, params)
            timeline = [dict(r) for r in cur.fetchall()]

            # Optimization stats (Caveman & Graphify)
            cur.execute(f"""
                SELECT 
                    COALESCE(SUM(has_caveman), 0) as caveman_sessions,
                    COALESCE(SUM(has_graphify), 0) as graphify_sessions
                FROM sessions
                {where_sql}
            """, params)
            optim_row = cur.fetchone()
            optim = {
                "caveman_sessions": optim_row["caveman_sessions"] if optim_row else 0,
                "graphify_sessions": optim_row["graphify_sessions"] if optim_row else 0
            }

            return {
                "overall": overall,
                "lifetime": lifetime,
                "today_stats": today_stats,
                "date_bounds": date_bounds,
                "period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_filtered": bool(start_date or end_date)
                },
                "by_ide": by_ide,
                "by_model": by_model,
                "by_project": by_project,
                "timeline": timeline,
                "optimizations": optim
            }

    def get_projects_list(self) -> List[Dict[str, Any]]:
        """Devuelve todos los proyectos con métricas acumuladas desde el inicio hasta hoy."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    s.project_name,
                    MAX(s.project_path) as project_path,
                    COUNT(*) as session_count,
                    COALESCE(SUM(s.total_tokens), 0) as total_tokens,
                    COALESCE(SUM(s.input_tokens), 0) as input_tokens,
                    COALESCE(SUM(s.output_tokens), 0) as output_tokens,
                    COALESCE(SUM(s.reasoning_tokens), 0) as reasoning_tokens,
                    COALESCE(SUM(s.cost_usd), 0.0) as total_cost_usd,
                    MIN(s.start_time) as first_session_date,
                    MAX(s.start_time) as last_session_date,
                    COUNT(DISTINCT s.source_ide) as ide_count,
                    COUNT(DISTINCT s.model_name) as model_count
                FROM sessions s
                WHERE s.project_name IS NOT NULL AND s.project_name != ''
                GROUP BY s.project_name
                ORDER BY total_tokens DESC
            """)
            return [dict(r) for r in cur.fetchall()]

    def get_project_detail(self, project_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Devuelve el desglose detallado de un proyecto con soporte de filtro de fechas."""
        with self.get_connection() as conn:
            cur = conn.cursor()

            # Where filter
            p_where = ["project_name = ?"]
            params = [project_name]
            if start_date:
                p_where.append("start_time IS NOT NULL AND SUBSTR(start_time, 1, 10) >= ?")
                params.append(start_date)
            if end_date:
                p_where.append("start_time IS NOT NULL AND SUBSTR(start_time, 1, 10) <= ?")
                params.append(end_date)

            where_sql = "WHERE " + " AND ".join(p_where)
            
            # 1. Resumen general del proyecto en el periodo
            cur.execute(f"""
                SELECT 
                    project_name,
                    MAX(project_path) as project_path,
                    COUNT(*) as session_count,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(input_tokens), 0) as input_tokens,
                    COALESCE(SUM(output_tokens), 0) as output_tokens,
                    COALESCE(SUM(reasoning_tokens), 0) as reasoning_tokens,
                    COALESCE(SUM(cost_usd), 0.0) as total_cost_usd,
                    MIN(start_time) as first_session_date,
                    MAX(start_time) as last_session_date
                FROM sessions
                {where_sql}
            """, params)
            base_row = cur.fetchone()
            if not base_row or not base_row["project_name"]:
                # If filtered yielded 0, query lifetime summary so project name and path remain visible
                cur.execute("SELECT project_name, MAX(project_path) as project_path FROM sessions WHERE project_name = ?", (project_name,))
                alt = cur.fetchone()
                if not alt or not alt["project_name"]:
                    return None
                summary = {
                    "project_name": alt["project_name"],
                    "project_path": alt["project_path"],
                    "session_count": 0,
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_tokens": 0,
                    "total_cost_usd": 0.0,
                    "first_session_date": "--",
                    "last_session_date": "--"
                }
            else:
                summary = dict(base_row)

            # Lifetime project summary
            cur.execute("""
                SELECT 
                    COUNT(*) as lifetime_sessions,
                    COALESCE(SUM(total_tokens), 0) as lifetime_tokens,
                    COALESCE(SUM(cost_usd), 0.0) as lifetime_cost_usd
                FROM sessions
                WHERE project_name = ?
            """, (project_name,))
            proj_life = dict(cur.fetchone())

            # 2. Desglose detallado por CADA Inteligencia Artificial (Modelos) en este proyecto
            cur.execute(f"""
                SELECT 
                    model_name,
                    COUNT(*) as session_count,
                    COALESCE(SUM(input_tokens), 0) as input_tokens,
                    COALESCE(SUM(output_tokens), 0) as output_tokens,
                    COALESCE(SUM(reasoning_tokens), 0) as reasoning_tokens,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(cost_usd), 0.0) as cost_usd
                FROM sessions
                {where_sql}
                GROUP BY model_name
                ORDER BY total_tokens DESC
            """, params)
            models_breakdown = [dict(r) for r in cur.fetchall()]

            # 3. Línea temporal histórica del proyecto
            cur.execute(f"""
                SELECT 
                    SUBSTR(start_time, 1, 10) as date,
                    COUNT(*) as session_count,
                    COALESCE(SUM(total_tokens), 0) as tokens,
                    COALESCE(SUM(input_tokens), 0) as input_tokens,
                    COALESCE(SUM(output_tokens), 0) as output_tokens,
                    COALESCE(SUM(cost_usd), 0.0) as cost_usd
                FROM sessions
                {where_sql} AND start_time IS NOT NULL AND start_time != ''
                GROUP BY SUBSTR(start_time, 1, 10)
                ORDER BY date ASC
            """, params)
            timeline = [dict(r) for r in cur.fetchall()]

            # 4. Sesiones y procesos registrados en este proyecto
            cur.execute(f"""
                SELECT 
                    id, source_ide, session_id, title, model_name,
                    input_tokens, output_tokens, reasoning_tokens, total_tokens,
                    cost_usd, start_time, end_time, has_caveman, has_graphify
                FROM sessions
                {where_sql}
                ORDER BY start_time DESC
                LIMIT 100
            """, params)
            sessions = [dict(r) for r in cur.fetchall()]

            # 5. Eventos manuales o de comandos registrados para el proyecto
            ev_params = [project_name]
            ev_where = ["project_name = ?"]
            if start_date:
                ev_where.append("SUBSTR(timestamp, 1, 10) >= ?")
                ev_params.append(start_date)
            if end_date:
                ev_where.append("SUBSTR(timestamp, 1, 10) <= ?")
                ev_params.append(end_date)

            cur.execute(f"""
                SELECT * FROM project_events
                WHERE {" AND ".join(ev_where)}
                ORDER BY timestamp DESC
                LIMIT 50
            """, ev_params)
            events = [dict(r) for r in cur.fetchall()]

            return {
                "summary": summary,
                "lifetime": proj_life,
                "models": models_breakdown,
                "timeline": timeline,
                "sessions": sessions,
                "events": events
            }

    def list_sessions(
        self, 
        limit: int = 50, 
        ide_filter: Optional[str] = None, 
        search: Optional[str] = None, 
        project_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM sessions WHERE 1=1"
        params = []

        if ide_filter and ide_filter.lower() != "all":
            query += " AND source_ide = ?"
            params.append(ide_filter.lower())

        if project_filter:
            query += " AND project_name = ?"
            params.append(project_filter)

        if start_date:
            query += " AND (start_time IS NOT NULL AND start_time != '' AND SUBSTR(start_time, 1, 10) >= ?)"
            params.append(start_date)

        if end_date:
            query += " AND (start_time IS NOT NULL AND start_time != '' AND SUBSTR(start_time, 1, 10) <= ?)"
            params.append(end_date)

        if search:
            query += " AND (title LIKE ? OR project_name LIKE ? OR model_name LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])

        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cur = conn.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
