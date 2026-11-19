#include "Player.cpp"
#include "Team.cpp"
#include "Match.cpp"
#include "Tournament.cpp"

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <cctype>
#include <sstream>
#include <memory>

// ============================================================================
// LIGHTWEIGHT, ZERO-DEPENDENCY JSON PARSER FOR C++ & PYTHON INTEGRATION
// ============================================================================

enum JsonType { J_NULL, J_BOOL, J_NUM, J_STR, J_ARR, J_OBJ };

struct JsonValue {
    JsonType type;
    bool bVal;
    double nVal;
    std::string sVal;
    std::vector<JsonValue> arr;
    std::map<std::string, JsonValue> obj;

    JsonValue() : type(J_NULL), bVal(false), nVal(0.0) {}

    int asInt(int def = 0) const {
        return (type == J_NUM) ? static_cast<int>(nVal) : def;
    }

    double asDouble(double def = 0.0) const {
        return (type == J_NUM) ? nVal : def;
    }

    std::string asString(const std::string& def = "") const {
        return (type == J_STR) ? sVal : def;
    }

    bool asBool(bool def = false) const {
        return (type == J_BOOL) ? bVal : def;
    }

    bool has(const std::string& key) const {
        return type == J_OBJ && obj.find(key) != obj.end();
    }

    const JsonValue& get(const std::string& key) const {
        static const JsonValue nullVal;
        if (type == J_OBJ) {
            auto it = obj.find(key);
            if (it != obj.end()) return it->second;
        }
        return nullVal;
    }
};

class JsonParser {
private:
    std::string src;
    size_t pos;

    void skipWhitespace() {
        while (pos < src.size() && (std::isspace(static_cast<unsigned char>(src[pos])) || src[pos] == '\r' || src[pos] == '\n')) {
            pos++;
        }
    }

    char peek() {
        skipWhitespace();
        return (pos < src.size()) ? src[pos] : '\0';
    }

    char get() {
        skipWhitespace();
        return (pos < src.size()) ? src[pos++] : '\0';
    }

    std::string parseString() {
        get(); // Consume opening quote
        std::string s;
        while (pos < src.size()) {
            char c = src[pos++];
            if (c == '"') {
                return s;
            } else if (c == '\\' && pos < src.size()) {
                char next = src[pos++];
                if (next == '"') s += '"';
                else if (next == '\\') s += '\\';
                else if (next == 'n') s += '\n';
                else if (next == 'r') s += '\r';
                else if (next == 't') s += '\t';
                else s += next;
            } else {
                s += c;
            }
        }
        return s;
    }

    JsonValue parseNumber() {
        skipWhitespace();
        size_t start = pos;
        if (pos < src.size() && (src[pos] == '-' || src[pos] == '+')) pos++;
        while (pos < src.size() && (std::isdigit(static_cast<unsigned char>(src[pos])) || src[pos] == '.')) {
            pos++;
        }
        std::string numStr = src.substr(start, pos - start);
        JsonValue val;
        val.type = J_NUM;
        try {
            val.nVal = std::stod(numStr);
        } catch (...) {
            val.nVal = 0.0;
        }
        return val;
    }

    JsonValue parseArray() {
        get(); // Consume '['
        JsonValue val;
        val.type = J_ARR;
        skipWhitespace();
        if (peek() == ']') {
            get();
            return val;
        }
        while (pos < src.size()) {
            val.arr.push_back(parseValue());
            char c = peek();
            if (c == ',') {
                get();
            } else if (c == ']') {
                get();
                break;
            } else {
                break;
            }
        }
        return val;
    }

    JsonValue parseObject() {
        get(); // Consume '{'
        JsonValue val;
        val.type = J_OBJ;
        skipWhitespace();
        if (peek() == '}') {
            get();
            return val;
        }
        while (pos < src.size()) {
            skipWhitespace();
            if (peek() != '"') break;
            std::string key = parseString();
            skipWhitespace();
            if (peek() == ':') get();
            JsonValue child = parseValue();
            val.obj[key] = child;
            char c = peek();
            if (c == ',') {
                get();
            } else if (c == '}') {
                get();
                break;
            } else {
                break;
            }
        }
        return val;
    }

public:
    JsonParser(const std::string& input) : src(input), pos(0) {}

