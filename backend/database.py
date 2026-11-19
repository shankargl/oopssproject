import os
import sqlite3
from typing import List, Dict, Any, Optional

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database"))
DB_PATH = os.path.join(DB_DIR, "cricket.db")

def get_connection() -> sqlite3.Connection:
    """Creates a connection to SQLite database with foreign keys enabled."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite database schema according to specifications."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Teams Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Players Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Batter', 'Bowler', 'All-rounder', 'Wicket-keeper')),
                team_id INTEGER NOT NULL,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );
        """)

        # 3. Tournaments Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                format TEXT NOT NULL DEFAULT 'T20' CHECK(format IN ('T20', 'ODI', 'Test')),
                status TEXT NOT NULL DEFAULT 'Upcoming' CHECK(status IN ('Upcoming', 'In Progress', 'Completed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. Tournament Teams (Associative table for Many-to-Many relation)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tournament_teams (
                tournament_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                PRIMARY KEY (tournament_id, team_id),
                FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );
        """)

        # 5. Matches Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER NOT NULL,
                match_number INTEGER NOT NULL,
                format TEXT NOT NULL DEFAULT 'T20',
                team_a_id INTEGER NOT NULL,
                team_b_id INTEGER NOT NULL,
                score_a INTEGER DEFAULT NULL,
                wickets_a INTEGER DEFAULT NULL,
                overs_a REAL DEFAULT NULL,
                score_b INTEGER DEFAULT NULL,
                wickets_b INTEGER DEFAULT NULL,
                overs_b REAL DEFAULT NULL,
                winner_id INTEGER DEFAULT NULL,
                is_tie INTEGER NOT NULL DEFAULT 0,
                result_description TEXT DEFAULT 'Scheduled',
                status TEXT NOT NULL DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'Completed')),
                FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
                FOREIGN KEY (team_a_id) REFERENCES teams(id) ON DELETE CASCADE,
                FOREIGN KEY (team_b_id) REFERENCES teams(id) ON DELETE CASCADE
            );
        """)
        conn.commit()

# ============================================================================
# TEAM CRUD OPERATIONS
# ============================================================================

def add_team(name: str) -> Dict[str, Any]:
    name = name.strip()
    if not name:
        raise ValueError("Team name cannot be empty.")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO teams (name) VALUES (?)", (name,))
        conn.commit()
        team_id = cursor.lastrowid
        return {"id": team_id, "name": name}

