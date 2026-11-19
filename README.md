# 🏏 Cricket Tournament Management System

A full-stack, Object-Oriented Cricket Tournament Management System built using **C++ (OOP)** for core cricket calculations, **Python Flask** for REST APIs, **SQLite** for database storage, and **HTML/CSS/JavaScript** for the responsive user interface.

---

## 📌 Project Architecture

```text
Frontend (HTML / CSS / JS)
          │  (HTTP / Fetch API)
          ▼
Python Flask Backend (app.py)
          │  (Subprocess JSON)
          ▼
C++ OOP Engine (engine.exe)
          │  (SQL Queries)
          ▼
SQLite Database (cricket.db)
```

---

## 💡 C++ OOP Concepts Used & Why We Used Them

Here is a clear, concise breakdown of every Object-Oriented Programming (OOP) concept implemented in our C++ engine:

---

### 1. Encapsulation
* **Definition:** Binding data (variables) and methods (functions) into a single unit (class) while restricting direct outside access to data using access specifiers (`private`).
* **Where Used:** `Player.cpp` and `Team.cpp`
* **Why We Used It:** To protect sensitive entity data such as `player_id`, `player_name`, `player_role`, and `team_id` from unauthorized direct modification, ensuring values are only read or updated through verified public getters and setters.

---

### 2. Abstraction
* **Definition:** Hiding internal complex background implementation and showing only essential features to the outside world using abstract classes and pure virtual functions (`= 0`).
* **Where Used:** `Match.cpp` (Abstract Base Class `Match`)
* **Why We Used It:** A general "cricket match" does not exist without a specific format (e.g., T20, ODI, Test). Abstraction ensures a base match template cannot be instantiated directly, while standardizing the interface (`getMaxOvers()`, `getFormatDescription()`) for all match types.

---

### 3. Inheritance
* **Definition:** Mechanism where a child class acquires the properties and behaviors of a parent class, promoting code reusability.
* **Where Used:** `Match.cpp` (`T20Match`, `ODIMatch`, and `TestMatch` derive from `Match`)
* **Why We Used It:** To avoid writing duplicate logic for scores, winner determination, and JSON generation across different formats. All derived match types automatically inherit the shared match logic from `Match` and only add their format-specific rules (20 overs, 50 overs, or multi-day).

---

### 4. Runtime Polymorphism (Dynamic Binding)
* **Definition:** Resolving a function call at runtime rather than compile time based on the actual object being pointed to, achieved via `virtual` functions and base class pointers (`Match*`).
* **Where Used:** Factory function `createMatch()` and `main.cpp`
* **Why We Used It:** Because the match format is chosen dynamically by the user at runtime in the web UI. A single base pointer `Match*` can represent any match format and execute the correct overridden methods (`getMaxOvers()`, `getFormat()`) without hardcoded conditional logic.

---

### 5. Object Composition ("Has-A" Relationship)
* **Definition:** Designing a complex object by combining other simpler objects as members, where the lifetime of the contained objects is tied to the parent object.
* **Where Used:** `Team.cpp` (Team has a list of `Player`s) and `Tournament.cpp` (Tournament has a list of `Team`s)
* **Why We Used It:** A cricket team naturally contains players, and a tournament naturally contains teams. Composition accurately models this real-world relationship using `std::vector<Player>` inside `Team` and `std::vector<Team>` inside `Tournament`.

---

### 6. Constructors & Destructors
* **Definition:** Special member functions called automatically when an object is created (to initialize data members) and destroyed (to release allocated resources).
* **Where Used:** All C++ classes (`Player`, `Team`, `Match`, `Tournament`)
* **Why We Used It:** Member initializer lists in constructors guarantee that entities always start with valid IDs and names. A virtual destructor in `Match` prevents memory leaks when deleting derived match objects through base pointers.

---

## 📂 Project Structure

```text
opps/
├── cpp_engine/
│   ├── Player.cpp          # Player entity (Encapsulation)
│   ├── Team.cpp            # Team entity (Composition)
│   ├── Match.cpp           # Match hierarchy (Abstraction, Inheritance, Polymorphism)
│   ├── Tournament.cpp      # Tournament entity (Round-robin scheduling & Points Table)
│   ├── main.cpp            # Engine entry point & JSON communication
│   └── engine.exe          # Compiled C++ executable
│
├── backend/
│   ├── app.py              # Flask server, REST API & subprocess handler
│   └── database.py         # SQLite schema & database operations
│
├── frontend/
│   ├── index.html          # Clean Single Page Dashboard UI
│   ├── style.css           # Styling and responsive design
│   └── script.js           # Client-side API caller & DOM handler
│
├── database/
│   └── cricket.db          # Relational SQLite database
│
├── requirements.txt        # Python dependencies (Flask)
└── README.md               # Project documentation
```

---

## 🏆 Points Table & Cricket Business Logic

* **Round-Robin Fixtures:** For $N$ teams, the C++ engine generates $N(N-1)/2$ unique matches ensuring no team plays against itself.
* **Points Rules:**
  * **Win:** 2 points
  * **Tie:** 1 point each
  * **Loss:** 0 points
* **Tie-Breaker Hierarchy:**
  1. Highest total points
  2. Highest number of wins
  3. Team name alphabetically

---

## 🚀 How to Run the Project

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Compile the C++ Engine
```powershell
cd cpp_engine
g++ -std=c++11 -O2 Player.cpp Team.cpp Match.cpp Tournament.cpp main.cpp -o engine.exe
cd ..
```

*(Optional: Test the standalone C++ OOP demo by running `.\cpp_engine\engine.exe --demo`)*

### 3. Start the Flask Backend
```powershell
python backend\app.py
```

### 4. Open in Browser
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**
