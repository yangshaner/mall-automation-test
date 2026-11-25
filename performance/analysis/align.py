# analysis/align.py
import glob
import os.path
import re

import pandas as pd


def parse_mysql_log(path):
    rows = []
    current_ts = None
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            m = re.match(r"TS=(\d+)", line)
            if m:
                current_ts = int(m.group(1)) * 1000
                continue
            parts = line.split("\t")
            if len(parts) == 2 and current_ts:
                try:
                    rows.append({"ts": current_ts, "metric": parts[0], "value": int(parts[1])})
                except ValueError:
                    continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df.pivot_table(index="ts", columns="metric", values="value", aggfunc="mean").reset_index()


def parse_redis_log(path):
    rows = []
    current_ts = None
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            m = re.match(r"TS=(\d+)", line)
            if m:
                current_ts = int(m.group(1)) * 1000
                continue
            if ":" in line and current_ts:
                k, v = line.split(":", 1)
                try:
                    value = float(v.strip())
                except ValueError:
                    continue
                rows.append({"ts": current_ts, "metric": k.strip(), "value": value})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df.pivot_table(index="ts", columns="metric", values="value", aggfunc="mean").reset_index()


def find_latest_req_metrics(metrics_dir):
    pattern = os.path.join(metrics_dir, "req_metrics_*.csv")
    files = glob.glob(pattern)
    if not files:
        fixed = os.path.join(metrics_dir, "req_metrics.csv")
        return fixed if os.path.exists(fixed) else None

    return max(files, key=os.path.getmtime)



def _coerce_ts_column(df, cols):
    df = df.copy()
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    before = len(df)
    df = df.dropna(subset=cols)
    after = len(df)
    if after < before:
        print(f"[align] discard {before - after} rows with invalid timestamp")
    for c in cols:
        df[c] = df[c].astype("int64")
    return df


def _load_or_build_stages(metrics_dir, req):
    path = os.path.join(metrics_dir, "stage_timeline.csv")
    if os.path.exists(path):
        try:
            stages = pd.read_csv(path)
            stages = _coerce_ts_column(stages, ["start_ts", "end_ts"])

            if not stages.empty:
                return stages
        except Exception:
            pass

    ts_col = pd.to_numeric(req["ts"], errors="coerce").dropna()
    if ts_col.empty:
        return pd.DataFrame()
    return pd.DataFrame([{
        "stage": "ALL",
        "start_ts": int(ts_col.min()),
        "end_ts": int(ts_col.max()) + 1,
    }])


def build_aligned_report(metrics_dir="metrics_output"):
    req_path = find_latest_req_metrics(metrics_dir)
    if not req_path:
        print(f"[analysis skip] no req_metrics_*.csv under {metrics_dir}, "
              f"pressure test may not have run or terminated early.")
        return None

    try:
        req = pd.read_csv(req_path)
    except pd.errors.EmptyDataError:
        print(f"[analysis skip] {req_path} is empty, no request was recorded.")
        return None

    req = _coerce_ts_column(req, ["ts"])
    if req.empty:
        print("[analysis skip] req_metrics is empty.")
        return None

    req["success"] = req["success"].map(
        {True: True, False: False, "True": True, "False": False}
    ).fillna(False).astype(bool)

    stages = _load_or_build_stages(metrics_dir, req)
    if stages.empty:
        print("[analysis skip] could not derive stage info.")
        return None

    def tag_stage(ts):
        for _, s in stages.iterrows():
            if s["start_ts"] <= ts < s["end_ts"]:
                return s["stage"]
        return "UNKNOWN"

    req["stage"] = req["ts"].apply(tag_stage)

    is_probe = req["api_name"].astype(str).str.startswith("PROBE_")
    probe = req[is_probe]
    req = req[~is_probe]

    summary = req.groupby(["stage", "api_name"]).agg(
        count=("ts", "size"),
        p95_ms=("response_time_ms", lambda x: x.quantile(.95)),
        p99_ms=("response_time_ms", lambda x: x.quantile(.99)),
        fail_rate=("success", lambda x: 1 - x.mean()),
    ).reset_index()


    mysql_df = pd.DataFrame()
    redis_df = pd.DataFrame()
    mysql_path = os.path.join(metrics_dir, "mysql_metrics.log")
    redis_path = os.path.join(metrics_dir, "redis_metrics.log")

    if os.path.exists(mysql_path):
        mysql_df = parse_mysql_log(mysql_path)
    if os.path.exists(redis_path):
        redis_df = parse_redis_log(redis_path)

    def stage_middleware(df, prefix):
        if df is None or df.empty:
            return pd.DataFrame()
        df = _coerce_ts_column(df, ["ts"])
        df["stage"] = df["ts"].apply(tag_stage)
        num_cols = [c for c in df.columns if c not in ("ts", "stage")]
        for c in num_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        agg = df.groupby("stage")[num_cols].mean().reset_index()
        agg.columns = ["stage"] + [f"{prefix}_{c}" for c in num_cols]
        return agg

    report = summary
    for df, prefix in ((mysql_df, "mysql"), (redis_df, "redis")):
        agg = stage_middleware(df, prefix)
        if not agg.empty:
            report = report.merge(agg, on="stage", how="left")

    out = os.path.join(metrics_dir, "aligned_report.csv")
    report.to_csv(out, index=False)
    print(f"[analysis] report saved to {out}")

    if not probe.empty:
        probe_path = os.path.join(metrics_dir, "probe_report.csv")
        probe_summary = probe.groupby(["stage", "api_name"]).agg(
            count=("ts", "size"),
            p95_ms=("response_time_ms", lambda x: x.quantile(.95)),
            fail_rate=("success", lambda x: 1 - x.mean()),
            failure_reason=("failure_reason", lambda x: (x.dropna().iloc[0] if not x.dropna().empty else "")),
        ).reset_index()
        probe_summary.to_csv(probe_path, index=False)
        print(f"[analysis] probe report saved to {probe_path}")
        print(probe_summary.to_string())
    return report


if __name__ == "__main__":
    build_aligned_report()