def get_all_teams() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.name, t.created_at, COUNT(p.id) AS player_count
            FROM teams t
            LEFT JOIN players p ON t.id = p.team_id
            GROUP BY t.id, t.name, t.created_at
            ORDER BY t.name ASC;
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_team_by_id(team_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, created_at FROM teams WHERE id = ?", (team_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_team(team_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        conn.commit()
        return cursor.rowcount > 0

# ============================================================================
# PLAYER CRUD OPERATIONS
# ============================================================================

def add_player(name: str, role: str, team_id: int) -> Dict[str, Any]:
    name = name.strip()
    role = role.strip()
    valid_roles = ('Batter', 'Bowler', 'All-rounder', 'Wicket-keeper')
    if not name:
        raise ValueError("Player name cannot be empty.")
    if role not in valid_roles:
        raise ValueError(f"Invalid role '{role}'. Must be one of {valid_roles}")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        # Verify team exists
        cursor.execute("SELECT id, name FROM teams WHERE id = ?", (team_id,))
        team = cursor.fetchone()
        if not team:
            raise ValueError(f"Team with ID {team_id} does not exist.")
        
        cursor.execute(
            "INSERT INTO players (name, role, team_id) VALUES (?, ?, ?)",
            (name, role, team_id)
        )
        conn.commit()
        player_id = cursor.lastrowid
        return {
            "id": player_id,
            "name": name,
            "role": role,
            "team_id": team_id,
            "team_name": team["name"]
        }

def get_all_players(team_id: Optional[int] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if team_id:
            cursor.execute("""
                SELECT p.id, p.name, p.role, p.team_id, t.name as team_name
                FROM players p
                JOIN teams t ON p.team_id = t.id
                WHERE p.team_id = ?
                ORDER BY p.name ASC;
            """, (team_id,))
        else:
            cursor.execute("""
                SELECT p.id, p.name, p.role, p.team_id, t.name as team_name
                FROM players p
                JOIN teams t ON p.team_id = t.id
                ORDER BY t.name ASC, p.name ASC;
            """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def delete_player(player_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM players WHERE id = ?", (player_id,))
        conn.commit()
        return cursor.rowcount > 0

# ============================================================================
# TOURNAMENT OPERATIONS
# ============================================================================

def create_tournament(name: str, format_: str, team_ids: List[int]) -> Dict[str, Any]:
    name = name.strip()
    format_ = format_.strip()
    if not name:
        raise ValueError("Tournament name cannot be empty.")
    if len(team_ids) < 2:
        raise ValueError("A tournament must have at least two participating teams.")
    if format_ not in ('T20', 'ODI', 'Test'):
        format_ = 'T20'

    with get_connection() as conn:
        cursor = conn.cursor()
        # Verify all teams exist
        placeholders = ",".join("?" for _ in team_ids)
        cursor.execute(f"SELECT id, name FROM teams WHERE id IN ({placeholders})", team_ids)
        teams = cursor.fetchall()
        if len(teams) < len(team_ids):
            raise ValueError("One or more selected teams do not exist.")

        cursor.execute(
            "INSERT INTO tournaments (name, format, status) VALUES (?, ?, 'Upcoming')",
            (name, format_)
        )
        tournament_id = cursor.lastrowid

        for t in teams:
            cursor.execute(
                "INSERT INTO tournament_teams (tournament_id, team_id) VALUES (?, ?)",
                (tournament_id, t["id"])
            )
        conn.commit()

        return {
            "id": tournament_id,
            "name": name,
            "format": format_,
            "status": "Upcoming",
            "teams": [{"id": t["id"], "name": t["name"]} for t in teams]
        }

def save_tournament_fixtures(tournament_id: int, format_: str, fixtures: List[Dict[str, Any]]) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        for fix in fixtures:
            cursor.execute("""
                INSERT INTO matches (
                    tournament_id, match_number, format, team_a_id, team_b_id, status
                ) VALUES (?, ?, ?, ?, ?, 'Scheduled')
            """, (
                tournament_id,
                fix.get("match_number", 1),
                format_,
                fix["team_a_id"],
                fix["team_b_id"]
            ))
        conn.commit()

def get_all_tournaments() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.id, t.name, t.format, t.status, t.created_at,
                COUNT(DISTINCT tt.team_id) AS team_count,
                COUNT(DISTINCT m.id) AS match_count,
                SUM(CASE WHEN m.status = 'Completed' THEN 1 ELSE 0 END) AS completed_match_count
            FROM tournaments t
            LEFT JOIN tournament_teams tt ON t.id = tt.tournament_id
            LEFT JOIN matches m ON t.id = m.tournament_id
            GROUP BY t.id, t.name, t.format, t.status, t.created_at
            ORDER BY t.id DESC;
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_tournament_by_id(tournament_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, format, status, created_at FROM tournaments WHERE id = ?", (tournament_id,))
        row = cursor.fetchone()
        if not row:
            return None
        tourney = dict(row)

        cursor.execute("""
            SELECT t.id, t.name
            FROM teams t
            JOIN tournament_teams tt ON t.id = tt.team_id
            WHERE tt.tournament_id = ?
            ORDER BY t.name ASC;
        """, (tournament_id,))
        tourney["teams"] = [dict(t) for t in cursor.fetchall()]
        return tourney

def delete_tournament(tournament_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
        conn.commit()
        return cursor.rowcount > 0

# ============================================================================
# MATCH OPERATIONS
# ============================================================================

def get_tournament_matches(tournament_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                m.id, m.tournament_id, m.match_number, m.format,
                m.team_a_id, ta.name as team_a_name,
                m.team_b_id, tb.name as team_b_name,
                m.score_a, m.wickets_a, m.overs_a,
                m.score_b, m.wickets_b, m.overs_b,
                m.winner_id,
                CASE 
                    WHEN m.is_tie = 1 THEN 'Tie'
                    WHEN m.winner_id = m.team_a_id THEN ta.name
                    WHEN m.winner_id = m.team_b_id THEN tb.name
                    ELSE NULL
                END as winner_name,
                m.is_tie, m.result_description, m.status
            FROM matches m
            JOIN teams ta ON m.team_a_id = ta.id
            JOIN teams tb ON m.team_b_id = tb.id
            WHERE m.tournament_id = ?
            ORDER BY m.match_number ASC;
        """, (tournament_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_match_by_id(match_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                m.*,
                ta.name as team_a_name,
                tb.name as team_b_name
            FROM matches m
            JOIN teams ta ON m.team_a_id = ta.id
            JOIN teams tb ON m.team_b_id = tb.id
            WHERE m.id = ?;
        """, (match_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_match_result(
    match_id: int,
    score_a: int,
    wickets_a: int,
    overs_a: float,
    score_b: int,
    wickets_b: int,
    overs_b: float,
    winner_id: Optional[int],
    is_tie: bool,
    result_description: str
) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE matches
            SET score_a = ?,
                wickets_a = ?,
                overs_a = ?,
                score_b = ?,
                wickets_b = ?,
                overs_b = ?,
                winner_id = ?,
                is_tie = ?,
                result_description = ?,
                status = 'Completed'
            WHERE id = ?;
        """, (
            score_a, wickets_a, overs_a,
            score_b, wickets_b, overs_b,
            winner_id,
            1 if is_tie else 0,
            result_description,
            match_id
        ))

        # Check if all matches in this tournament are completed, update tournament status
        cursor.execute("SELECT tournament_id FROM matches WHERE id = ?", (match_id,))
        t_row = cursor.fetchone()
        if t_row:
            tourney_id = t_row["tournament_id"]
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
                FROM matches WHERE tournament_id = ?
            """, (tourney_id,))
            counts = cursor.fetchone()
            if counts and counts["total"] > 0:
                if counts["completed"] == counts["total"]:
                    new_status = "Completed"
                elif counts["completed"] > 0:
                    new_status = "In Progress"
                else:
                    new_status = "Upcoming"
                cursor.execute("UPDATE tournaments SET status = ? WHERE id = ?", (new_status, tourney_id))

        conn.commit()
        return cursor.rowcount > 0

# ============================================================================
# STATS OPERATIONS
# ============================================================================

def get_dashboard_summary() -> Dict[str, int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM teams")
        total_teams = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM players")
        total_players = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tournaments")
        total_tournaments = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM matches WHERE status = 'Completed'")
        total_completed_matches = cursor.fetchone()[0]

        return {
            "total_teams": total_teams,
            "total_players": total_players,
            "total_tournaments": total_tournaments,
            "total_completed_matches": total_completed_matches
        }
