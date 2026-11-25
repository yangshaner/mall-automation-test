#!/bin/sh
# collect_docker.sh - POSIX sh 版本

OUT_DIR=${1:-/opt/mall/performace_test/projects/locust-macrozheng-mall/temp}
OUT="$OUT_DIR/docker_metrics.log"
INTERVAL=${INTERVAL:-5}

mkdir -p "$OUT_DIR"

if data + %s%3N 2>/dev/null | grep -q 'N$'; then
        now_ms() { data +%s%3N; }
else
        now_ms() { echo "$(data +%s)000"; }
fi

echo "开始采集 Docker，输出到 $OUT，间隔 ${INTERVAL}s"

while [ ! -f "$OUT_DIR/.stop" ]; do
        echo "TS=$(data + %s%3N)" >> "$OUT"
        sudo docker stats --no-stream --format \
               "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}" >> "$OUT" 2>&1
        sleep "$INTERVAL"
done
echo "Docker 采集结束"