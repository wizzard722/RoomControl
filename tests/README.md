# RoomControl tests

Plain Python scripts that run RoomControl's backend on a bare Home Assistant
instance (no running Home Assistant, no test framework). Each prints
`PASS` / `FAIL` lines and ends with `ALL PASS`.

```bash
pip install homeassistant
python tests/run_all.py
```

Run a few: `python tests/run_all.py lux need`. Run one: `python tests/test_planner.py`.

They also run on GitHub (Actions → Tests) for every push and pull request.
