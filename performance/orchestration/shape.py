# orchestration/shape.py
import time
import csv
import os
from locust import LoadTestShape


class InstrumentStepShape(LoadTestShape):
    stages = [
        {"name": "S1_5u", "duration": 300, "users": 5, "spawn_rate": 1},
        {"name": "S2_10u", "duration": 600, "users": 10, "spawn_rate": 1},
        {"name": "S3_20u", "duration": 900, "users": 20, "spawn_rate": 2},
        {"name": "S4_35u", "duration": 1200, "users": 35, "spawn_rate": 2},
        {"name": "S5_50u", "duration": 1500, "users": 50, "spawn_rate": 2},
    ]

    def __init__(self):
        super().__init__()
        self._stage_start = time.time()

    def tick(self):
        run_time = self.get_run_time()
        prev_end = 0
        for stage in self.stages:
            if prev_end <= run_time < stage["duration"]:
                self._maybe_write_timeline(stage, prev_end)
                return (stage["users"], stage["spawn_rate"])
            prev_end = stage["duration"]
        return None

    def _maybe_write_timeline(self, stage, start_offset):
        marker = f"{stage['name']}_written"
        if getattr(self, marker, False):
            return
        setattr(self, marker, True)
        os.makedirs("metrics_output", exist_ok=True)
        path = "metrics_output/stage_timeline.csv"
        new_file = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(["stage", "users", "start_ts", "end_ts"])
            start_ts = int((self._stage_start + start_offset) * 1000)
            end_ts = int((self._stage_start + stage["duration"]) * 1000)
            w.writerow([stage["name"], stage["users"], start_ts, end_ts])
