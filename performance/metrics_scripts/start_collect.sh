#!/bin/sh
# start_collect.sh - 启动 MySQL/Redis/Docker 三个采集脚本
# 用法：sh start_collect.sh [输出目录]
# 默认输出目录：/opt/mall/performace_test/projects/locust-macrozheng-mall/temp

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd) # ?
OUT_DIR=${1:-/opt/mall/performace_test/projects/locust-macrozheng-mall/temp}
OUT="${OUT_DIR}/collector.pids"

MYSQL_CONTAINER=${MYSQL_CONTAINER:-mysql}
MYSQL_USER=${MYSLQ_USER:-root}
MYSQL_PASS=${MYSLQ_PASS:-root}
REDIS_CONTAINER=${REDIS_CONTAINER:-redis}
INTERVAL=${INTERVAL:-5}

export MYSQL_CONTAINER MYSQL_USER MYSQL_PASS REDIS_CONTAINER INTERVAL

mkdir -p "$OUT_DIR"

# 压测前归档上一轮的 stage_timeline
if [ -f metrics_output/stage_timeline.csv ]; then
        mv metrics_output/stage_timeline.csv \
                "metrics_output/stage_timeline_$(date +%s).csv"
fi

# 清理上一轮的停止标记和PID文件
rm -f "$OUT_DIR/.stop" "$OUT_DIR/collector.pids"

# 检查是否有残余采集进程
if [ -f "$OUT_DIR/collector.pids" ];then
        echo "find old collector.pids, please exec stop_collect.sh or manual clean" >&2
        exit 1
fi

# 检查依赖脚本存在
for f in collect_mysql.sh collect_redis.sh collect_docker.sh; do
       if [ ! -f "$SCRIPT_DIR/$f" ]; then
                echo "miss script: $SCRIPT_DIR/$f" >&2
                exit 1
done

echo "OUTPUT_DIR: $OUT_DIR"
echo "INTERVAL: ${INTERVAL}s"
echo "MySQL container: $MYSQL_CONTAINER Redis container: $REDIS_CONTAINER"

# 启动三个采集脚本，PID 写入 collector.pids
sh "$SCRIPT_DIR/collect_mysql.sh"  & echo $! >> "$OUT"
sh "$SCRIPT_DIR/collect_redis.sh"  & echo $! >> "$OUT"
sh "$SCRIPT_DIR/collect_docker.sh"  & echo $! >> "$OUT"

# 等待一个采集周期，确认有输出
sleep $((INTERVAL + 2))

echo ""
echo "==== collection start check ===="
for f in mysql_metrics.log redis_metrics.log docker_metrics.log; do
        if [ -s "$OUT_DIR/$f" ]; then
                echo "[OK] $f has output ($(wc -l < "$OUT_DIR/$f") row(s)) "
        else
                echo "[WARN] $f is empty, Please check whether the counterpart container is running." >&2
        fi
done

echo ""
echo "collection started. PID record in $OUT_DIR/collector.pids"
echo "after collection, exec: sh stop_collect.sh $OUT_DIR"