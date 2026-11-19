#ifndef TOURNAMENT_CPP
#define TOURNAMENT_CPP

#include "Match.cpp"
#include <vector>
#include <map>
#include <algorithm>
#include <iostream>
#include <sstream>

/**
 * Structure representing a team's standing in the Points Table
 */
struct TeamStanding {
    int rank;
    int teamId;
    std::string teamName;
    int played;
    int won;
    int lost;
    int tied;
    int points;

    TeamStanding()
        : rank(0), teamId(0), teamName(""), played(0), won(0), lost(0), tied(0), points(0) {}

    TeamStanding(int id, const std::string& name)
        : rank(0), teamId(id), teamName(name), played(0), won(0), lost(0), tied(0), points(0) {}

    std::string toJson() const {
        std::ostringstream ss;
        ss << "{"
           << "\"rank\":" << rank << ","
           << "\"team_id\":" << teamId << ","
           << "\"team_name\":\"" << teamName << "\","
           << "\"played\":" << played << ","
           << "\"won\":" << won << ","
           << "\"lost\":" << lost << ","
           << "\"tied\":" << tied << ","
           << "\"points\":" << points
           << "}";
        return ss.str();
    }
};

/**
 * Strict Points Table Comparator:
 * 1. Highest points
 * 2. Highest number of wins
 * 3. Team name alphabetically
 */
inline bool compareStandings(const TeamStanding& a, const TeamStanding& b) {
    if (a.points != b.points) {
        return a.points > b.points;
    }
    if (a.won != b.won) {
        return a.won > b.won;
    }
    return a.teamName < b.teamName;
}

/**
 * Data structure representing a match result passed for points calculation
 */
struct MatchRecord {
    int teamAId;
    int teamBId;
    int scoreA;
    int scoreB;
    int winnerId;
    bool isTie;
    bool isCompleted;

    MatchRecord() : teamAId(0), teamBId(0), scoreA(0), scoreB(0), winnerId(0), isTie(false), isCompleted(false) {}
};

/**
 * Fixture Item representation including Stage and Placeholders for Playoffs
 */
struct FixtureItem {
    int matchNumber;
    std::string stage; // "Round-Robin", "Semifinal 1", "Semifinal 2", "Final"
    std::string format;
    int teamAId;
    std::string teamAName;
    int teamBId;
    std::string teamBName;
    std::string placeholderA;
    std::string placeholderB;
    std::string status; // "Scheduled" or "Pending Qualification"
};

/**
 * Tournament Class
 * Manages tournament metadata, participating teams, fixture generation,
 * and points table compilation according to ICC cricket tournament rules.
 * Supports Round-Robin group stage + Playoffs (SF1: 1st vs 3rd, SF2: 2nd vs 4th, Final).
 */
class Tournament {
private:
    int id;
    std::string name;
    std::string format; // "T20", "ODI", "Test"
    std::vector<Team> teams;
    std::vector<Match*> matches;
    std::vector<FixtureItem> allFixtures;

    static std::string escapeJson(const std::string& input) {
        std::string out;
        for (char c : input) {
            if (c == '"') out += "\\\"";
            else if (c == '\\') out += "\\\\";
            else out += c;
        }
        return out;
    }

public:
    Tournament(int tId = 0, const std::string& tName = "", const std::string& tFormat = "T20")
        : id(tId), name(tName), format(tFormat) {}

    ~Tournament() {
        clearMatches();
    }

    void clearMatches() {
        for (Match* m : matches) {
            delete m;
        }
        matches.clear();
        allFixtures.clear();
    }

    // Getters and Setters
    int getId() const { return id; }
    void setId(int tId) { id = tId; }

    std::string getName() const { return name; }
    void setName(const std::string& tName) { name = tName; }

    std::string getFormat() const { return format; }
    void setFormat(const std::string& tFormat) { format = tFormat; }

    const std::vector<Team>& getTeams() const { return teams; }
    const std::vector<Match*>& getMatches() const { return matches; }
    const std::vector<FixtureItem>& getAllFixtures() const { return allFixtures; }