    JsonValue parseValue() {
        skipWhitespace();
        char c = peek();
        if (c == '"') {
            JsonValue val;
            val.type = J_STR;
            val.sVal = parseString();
            return val;
        } else if (c == '{') {
            return parseObject();
        } else if (c == '[') {
            return parseArray();
        } else if (std::isdigit(static_cast<unsigned char>(c)) || c == '-' || c == '+') {
            return parseNumber();
        } else if (c == 't' || c == 'T') {
            pos += 4;
            JsonValue val;
            val.type = J_BOOL;
            val.bVal = true;
            return val;
        } else if (c == 'f' || c == 'F') {
            pos += 5;
            JsonValue val;
            val.type = J_BOOL;
            val.bVal = false;
            return val;
        } else if (c == 'n') {
            pos += 4;
            return JsonValue();
        }
        return JsonValue();
    }
};

// ============================================================================
// ENGINE HANDLERS
// ============================================================================

void handleGenerateFixtures(const std::string& jsonInput) {
    JsonParser parser(jsonInput);
    JsonValue root = parser.parseValue();

    int tourneyId = root.get("tournament_id").asInt(1);
    std::string tourneyName = root.get("tournament_name").asString("Tournament");
    std::string format = root.get("format").asString("T20");

    Tournament tournament(tourneyId, tourneyName, format);

    const JsonValue& teamsArr = root.get("teams");
    if (teamsArr.type == J_ARR) {
        for (const auto& tItem : teamsArr.arr) {
            int tId = tItem.get("id").asInt(0);
            std::string tName = tItem.get("name").asString("Unknown Team");
            Team team(tId, tName);
            tournament.addTeam(team);
        }
    }

    if (tournament.getTeams().size() < 5) {
        std::cout << "{\"status\":\"error\",\"message\":\"At least five teams are required to create a tournament with playoffs.\"}" << std::endl;
        return;
    }

    bool success = tournament.generateRoundRobinFixtures();
    if (success) {
        std::cout << tournament.fixturesToJson() << std::endl;
    } else {
        std::cout << "{\"status\":\"error\",\"message\":\"Failed to generate fixtures.\"}" << std::endl;
    }
}

void handleCalculateResult(const std::string& jsonInput) {
    JsonParser parser(jsonInput);
    JsonValue root = parser.parseValue();

    int matchId = root.get("match_id").asInt(1);
    std::string format = root.get("format").asString("T20");

    int teamAId = root.get("team_a_id").asInt(1);
    std::string teamAName = root.get("team_a_name").asString("Team A");
    Team teamA(teamAId, teamAName);

    int teamBId = root.get("team_b_id").asInt(2);
    std::string teamBName = root.get("team_b_name").asString("Team B");
    Team teamB(teamBId, teamBName);

    int scoreA = root.get("score_a").asInt(0);
    int wicketsA = root.get("wickets_a").asInt(0);
    double oversA = root.get("overs_a").asDouble(0.0);

    int scoreB = root.get("score_b").asInt(0);
    int wicketsB = root.get("wickets_b").asInt(0);
    double oversB = root.get("overs_b").asDouble(0.0);

    // Demonstrate Runtime Polymorphism via factory & base pointer
    std::unique_ptr<Match> match(createMatch(format, matchId, teamA, teamB));
    match->setScores(scoreA, wicketsA, oversA, scoreB, wicketsB, oversB);
    match->calculateWinner();

    std::cout << "{\"status\":\"success\",\"match\":" << match->toJson() << "}" << std::endl;
}

void handlePointsTable(const std::string& jsonInput) {
    JsonParser parser(jsonInput);
    JsonValue root = parser.parseValue();

    int tourneyId = root.get("tournament_id").asInt(1);
    std::string tourneyName = root.get("tournament_name").asString("Tournament");
    std::string format = root.get("format").asString("T20");

    Tournament tournament(tourneyId, tourneyName, format);

    const JsonValue& teamsArr = root.get("teams");
    if (teamsArr.type == J_ARR) {
        for (const auto& tItem : teamsArr.arr) {
            int tId = tItem.get("id").asInt(0);
            std::string tName = tItem.get("name").asString("Unknown Team");
            Team team(tId, tName);
            tournament.addTeam(team);
        }
    }

    std::vector<MatchRecord> matchRecords;
    const JsonValue& matchesArr = root.get("matches");
    if (matchesArr.type == J_ARR) {
        for (const auto& mItem : matchesArr.arr) {
            MatchRecord rec;
            rec.teamAId = mItem.get("team_a_id").asInt(0);
            rec.teamBId = mItem.get("team_b_id").asInt(0);
            rec.scoreA = mItem.get("score_a").asInt(0);
            rec.scoreB = mItem.get("score_b").asInt(0);
            rec.winnerId = mItem.get("winner_id").asInt(0);
            rec.isTie = mItem.get("is_tie").asBool(false);
            rec.isCompleted = mItem.get("is_completed").asBool(true);
            matchRecords.push_back(rec);
        }
    }

    std::vector<TeamStanding> table = tournament.calculatePointsTable(matchRecords);

    std::ostringstream ss;
    ss << "{\"status\":\"success\","
       << "\"tournament_id\":" << tourneyId << ","
       << "\"tournament_name\":\"" << tourneyName << "\","
       << "\"format\":\"" << format << "\","
       << "\"points_table\":[";

    for (size_t i = 0; i < table.size(); ++i) {
        if (i > 0) ss << ",";
        ss << table[i].toJson();
    }
    ss << "]}";

    std::cout << ss.str() << std::endl;
}

