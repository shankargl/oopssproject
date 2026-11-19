
import os
import sys
import json
import subprocess
from typing import Dict, Any

from flask import Flask, request, jsonify, send_from_directory

# ============================================================================
# DIRECTORY CONFIGURATION
# ============================================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
CPP_ENGINE_DIR = os.path.join(BASE_DIR, "cpp_engine")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Database module
import database_crex_upgrade as database

# ============================================================================
# FLASK CONFIGURATION
# ============================================================================

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

ENGINE_EXE_NAME = "engine.exe" if os.name == "nt" else "engine"
ENGINE_PATH = os.path.join(CPP_ENGINE_DIR, ENGINE_EXE_NAME)

# ============================================================================
# C++ ENGINE INTEGRATION
# ============================================================================

def run_cpp_engine(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    json_input = json.dumps(payload)

    if os.path.exists(ENGINE_PATH):
        try:
            result = subprocess.run(
                [ENGINE_PATH, command, json_input],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=CPP_ENGINE_DIR
            )

            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout.strip())
                    data["engine_source"] = "C++ OOP Engine (Compiled Binary)"
                    return data
                except json.JSONDecodeError:
                    print("[C++ Engine Error] Invalid JSON:", result.stdout)

            print(
                f"[C++ Engine Notice] Return code: {result.returncode}, "
                f"Stderr: {result.stderr.strip()}"
            )

        except Exception as e:
            print(f"[C++ Engine Notice] Execution error: {e}")

    return mirrored_cpp_engine_logic(command, payload)


