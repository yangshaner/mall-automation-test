#!/bin/sh
#stop_collect.sh - 停止采集
# 用法；sh stop_collect.sh [输出目录]

OUT_DIR=${1:-/opt/mall/performace_test/projects/locust-macrozheng-mall/temp}
INTERVAL=${interval:-5}

if [ ! -d "$OUT_DIR" ]; then
        echo "output dir does not exist: $OUT_DIR" >&2
        exit 1
fi

# 方式一：创建 .stop 标记，让采集循环优雅退出
touch "$OUT_DIR/.stop"
echo "created $OUT_DIR/.stop, waiting for collect script exit (about ${INTERVAL}s) ..."
sleep $((INTERVAL + 2))

# 方式二：按 PID 文件兜底 kill （防止脚本卡在 docker exec 里）
if [ -f "$OUT_DIR/collect.pids" ]; then
        while read -r pid; do
                [-n "$pid" ] && kill "$pid" 2>/dev/null
        done < "$OUT_DIR/collector.pids"
        rm -f "$OUT_DIR.collector.pids"
        echo "has cleaned PID file(s)"
fi

# 检查是否还有残留
REMAIN=$(ps -ef | grep -E "collect_(mysql|redis|docker)\.sh" | grep -v grep | wc -l)
if [ "$REMAIN" -gt 0 ]; then
        echo "[WARN] still has $REMAIN processes of collection, manual check: ps -ef | grep collect_" >&2
else
        echo "collections have stopped."
fi

echo ""
echo "==== collection output ===="
ls -lh "$OUT_DIR"/*.log 2>/dev/null