// ============================================================================
// OOP DEMONSTRATION MODE (STANDALONE CONSOLE EXECUTION)
// ============================================================================

void runConsoleOOPDemo() {
    std::cout << "\n";
    std::cout << "******************************************************************\n";
    std::cout << "*       CRICKET TOURNAMENT MANAGEMENT SYSTEM - C++ OOP ENGINE    *\n";
    std::cout << "*   Demonstrating Classes, Inheritance, Abstraction, Polymorphism *\n";
    std::cout << "******************************************************************\n\n";

    // 1. DEMONSTRATE PLAYER CLASS
    std::cout << ">>> [1] PLAYER CLASS (Encapsulation & Data Abstraction)\n";
    Player p1(101, "Virat Kohli", "Batter", 1);
    Player p2(102, "Jasprit Bumrah", "Bowler", 1);
    Player p3(103, "Hardik Pandya", "All-rounder", 1);
    Player p4(104, "Rishabh Pant", "Wicket-keeper", 1);
    p1.display();
    p2.display();
    p3.display();
    p4.display();

    // 2. DEMONSTRATE TEAM CLASS
    std::cout << "\n>>> [2] TEAM CLASS (Object Composition & Containment)\n";
    Team teamIndia(1, "India");
    teamIndia.addPlayer(p1);
    teamIndia.addPlayer(p2);
    teamIndia.addPlayer(p3);
    teamIndia.addPlayer(p4);
    teamIndia.display();

    Team teamAustralia(2, "Australia");
    teamAustralia.addPlayer(Player(201, "Pat Cummins", "Bowler", 2));
    teamAustralia.addPlayer(Player(202, "Travis Head", "Batter", 2));
    teamAustralia.addPlayer(Player(203, "Glenn Maxwell", "All-rounder", 2));
    teamAustralia.addPlayer(Player(204, "Josh Inglis", "Wicket-keeper", 2));

    Team teamEngland(3, "England");
    teamEngland.addPlayer(Player(301, "Ben Stokes", "All-rounder", 3));
    teamEngland.addPlayer(Player(302, "Jos Buttler", "Wicket-keeper", 3));

    Team teamSouthAfrica(4, "South Africa");
    teamSouthAfrica.addPlayer(Player(401, "Kagiso Rabada", "Bowler", 4));
    teamSouthAfrica.addPlayer(Player(402, "Quinton de Kock", "Batter", 4));

    Team teamNewZealand(5, "New Zealand");
    teamNewZealand.addPlayer(Player(501, "Kane Williamson", "Batter", 5));
    teamNewZealand.addPlayer(Player(502, "Trent Boult", "Bowler", 5));

    // 3. DEMONSTRATE RUNTIME POLYMORPHISM & INHERITANCE IN MATCH CLASS
    std::cout << "\n>>> [3] MATCH FORMATS (Inheritance & Runtime Polymorphism)\n";
    std::cout << "Creating matches dynamically via Base Class Pointer 'Match*'...\n";

    std::vector<Match*> polyMatches;
    polyMatches.push_back(createMatch("T20", 1, teamIndia, teamAustralia));
    polyMatches.push_back(createMatch("ODI", 2, teamEngland, teamSouthAfrica));
    polyMatches.push_back(createMatch("Test", 3, teamIndia, teamEngland));

    for (Match* m : polyMatches) {
        std::cout << "  -> Format: " << m->getFormat()
                  << " | Max Overs: " << m->getMaxOvers()
                  << " | Rules: " << m->getFormatDescription() << "\n";
    }

    // Simulate Match 1 (T20): India vs Australia
    polyMatches[0]->setScores(192, 4, 20.0, 185, 7, 20.0);
    polyMatches[0]->calculateWinner();
    polyMatches[0]->displayResult();

    // Clean up polymorphic match pointers
    for (Match* m : polyMatches) delete m;
    polyMatches.clear();

    // 4. DEMONSTRATE TOURNAMENT CLASS (Round Robin Fixtures & Points Table)
    std::cout << "\n>>> [4] TOURNAMENT CLASS (Round Robin Fixtures & Standings)\n";
    Tournament worldCup(10, "ICC Champions Trophy 2026", "ODI");
    worldCup.addTeam(teamIndia);
    worldCup.addTeam(teamAustralia);
    worldCup.addTeam(teamEngland);
    worldCup.addTeam(teamSouthAfrica);

    std::cout << "Generating round-robin schedule for 4 teams...\n";
    worldCup.generateRoundRobinFixtures();
    worldCup.displayTournamentDetails();

    // Simulate Completed Matches
    std::cout << "\nSimulating match results and calculating ICC points table...\n";
    std::vector<MatchRecord> results;
    // Match 1: India (280) vs Australia (270) -> India wins
    MatchRecord m1; m1.teamAId = 1; m1.teamBId = 2; m1.scoreA = 280; m1.scoreB = 270; m1.winnerId = 1; m1.isTie = false; m1.isCompleted = true;
    results.push_back(m1);
    // Match 2: England (250) vs South Africa (250) -> Tie
    MatchRecord m2; m2.teamAId = 3; m2.teamBId = 4; m2.scoreA = 250; m2.scoreB = 250; m2.winnerId = 0; m2.isTie = true; m2.isCompleted = true;
    results.push_back(m2);
    // Match 3: India (310) vs England (240) -> India wins
    MatchRecord m3; m3.teamAId = 1; m3.teamBId = 3; m3.scoreA = 310; m3.scoreB = 240; m3.winnerId = 1; m3.isTie = false; m3.isCompleted = true;
    results.push_back(m3);
    // Match 4: Australia (295) vs South Africa (290) -> Australia wins
    MatchRecord m4; m4.teamAId = 2; m4.teamBId = 4; m4.scoreA = 295; m4.scoreB = 290; m4.winnerId = 2; m4.isTie = false; m4.isCompleted = true;
    results.push_back(m4);

    std::vector<TeamStanding> table = worldCup.calculatePointsTable(results);

    std::cout << "\n+------+-----------------------+--------+-----+------+------+--------+\n";
    std::cout << "| Rank | Team Name             | Played | Won | Lost | Tied | Points |\n";
    std::cout << "+------+-----------------------+--------+-----+------+------+--------+\n";
    for (const auto& row : table) {
        std::cout << "| " << std::left << std::setw(4) << row.rank << " | "
                  << std::left << std::setw(21) << row.teamName << " | "
                  << std::setw(6) << row.played << " | "
                  << std::setw(3) << row.won << " | "
                  << std::setw(4) << row.lost << " | "
                  << std::setw(4) << row.tied << " | "
                  << std::setw(6) << row.points << " |\n";
    }
    std::cout << "+------+-----------------------+--------+-----+------+------+--------+\n";
    std::cout << "\nPoints Table Rules Applied:\n";
    std::cout << "  - Win: 2 points | Tie: 1 point | Loss: 0 points\n";
    std::cout << "  - Sorted by: 1) Points, 2) Wins, 3) Team Name (Alphabetical)\n";
    std::cout << "\n[C++ OOP Engine Operational & Ready for Flask Integration]\n\n";
}

// ============================================================================
// MAIN ENTRY POINT
// ============================================================================

int main(int argc, char* argv[]) {
    // If no arguments or --demo, run interactive console demonstration
    if (argc < 2 || std::string(argv[1]) == "--demo") {
        runConsoleOOPDemo();
        return 0;
    }

    std::string command = argv[1];
    std::string jsonInput = "";

    // Read JSON payload from second argument or standard input
    if (argc >= 3) {
        jsonInput = argv[2];
    } else {
        std::string line;
        while (std::getline(std::cin, line)) {
            jsonInput += line;
        }
    }

    if (command == "--fixtures" || command == "-f") {
        handleGenerateFixtures(jsonInput);
    } else if (command == "--calculate-result" || command == "--result" || command == "-r") {
        handleCalculateResult(jsonInput);
    } else if (command == "--points-table" || command == "--standings" || command == "-p") {
        handlePointsTable(jsonInput);
    } else {
        std::cout << "{\"status\":\"error\",\"message\":\"Unknown command: " << command << "\"}" << std::endl;
        return 1;
    }

    return 0;
}