def mirrored_cpp_engine_logic(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:

    if command in ("--fixtures", "-f"):

        teams = payload.get("teams", [])

        if len(teams) < 2:
            return {
                "status": "error",
                "message": "At least two teams are required to create a tournament."
            }

        fixtures = []
        match_number = 1
        format_ = payload.get("format", "T20")

        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                fixtures.append({
                    "match_number": match_number,
                    "format": format_,
                    "team_a_id": teams[i]["id"],
                    "team_a_name": teams[i]["name"],
                    "team_b_id": teams[j]["id"],
                    "team_b_name": teams[j]["name"],
                    "match_stage": "League"
                })
                match_number += 1

        return {
            "status": "success",
            "tournament_id": payload.get("tournament_id", 1),
            "tournament_name": payload.get("tournament_name", "Tournament"),
            "format": format_,
            "total_fixtures": len(fixtures),
            "fixtures": fixtures,
            "engine_source": "C++ OOP Engine (Mirrored Fallback)"
        }

    elif command in ("--calculate-result", "--result", "-r"):

        format_ = payload.get("format", "T20")

        score_a = int(payload.get("score_a", 0))
        wickets_a = int(payload.get("wickets_a", 0))
        overs_a = float(payload.get("overs_a", 0.0))

        score_b = int(payload.get("score_b", 0))
        wickets_b = int(payload.get("wickets_b", 0))
        overs_b = float(payload.get("overs_b", 0.0))

        team_a_name = payload.get("team_a_name", "Team A")
        team_b_name = payload.get("team_b_name", "Team B")

        team_a_id = payload.get("team_a_id", 1)
        team_b_id = payload.get("team_b_id", 2)

        if score_a > score_b:
            winner_id = team_a_id
            winner_name = team_a_name
            loser_id = team_b_id
            loser_name = team_b_name
            is_tie = False
            margin = score_a - score_b

            result_description = (
                f"{winner_name} won by {margin} runs ({format_})"
            )

        elif score_b > score_a:
            winner_id = team_b_id
            winner_name = team_b_name
            loser_id = team_a_id
            loser_name = team_a_name
            is_tie = False

            wickets_left = max(0, 10 - wickets_b)

            result_description = (
                f"{winner_name} won by {wickets_left} wickets ({format_})"
            )

        else:
            winner_id = 0
            winner_name = "Tie"
            loser_id = 0
            loser_name = ""
            is_tie = True

            result_description = (
                f"Match ended in a Tie! Both teams scored {score_a} runs ({format_})"
            )

        return {
            "status": "success",
            "match": {
                "match_id": payload.get("match_id", 1),
                "format": format_,
                "team_a_id": team_a_id,
                "team_a_name": team_a_name,
                "team_b_id": team_b_id,
                "team_b_name": team_b_name,
                "score_a": score_a,
                "wickets_a": wickets_a,
                "overs_a": overs_a,
                "score_b": score_b,
                "wickets_b": wickets_b,
                "overs_b": overs_b,
                "is_completed": True,
                "is_tie": is_tie,
                "winner_id": winner_id,
                "winner_name": winner_name,
                "loser_id": loser_id,
                "loser_name": loser_name,
                "result_description": result_description
            },
            "engine_source": "C++ OOP Engine (Mirrored Fallback)"
        }

    return {
        "status": "error",
        "message": f"Unknown command {command}"
    }


# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ============================================================================
# DASHBOARD API
# ============================================================================

@app.route("/api/dashboard/stats", methods=["GET"])
def get_stats():
    try:
        stats = database.get_dashboard_summary()
        stats["engine_binary_exists"] = os.path.exists(ENGINE_PATH)

        return jsonify({"status": "success", "data": stats})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# TEAMS API
# ============================================================================

@app.route("/api/teams", methods=["GET"])
def list_teams():
    try:
        teams = database.get_all_teams()
        return jsonify({"status": "success", "data": teams})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/teams", methods=["POST"])
def create_team():
    try:
        data = request.get_json() or {}
        name = data.get("name")

        if not name or not name.strip():
            return jsonify({
                "status": "error",
                "message": "Team name is required."
            }), 400

        team = database.add_team(name)

        return jsonify({"status": "success", "data": team}), 201

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return jsonify({
                "status": "error",
                "message": "A team with this name already exists."
            }), 400

        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/teams/<int:team_id>", methods=["DELETE"])
def remove_team(team_id):
    try:
        deleted = database.delete_team(team_id)

        if deleted:
            return jsonify({
                "status": "success",
                "message": "Team deleted successfully."
            })

        return jsonify({
            "status": "error",
            "message": "Team not found."
        }), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# PLAYERS API
# ============================================================================

@app.route("/api/players", methods=["GET"])
def list_players():
    try:
        team_id = request.args.get("team_id", type=int)
        players = database.get_all_players(team_id)

        return jsonify({"status": "success", "data": players})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/players", methods=["POST"])
def create_player():
    try:
        data = request.get_json() or {}

        name = data.get("name")
        role = data.get("role")
        team_id = data.get("team_id")

        if not name or not role or not team_id:
            return jsonify({
                "status": "error",
                "message": "Player name, role, and team_id are required."
            }), 400

        player = database.add_player(name, role, int(team_id))

        return jsonify({"status": "success", "data": player}), 201

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/players/<int:player_id>", methods=["DELETE"])
def remove_player(player_id):
    try:
        deleted = database.delete_player(player_id)

        if deleted:
            return jsonify({
                "status": "success",
                "message": "Player deleted successfully."
            })

        return jsonify({
            "status": "error",
            "message": "Player not found."
        }), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# TOURNAMENT API
# ============================================================================

@app.route("/api/tournaments", methods=["GET"])
def list_tournaments():
    try:
        tournaments = database.get_all_tournaments()
        return jsonify({"status": "success", "data": tournaments})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/tournaments/<int:tournament_id>", methods=["GET"])
def get_tournament_details(tournament_id):
    try:
        tournament = database.get_tournament_by_id(tournament_id)

        if not tournament:
            return jsonify({
                "status": "error",
                "message": "Tournament not found."
            }), 404

        return jsonify({"status": "success", "data": tournament})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/tournaments", methods=["POST"])
def create_tournament():
    try:
        data = request.get_json() or {}

        name = data.get("name")
        format_ = data.get("format", "T20")
        team_ids = data.get("team_ids", [])

        if not name or not name.strip():
            return jsonify({
                "status": "error",
                "message": "Tournament name is required."
            }), 400

        if not isinstance(team_ids, list) or len(team_ids) < 2:
            return jsonify({
                "status": "error",
                "message": "Cannot create tournament with fewer than two teams."
            }), 400

        tournament = database.create_tournament(name, format_, team_ids)

        engine_payload = {
            "tournament_id": tournament["id"],
            "tournament_name": tournament["name"],
            "format": tournament["format"],
            "teams": tournament["teams"]
        }

        engine_response = run_cpp_engine("--fixtures", engine_payload)

        if engine_response.get("status") != "success":
            return jsonify({
                "status": "error",
                "message": engine_response.get(
                    "message", "Fixture generation failed."
                )
            }), 500

        fixtures = engine_response.get("fixtures", [])

        database.save_tournament_fixtures(
            tournament["id"], format_, fixtures
        )

        tournament["fixtures"] = fixtures
        tournament["engine_source"] = engine_response.get("engine_source")

        return jsonify({"status": "success", "data": tournament}), 201

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/tournaments/<int:tournament_id>", methods=["DELETE"])
def remove_tournament(tournament_id):
    try:
        deleted = database.delete_tournament(tournament_id)

        if deleted:
            return jsonify({
                "status": "success",
                "message": "Tournament deleted successfully."
            })

        return jsonify({
            "status": "error",
            "message": "Tournament not found."
        }), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# MATCH API
# ============================================================================

@app.route("/api/tournaments/<int:tournament_id>/matches", methods=["GET"])
def list_tournament_matches(tournament_id):
    try:
        matches = database.get_tournament_matches(tournament_id)
        return jsonify({"status": "success", "data": matches})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/matches/<int:match_id>/score", methods=["POST"])
def submit_match_score(match_id):
    try:
        match_record = database.get_match_by_id(match_id)

        if not match_record:
            return jsonify({
                "status": "error",
                "message": "Match not found."
            }), 404

        data = request.get_json() or {}

        score_a = int(data.get("score_a", 0))
        wickets_a = int(data.get("wickets_a", 0))
        overs_a = float(data.get("overs_a", 20.0))

        score_b = int(data.get("score_b", 0))
        wickets_b = int(data.get("wickets_b", 0))
        overs_b = float(data.get("overs_b", 20.0))

        if not (0 <= wickets_a <= 10 and 0 <= wickets_b <= 10):
            return jsonify({
                "status": "error",
                "message": "Wickets must be between 0 and 10."
            }), 400

        if min(score_a, score_b, overs_a, overs_b) < 0:
            return jsonify({
                "status": "error",
                "message": "Scores and overs cannot be negative."
            }), 400

        engine_payload = {
            "match_id": match_id,
            "format": match_record["format"],
            "team_a_id": match_record["team_a_id"],
            "team_a_name": match_record["team_a_name"],
            "team_b_id": match_record["team_b_id"],
            "team_b_name": match_record["team_b_name"],
            "score_a": score_a,
            "wickets_a": wickets_a,
            "overs_a": overs_a,
            "score_b": score_b,
            "wickets_b": wickets_b,
            "overs_b": overs_b
        }

        engine_response = run_cpp_engine(
            "--calculate-result", engine_payload
        )

        if engine_response.get("status") != "success":
            return jsonify({
                "status": "error",
                "message": "Failed to calculate match result."
            }), 500

        calc_match = engine_response.get("match", {})

        winner_id = calc_match.get("winner_id")
        if winner_id == 0:
            winner_id = None

        database.update_match_result(
            match_id=match_id,
            score_a=score_a,
            wickets_a=wickets_a,
            overs_a=overs_a,
            score_b=score_b,
            wickets_b=wickets_b,
            overs_b=overs_b,
            winner_id=winner_id,
            is_tie=calc_match.get("is_tie", False),
            result_description=calc_match.get(
                "result_description", ""
            )
        )

        return jsonify({
            "status": "success",
            "data": calc_match,
            "engine_source": engine_response.get("engine_source")
        })

    except (ValueError, TypeError) as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# SCORECARD API
# ============================================================================

@app.route("/api/matches/<int:match_id>/scorecard", methods=["GET"])
def get_match_scorecard_api(match_id):
    try:
        scorecard = database.get_match_scorecard(match_id)
        return jsonify({"status": "success", "data": scorecard})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/matches/<int:match_id>/batting", methods=["POST"])
def save_batting_entry(match_id):
    try:
        data = request.get_json() or {}

        database.save_player_batting(
            match_id=match_id,
            innings=int(data.get("innings", 1)),
            team_id=int(data.get("team_id")),
            player_id=int(data.get("player_id")),
            runs=int(data.get("runs", 0)),
            balls=int(data.get("balls", 0)),
            fours=int(data.get("fours", 0)),
            sixes=int(data.get("sixes", 0)),
            is_out=bool(data.get("is_out", False)),
            dismissal=data.get("dismissal")
        )

        return jsonify({
            "status": "success",
            "message": "Batting scorecard saved successfully."
        })

    except (ValueError, TypeError) as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/matches/<int:match_id>/bowling", methods=["POST"])
def save_bowling_entry(match_id):
    try:
        data = request.get_json() or {}

        database.save_player_bowling(
            match_id=match_id,
            innings=int(data.get("innings", 1)),
            team_id=int(data.get("team_id")),
            player_id=int(data.get("player_id")),
            overs=data.get("overs", 0.0),
            maidens=int(data.get("maidens", 0)),
            runs_conceded=int(data.get("runs_conceded", 0)),
            wickets=int(data.get("wickets", 0)),
            wides=int(data.get("wides", 0)),
            no_balls=int(data.get("no_balls", 0))
        )

        return jsonify({
            "status": "success",
            "message": "Bowling scorecard saved successfully."
        })

    except (ValueError, TypeError) as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# STANDINGS AND PLAYER STATS
# ============================================================================

@app.route("/api/tournaments/<int:tournament_id>/standings", methods=["GET"])
def get_tournament_standings(tournament_id):
    try:
        tourney = database.get_tournament_by_id(tournament_id)

        if not tourney:
            return jsonify({
                "status": "error",
                "message": "Tournament not found."
            }), 404

        standings = database.get_points_table(tournament_id)

        return jsonify({
            "status": "success",
            "data": {
                "tournament": tourney,
                "standings": standings
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/tournaments/<int:tournament_id>/player-stats", methods=["GET"])
def get_tournament_player_stats(tournament_id):
    try:
        stats = database.get_player_tournament_stats(tournament_id)
        return jsonify({"status": "success", "data": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# PLAYOFFS API
# ============================================================================

@app.route("/api/tournaments/<int:tournament_id>/playoffs/generate", methods=["POST"])
def generate_tournament_playoffs(tournament_id):
    try:
        fixtures = database.generate_playoffs(tournament_id)

        return jsonify({
            "status": "success",
            "data": fixtures,
            "message": "Playoffs generated successfully."
        })

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/tournaments/<int:tournament_id>/playoffs/advance", methods=["POST"])
def advance_tournament_playoffs(tournament_id):
    try:
        fixtures = database.advance_playoffs(tournament_id)

        return jsonify({
            "status": "success",
            "data": fixtures,
            "message": "Playoffs advanced successfully."
        })

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# DEMO DATA
# ============================================================================

@app.route("/api/demo/seed", methods=["POST"])
def seed_demo_data():
    try:
        sample_teams = [
            {
                "name": "India",
                "players": [
                    ("Rohit Sharma", "Batter"),
                    ("Virat Kohli", "Batter"),
                    ("Hardik Pandya", "All-rounder"),
                    ("Jasprit Bumrah", "Bowler"),
                    ("Rishabh Pant", "Wicket-keeper")
                ]
            },
            {
                "name": "Australia",
                "players": [
                    ("Pat Cummins", "Bowler"),
                    ("Travis Head", "Batter"),
                    ("Glenn Maxwell", "All-rounder"),
                    ("Mitchell Starc", "Bowler"),
                    ("Josh Inglis", "Wicket-keeper")
                ]
            },
            {
                "name": "England",
                "players": [
                    ("Jos Buttler", "Wicket-keeper"),
                    ("Harry Brook", "Batter"),
                    ("Ben Stokes", "All-rounder"),
                    ("Jofra Archer", "Bowler"),
                    ("Adil Rashid", "Bowler")
                ]
            },
            {
                "name": "South Africa",
                "players": [
                    ("Aiden Markram", "Batter"),
                    ("Heinrich Klaasen", "Wicket-keeper"),
                    ("Marco Jansen", "All-rounder"),
                    ("Kagiso Rabada", "Bowler"),
                    ("David Miller", "Batter")
                ]
            }
        ]

        created_team_ids = []

        for team_info in sample_teams:
            existing = [
                team for team in database.get_all_teams()
                if team["name"].lower() == team_info["name"].lower()
            ]

            if existing:
                team_id = existing[0]["id"]
            else:
                team = database.add_team(team_info["name"])
                team_id = team["id"]

            created_team_ids.append(team_id)

            existing_players = database.get_all_players(team_id)

            for player_name, player_role in team_info["players"]:
                if not any(
                    p["name"].lower() == player_name.lower()
                    for p in existing_players
                ):
                    database.add_player(
                        player_name, player_role, team_id
                    )

        tournaments = database.get_all_tournaments()

        if not tournaments and len(created_team_ids) >= 4:
            tournament = database.create_tournament(
                "ICC Super 4 Champions Cup",
                "T20",
                created_team_ids[:4]
            )

            engine_payload = {
                "tournament_id": tournament["id"],
                "tournament_name": tournament["name"],
                "format": "T20",
                "teams": tournament["teams"]
            }

            engine_response = run_cpp_engine(
                "--fixtures", engine_payload
            )

            if engine_response.get("status") == "success":
                database.save_tournament_fixtures(
                    tournament["id"],
                    "T20",
                    engine_response["fixtures"]
                )

        return jsonify({
            "status": "success",
            "message": "Demo sample teams, players, and fixtures initialized!"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":

    database.init_db()

    port = int(os.environ.get("PORT", 5000))

    print("=" * 60)
    print("CRICKET TOURNAMENT MANAGEMENT SYSTEM - READY")
    print(f"Server running at: http://127.0.0.1:{port}")
    print(f"C++ Engine Binary: {ENGINE_PATH}")
    print(f"Engine Exists: {os.path.exists(ENGINE_PATH)}")
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