    // Add team to tournament
    bool addTeam(const Team& team) {
        // Prevent duplicate team registration
        for (const auto& t : teams) {
            if (t.getId() == team.getId()) {
                return false;
            }
        }
        teams.push_back(team);
        return true;
    }

    // Automatic Round-Robin Fixture Generation + Playoff Stage
    // Rules:
    // 1. Every tournament requires AT LEAST 5 TEAMS to ensure a competitive group stage & top-4 playoffs.
    // 2. Round-Robin: Every team plays every other team once.
    // 3. Semifinal 1: Position 1 vs Position 3 (Pending Qualification until all group matches finish).
    // 4. Semifinal 2: Position 2 vs Position 4 (Pending Qualification until all group matches finish).
    // 5. Final: Winner SF1 vs Winner SF2 (Pending Qualification until semifinals finish).
    bool generateRoundRobinFixtures() {
        if (teams.size() < 5) {
            return false;
        }

        clearMatches();
        int matchNumber = 1;
        size_t n = teams.size();

        // 1. Group Stage: Round Robin
        for (size_t i = 0; i < n; ++i) {
            for (size_t j = i + 1; j < n; ++j) {
                if (teams[i].getId() == teams[j].getId()) continue;

                Match* match = createMatch(format, matchNumber, teams[i], teams[j]);
                matches.push_back(match);

                FixtureItem item;
                item.matchNumber = matchNumber++;
                item.stage = "Round-Robin";
                item.format = format;
                item.teamAId = teams[i].getId();
                item.teamAName = teams[i].getName();
                item.teamBId = teams[j].getId();
                item.teamBName = teams[j].getName();
                item.placeholderA = "";
                item.placeholderB = "";
                item.status = "Scheduled";
                allFixtures.push_back(item);
            }
        }

        // 2. Playoff: Semifinal 1 (Position 1 vs Position 3)
        FixtureItem sf1;
        sf1.matchNumber = matchNumber++;
        sf1.stage = "Semifinal 1";
        sf1.format = format;
        sf1.teamAId = 0;
        sf1.teamAName = "Rank 1 (TBD)";
        sf1.teamBId = 0;
        sf1.teamBName = "Rank 3 (TBD)";
        sf1.placeholderA = "Rank 1 (TBD)";
        sf1.placeholderB = "Rank 3 (TBD)";
        sf1.status = "Pending Qualification";
        allFixtures.push_back(sf1);

        // 3. Playoff: Semifinal 2 (Position 2 vs Position 4)
        FixtureItem sf2;
        sf2.matchNumber = matchNumber++;
        sf2.stage = "Semifinal 2";
        sf2.format = format;
        sf2.teamAId = 0;
        sf2.teamAName = "Rank 2 (TBD)";
        sf2.teamBId = 0;
        sf2.teamBName = "Rank 4 (TBD)";
        sf2.placeholderA = "Rank 2 (TBD)";
        sf2.placeholderB = "Rank 4 (TBD)";
        sf2.status = "Pending Qualification";
        allFixtures.push_back(sf2);

        // 4. Playoff: Grand Final (Winner SF1 vs Winner SF2)
        FixtureItem fin;
        fin.matchNumber = matchNumber++;
        fin.stage = "Final";
        fin.format = format;
        fin.teamAId = 0;
        fin.teamAName = "Winner of SF1";
        fin.teamBId = 0;
        fin.teamBName = "Winner of SF2";
        fin.placeholderA = "Winner of SF1";
        fin.placeholderB = "Winner of SF2";
        fin.status = "Pending Qualification";
        allFixtures.push_back(fin);

        return true;
    }

