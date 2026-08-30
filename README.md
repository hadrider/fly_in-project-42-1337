*This project has been created as part of the 42 curriculum by hadrider.*

# Fly-in

## Description

Fly-in simulates drones traveling through a network of zones (hubs) linked by
connections, from a `start_hub` to an `end_hub`. Zones and connections have
limited capacity, and some zone types cost extra turns to cross. The program
parses a custom map format, builds the graph by hand (no `networkx` or
similar library), finds paths for the drones, and simulates their movement
turn by turn without ever violating a capacity constraint.

## Instructions

```sh
make install                   # pip install -r requirements.txt
make run                       # runs main.py on maps/map.txt
make run MAP=maps/my_map.txt   # runs on a custom map
make lint                      # flake8 + mypy
```

Or directly: `python3 main.py maps/map.txt` (defaults to `maps/map.txt` if no
argument is given).

**Map format:**

```
nb_drones: <number>
start_hub: <name> <x> <y> [zone=<type> color=<color> max_drones=<n>]
hub:       <name> <x> <y> [zone=<type> color=<color> max_drones=<n>]
end_hub:   <name> <x> <y> [zone=<type> color=<color> max_drones=<n>]
connection: <zone1>-<zone2> [max_link_capacity=<n>]
```

`zone` defaults to `normal` (also: `restricted`, `priority`, `blocked`);
`max_drones` and `max_link_capacity` default to `1`.

## Algorithm Explanation

- **Graph** (`pathfinder.py`): a hand-built adjacency list from the parsed
  `Connection` objects.
- **Pathfinding**: a custom Dijkstra-style search run backward from
  `end_hub`, where entering a zone costs `1` (normal), `2` (restricted, i.e.
  takes an extra turn), `0.9` (priority, so it's preferred), or `∞`
  (blocked, never traversable). `find_paths` collects up to *k* equal-cost
  optimal paths, and `main.py` spreads drones across them so they don't all
  queue on a single route.
- **Simulation** (`simulator.py`): each turn, in-flight drones (mid-crossing
  a restricted zone) are advanced first, then waiting drones try to step to
  their next zone. A move only succeeds if the destination zone has free
  capacity and the connection has free capacity for that turn; otherwise the
  drone waits and retries next turn. This is how zone/link conflicts are
  resolved without ever exceeding a declared capacity.

## Visual Representation

`visualizer.py` opens a Pygame window that replays the simulation: zones are
drawn as circles colored per their `color=` metadata (start/end larger),
connections as lines between them, and drones as labeled tokens animated
turn by turn — a drone crossing a restricted (2-turn) zone is shown mid-link
while in flight. Zoom (scroll) and pan (drag) are supported, and `SPACE`
starts/restarts the replay. This makes bottlenecks and multi-turn crossings
immediately visible, which is much harder to read from plain text output.

## Example

`maps/map.txt`:

```
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]
connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

`python3 main.py maps/map.txt` outputs:

```
Turn 1: D1-waypoint1
Turn 2: D1-waypoint2 D2-waypoint1
Turn 3: D1-goal D2-waypoint2
Turn 4: D2-goal
```

Since every zone/connection has the default capacity of `1`, the two drones
queue one hub apart along the single path.

## Resources

- [Dijkstra's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Pygame documentation](https://www.pygame.org/docs/)
- [`webcolors` documentation](https://webcolors.readthedocs.io/)


### **AI usage:**

AI was used for boilerplate/type-annotation
suggestions, style/lint fixes, and drafting this README. Algorithm design and
final code decisions were made by the author.