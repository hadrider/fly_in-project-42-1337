# Fly-in: Drone Routing Simulation

A beginner-friendly Python 3.10+ implementation of the Fly-in drone routing project.

## Requirements

- Python 3.10+
- `flake8`
- `mypy`

## Project structure

```text
fly_in/
├── main.py
├── models.py
├── parser.py
├── pathfinder.py
├── simulator.py
├── colors.py
├── Makefile
├── requirements.txt
├── maps/
│   └── sample_map.txt
└── README.md
```

## Run

```bash
make install
make run
```

The default map is `maps/sample_map.txt`.

You can also run directly:

```bash
python3 main.py maps/sample_map.txt
```

## Other Make targets

```bash
make debug
make lint
make lint-strict
make clean
```

`make debug` runs Python's built-in debugger.

## Routing rules

- Normal zone: entry cost 1.
- Priority zone: entry cost 1.
- Restricted zone: entry cost 2.
- Blocked zone: unreachable.
- A zone's `max_drones` limits how many drones may occupy it.
- A connection's `max_link_capacity` limits how many drones may use it during a turn.
- A drone entering a restricted zone spends two turns travelling into it.
- A restricted-zone move cannot be paused halfway through.
- Start and end zones ignore their `max_drones` setting.
