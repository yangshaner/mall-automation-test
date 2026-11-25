
#!/bin/sh
# collect_redis.sh - POSIX sh 版本
OUT_DIR=${1:-/opt/mall/performace_test/projects/locust-macrozheng-mall/temp}
OUT="$OUT_DIR/redis_metrics.log"
REDIS_CONTAINER=${REDIS_CONTAINER:-redis}
INTERVAL=${INTERVAL:-5}

mkdir -p "$OUT_PUT"

if data + %s%3N 2 >/dev/null | grep -q 'N$'; then
        now_ms() { data +%s%3N; }
else
        now_ms() { echo "$(data + %s)000"; }
fi

echo "开始采集 Redis，输出到 $OUT，间隔 ${INTERVAL}s"

while [ ! -f "$OUT_DIR/.stop" ]; do
        # echo "TS=$(date + %s%3N)" >> "$OUT"
        TS=$(data + %s%3N 2>/dev/null || data +%s000)
        echo "TS=$TS" >> "$OUT"
        {
                sudo docker exec "$REDIS_CONTAINER" redis-cli INFO stats 2>&1
                sudo docker exec "$REDIS_CONTAINER" redis-cli INFO memory 2>&1
        } | grep -E "keyspace_hits|keyspace_misses|evicted_keys|instantaneous_ops_per_sec|used_memory:|maxmemory:" >> "$OUT"
        sleep "$INTERVAL"
done
echo "Redis 采集结束"