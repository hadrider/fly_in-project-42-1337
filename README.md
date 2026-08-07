*This project has been created as part of the 42 curriculum by hadrider.*

---

## Description

**Fly-in** is a drone routing simulation system.  
Given a network of zones and a fleet of drones, it finds the optimal path from a start hub to an end hub and simulates all drones moving turn by turn, respecting zone capacities, connection capacities, and movement costs.

---

## Instructions

### Install dependencies
```bash
make install
```

### Run with colored visual output (default)
```bash
make run MAP=maps/map.txt
```

### Run with log output only (no colors)
```bash
make run-no-visual MAP=maps/map.txt
```

### Run with capacity info appended to each line
```bash
make run-capacity MAP=maps/map.txt
```

### Debug mode
```bash
make debug MAP=maps/map.txt
```

### Lint
```bash
make lint
```

### Clean caches
```bash
make clean
```

---

## Map file format

```
nb_drones: 3

start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]

connection: hub-roof1
connection: roof1-corridorA [max_link_capacity=2]
connection: corridorA-goal
```

**Zone types:**
- `normal` — 1 turn to enter (default)
- `restricted` — 2 turns to enter, drone is in transit during first turn
- `priority` — 1 turn, preferred in pathfinding tie-breaks
- `blocked` — cannot be entered

**Metadata:**
- `zone=<type>` — zone type (default: normal)
- `color=<name>` — terminal display color
- `max_drones=<n>` — max drones allowed simultaneously (default: 1)
- `max_link_capacity=<n>` — max drones on a connection per turn (default: 1)

---

## Algorithm

### Pathfinding — Dijkstra
- Uses zone move cost as edge weight
- Skips blocked zones entirely
- Priority zones win tie-breaks via a penalty value in the heap tuple
- Complexity: O((V + E) log V)
- No external graph libraries used — implemented from scratch

### Simulation — turn-based state machine
Each turn runs in 4 phases:
1. **Snapshot** — record current occupancy before any moves
2. **Validate** — check zone capacity and connection capacity for each intended move
3. **Apply** — execute all approved moves simultaneously
4. **Output** — format and display the turn

**Restricted zone transit:**  
Moving into a restricted zone takes 2 turns. On turn 1 the drone occupies the connection (IN_TRANSIT). On turn 2 it must arrive — it cannot wait on the connection.

**Conflict resolution:**  
Drones are processed in ID order. If a zone or connection is full, the drone waits (stays in place) until the next turn.

---

## Visual representation

The default output shows a colored terminal display for each turn:
- Zone names are colored by their `color` attribute
- Drone labels (D1, D2...) shown in cyan inside their current zone
- Occupancy shown as `[used/max]` — red if at capacity
- Connection usage shown as `used/max` — red if at capacity
- Final summary shows total turns, drones delivered, average turns per drone

Visual mode now also prints the plain movement log line after each rendered turn.
Use `--no-visual` to suppress colors and print only the log lines.

---

## Output format

Each turn outputs one line listing all drone movements:
```
D1-roof2
D1-corridorA D2-roof2
D1-goal D2-corridorA D3-roof2
D2-goal D3-corridorA
D3-goal
```

For drones in transit toward a restricted zone: `D1-hub-roof1`  
Drones that do not move are omitted from the line.

---

## Resources

- [Dijkstra's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Python dataclasses — docs.python.org](https://docs.python.org/3/library/dataclasses.html)
- [Python heapq — docs.python.org](https://docs.python.org/3/library/heapq.html)
- [ANSI escape codes](https://en.wikipedia.org/wiki/ANSI_escape_code)

**AI usage:**  
AI was used to help explain Python concepts (references, dataclasses, heapq internals) and to review code structure. All code was written and understood by the author. AI was not used to generate code that was copy-pasted without understanding.