    // Calculate Points Table
    // Rules:
    // Win = 2 points
    // Tie = 1 point for each team
    // Loss = 0 points
    std::vector<TeamStanding> calculatePointsTable(const std::vector<MatchRecord>& matchRecords) const {
        std::map<int, TeamStanding> standingsMap;

        // Initialize standings for all participating teams
        for (const auto& team : teams) {
            standingsMap[team.getId()] = TeamStanding(team.getId(), team.getName());
        }

        // Tally results for all completed matches
        for (const auto& match : matchRecords) {
            if (!match.isCompleted) continue;

            auto itA = standingsMap.find(match.teamAId);
            auto itB = standingsMap.find(match.teamBId);

            if (itA != standingsMap.end() && itB != standingsMap.end()) {
                TeamStanding& teamA = itA->second;
                TeamStanding& teamB = itB->second;

                teamA.played++;
                teamB.played++;

                if (match.isTie) {
                    teamA.tied++;
                    teamA.points += 1;
                    teamB.tied++;
                    teamB.points += 1;
                } else if (match.winnerId == match.teamAId) {
                    teamA.won++;
                    teamA.points += 2;
                    teamB.lost++;
                } else if (match.winnerId == match.teamBId) {
                    teamB.won++;
                    teamB.points += 2;
                    teamA.lost++;
                }
            }
        }

        // Convert map to vector
        std::vector<TeamStanding> standingsList;
        for (const auto& pair : standingsMap) {
            standingsList.push_back(pair.second);
        }

        // Sort by:
        // 1. Highest points
        // 2. Highest number of wins
        // 3. Team name alphabetically
        std::sort(standingsList.begin(), standingsList.end(), compareStandings);

        // Assign ordinal ranks
        for (size_t i = 0; i < standingsList.size(); ++i) {
            standingsList[i].rank = static_cast<int>(i + 1);
        }

        return standingsList;
    }

    // Display Tournament Details
    void displayTournamentDetails() const {
        std::cout << "\n============================================================\n";
        std::cout << "TOURNAMENT: " << name << " (ID: " << id << ")\n";
        std::cout << "Format: " << format << " | Participating Teams: " << teams.size() << "\n";
        std::cout << "------------------------------------------------------------\n";
        std::cout << "Teams:\n";
        for (const auto& t : teams) {
            std::cout << "  - [ID: " << t.getId() << "] " << t.getName() 
                      << " (" << t.getPlayerCount() << " players)\n";
        }
        std::cout << "------------------------------------------------------------\n";
        std::cout << "Generated Fixtures (" << allFixtures.size() << " total):\n";
        for (const auto& f : allFixtures) {
            std::cout << "  Match #" << f.matchNumber << " [" << f.stage << "]: "
                      << f.teamAName << " vs " << f.teamBName
                      << " (" << f.status << ")\n";
        }
        std::cout << "============================================================\n";
    }

    // JSON serialization of generated fixtures (including playoffs)
    std::string fixturesToJson() const {
        std::ostringstream ss;
        ss << "{"
           << "\"status\":\"success\","
           << "\"tournament_id\":" << id << ","
           << "\"tournament_name\":\"" << escapeJson(name) << "\","
           << "\"format\":\"" << escapeJson(format) << "\","
           << "\"total_fixtures\":" << allFixtures.size() << ","
           << "\"fixtures\":[";
        for (size_t i = 0; i < allFixtures.size(); ++i) {
            if (i > 0) ss << ",";
            const auto& f = allFixtures[i];
            ss << "{"
               << "\"match_number\":" << f.matchNumber << ","
               << "\"stage\":\"" << escapeJson(f.stage) << "\","
               << "\"format\":\"" << escapeJson(f.format) << "\","
               << "\"team_a_id\":" << f.teamAId << ","
               << "\"team_a_name\":\"" << escapeJson(f.teamAName) << "\","
               << "\"team_b_id\":" << f.teamBId << ","
               << "\"team_b_name\":\"" << escapeJson(f.teamBName) << "\","
               << "\"placeholder_a\":\"" << escapeJson(f.placeholderA) << "\","
               << "\"placeholder_b\":\"" << escapeJson(f.placeholderB) << "\","
               << "\"status\":\"" << escapeJson(f.status) << "\""
               << "}";
        }
        ss << "]}";
        return ss.str();
    }
};

#endif // TOURNAMENT_CPP
