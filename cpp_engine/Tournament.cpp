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
 * Tournament Class
 * Manages tournament metadata, participating teams, fixture generation,
 * and points table compilation according to ICC cricket tournament rules.
 */
class Tournament {
private:
    int id;
    std::string name;
    std::string format; // "T20", "ODI", "Test"
    std::vector<Team> teams;
    std::vector<Match*> matches;

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

    // Automatic Round-Robin Fixture Generation
    // Rules:
    // 1. Every team plays against every other team exactly once.
    // 2. Prevent a team from playing against itself.
    // 3. Prevent creating fixtures with fewer than 2 teams.
    bool generateRoundRobinFixtures() {
        if (teams.size() < 2) {
            return false;
        }

        clearMatches();
        int matchNumber = 1;
        size_t n = teams.size();

        for (size_t i = 0; i < n; ++i) {
            for (size_t j = i + 1; j < n; ++j) {
                // Ensure no team plays against itself
                if (teams[i].getId() == teams[j].getId()) continue;

                // Create polymorphic Match based on tournament format
                Match* match = createMatch(format, matchNumber++, teams[i], teams[j]);
                matches.push_back(match);
            }
        }
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
        std::cout << "Generated Fixtures (" << matches.size() << " total):\n";
        for (const auto* m : matches) {
            std::cout << "  Match #" << m->getMatchId() << ": "
                      << m->getTeamA().getName() << " vs " << m->getTeamB().getName()
                      << " [" << m->getFormat() << "]\n";
        }
        std::cout << "============================================================\n";
    }

    // JSON serialization of generated fixtures
    std::string fixturesToJson() const {
        std::ostringstream ss;
        ss << "{"
           << "\"status\":\"success\","
           << "\"tournament_id\":" << id << ","
           << "\"tournament_name\":\"" << escapeJson(name) << "\","
           << "\"format\":\"" << escapeJson(format) << "\","
           << "\"total_fixtures\":" << matches.size() << ","
           << "\"fixtures\":[";
        for (size_t i = 0; i < matches.size(); ++i) {
            if (i > 0) ss << ",";
            ss << "{"
               << "\"match_number\":" << matches[i]->getMatchId() << ","
               << "\"format\":\"" << escapeJson(matches[i]->getFormat()) << "\","
               << "\"team_a_id\":" << matches[i]->getTeamA().getId() << ","
               << "\"team_a_name\":\"" << escapeJson(matches[i]->getTeamA().getName()) << "\","
               << "\"team_b_id\":" << matches[i]->getTeamB().getId() << ","
               << "\"team_b_name\":\"" << escapeJson(matches[i]->getTeamB().getName()) << "\""
               << "}";
        }
        ss << "]}";
        return ss.str();
    }
};

#endif // TOURNAMENT_CPP
