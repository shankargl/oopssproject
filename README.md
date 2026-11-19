# 🏏 Cricket Tournament Management System

A full-stack, Object-Oriented **Cricket Tournament Management System** combining high-performance **C++ (OOP)** for core cricket logic, **Python Flask** for REST APIs, **SQLite** for relational persistence, and **HTML5, CSS3, & Vanilla JavaScript** for a responsive user dashboard.

---

## 1. Project Folder Structure

The project strictly follows the requested layout:

```text
CricketManagement/
│
├── cpp_engine/
│   ├── Player.cpp          # Player entity (encapsulation, constructors, getters/setters)
│   ├── Team.cpp            # Team entity (composition of Player objects, squad management)
│   ├── Match.cpp           # Abstract base Match & derived classes (T20, ODI, Test polymorphism)
│   ├── Tournament.cpp      # Tournament entity (round-robin scheduling & ICC points table)
│   ├── main.cpp            # Engine entry point, CLI interface, and JSON data parser
│   └── engine.exe          # Compiled single C++ executable
│
├── backend/
│   ├── app.py              # Flask server, API endpoints, C++ subprocess runner
│   └── database.py         # SQLite schema, tables creation, and relational queries
│
├── frontend/
│   ├── index.html          # Modern dashboard UI (Teams, Players, Tourneys, Fixtures, Table)
│   ├── style.css           # Custom responsive styles, badges, modals, and stadium theme
│   └── script.js           # Vanilla JS controller with Fetch API and modal handling
│
├── database/
│   └── cricket.db          # SQLite relational database
│
├── requirements.txt        # Python backend dependencies
└── README.md               # Complete setup, compilation, and execution documentation
```

---

## 2. Architecture & OOP Implementation

```text
Frontend (HTML / CSS / JavaScript)
               ↓  [Fetch JSON API]
Flask Backend (app.py)
               ↓  [Subprocess CLI Arguments & JSON Stdin]
C++ OOP Engine (engine.exe)
               ↓  [Round Robin & Standings Logic]
SQLite Database (cricket.db via database.py)
```

### C++ Object-Oriented Principles Applied
1. **Encapsulation & Data Abstraction (`Player.cpp`, `Team.cpp`)**:
   - Private members (`id`, `name`, `role`, `teamId`).
   - Strict public getters and setters to protect internal state.
   - Self-contained JSON serialization methods.
2. **Object Composition (`Team.cpp`, `Tournament.cpp`)**:
   - `Team` has-a collection of `Player` objects (`std::vector<Player>`).
   - `Tournament` has-a collection of `Team` objects and `Match` pointers.
3. **Inheritance & Runtime Polymorphism (`Match.cpp`)**:
   - Abstract Base Class `Match` defines pure virtual methods:
     - `virtual std::string getFormat() const = 0;`
     - `virtual int getMaxOvers() const = 0;`
     - `virtual std::string getFormatDescription() const = 0;`
     - `virtual void calculateWinner();`
   - Concrete Subclasses:
     - `T20Match`: 20 overs per innings, powerplay constraints.
     - `ODIMatch`: 50 overs per innings, 3 powerplay phases.
     - `TestMatch`: Traditional multi-day format with red ball.
   - Dynamic Binding: Factory function `createMatch()` instantiates derived formats via base class pointers `Match*`.
4. **Round-Robin Scheduling Algorithm (`Tournament.cpp`)**:
   - Automated fixture generator: for $N$ teams, generates $N(N-1)/2$ unique matches.
   - Prevents a team from playing itself.
   - Enforces a minimum of 2 teams per tournament.
5. **ICC Points Table Calculation & Ranking (`Tournament.cpp`)**:
   - Win = 2 points, Tie = 1 point, Loss = 0 points.
   - Strict 3-tier tiebreaker sorting:
     1. Highest points descending
     2. Highest number of wins descending
     3. Team name alphabetically ascending

---

## 3. Prerequisites & Installation

### Requirements
- **Windows 10 / 11** with PowerShell
- **Python 3.10+** (tested on Python 3.12)
- **MinGW / GCC C++ Compiler** (`g++`)

### Step 1: Install Python Dependencies
Open PowerShell or VS Code terminal in the project directory:

```powershell
cd "CricketManagement"
pip install -r requirements.txt
```

---

## 4. Compiling the C++ OOP Engine

Link all C++ source files into a single standalone executable `engine.exe`:

```powershell
cd cpp_engine
g++ -std=c++11 -O2 Player.cpp Team.cpp Match.cpp Tournament.cpp main.cpp -o engine.exe
cd ..
```

### Standalone Console OOP Demonstration (Optional)
To verify the C++ engine logic directly in your terminal, run:

```powershell
.\cpp_engine\engine.exe --demo
```
This prints the complete OOP demonstration including class instantiation, polymorphic match resolution, round-robin fixtures, and formatted ASCII points table!

---

## 5. Running the Flask Backend

From the `CricketManagement` directory, start the server:

```powershell
python backend/app.py
```

You will see:
```text
============================================================
CRICKET TOURNAMENT MANAGEMENT SYSTEM - BACKEND READY
Server running at: http://127.0.0.1:5000
C++ Engine Binary: ...\CricketManagement\cpp_engine\engine.exe (Exists: True)
============================================================
```

---

## 6. Accessing the Application in the Browser

Open your web browser (Chrome, Edge, Firefox) and navigate to:

👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 7. Feature Walkthrough & Demonstration Guide

1. **Quick Demo Setup**:
   - Click the **"⚡ Quick Demo Data"** button in the header.
   - This automatically creates 4 international teams (India, Australia, England, South Africa) with squads, and seeds an upcoming tournament with 6 round-robin fixtures!
2. **Team Management**:
   - Navigate to the **Teams** tab.
   - Add new teams or delete existing ones.
3. **Player Management**:
   - Navigate to the **Players** tab.
   - Add a player with name, role (Batter, Bowler, All-rounder, Wicket-keeper), and assign to a team.
   - Filter roster team-wise using the dropdown.
4. **Tournament Creation**:
   - Navigate to the **Tournaments** tab.
   - Give the tournament a name, select a format (T20, ODI, Test), and check at least 2 teams.
   - Click **Create Tournament & Generate Fixtures**. The C++ engine generates the round-robin schedule instantly!
5. **Fixtures & Score Entry**:
   - Navigate to the **Fixtures & Matches** tab.
   - Select the tournament from the dropdown.
   - Click **"🎯 Enter Score"** on any match card.
   - Input runs, wickets, and overs for both innings.
   - Click **"Calculate Result via C++ Engine"**. The C++ engine computes the winner or tie, victory margin, and updates the database.
6. **Points Table**:
   - Navigate to the **Points Table** tab.
   - Select the tournament to view updated rankings computed by the C++ engine according to ICC points rules (Win: 2 pts, Tie: 1 pt, Loss: 0 pts).
