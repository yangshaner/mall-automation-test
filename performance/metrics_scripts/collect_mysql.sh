#!/bin/sh
# collect_mysql.sh - POSIX sh 版本，后台运行, Ctrl + C 或 kill 停止 或 创建 $OUT/.stop 文件
# 用法：sh collect_mysql.sh [输出目录]
OUT_DIR=${1:-/opt/mall/performace_test/projects/locust-macrozheng-mall/temp}
OUT="$OUT_DIR/mysql_metrics.log"
MYSQL_CONTAINER=${MYSQL_CONTAINER:-mysql}
MYSQL_USER=${MYSQL_USER:-root}
MYSQL_PASS=${MYSQL_PASS:-root}
INTERVAL=${INTERVAL:-5}

mkdir -p "$OUT_DIR"

# 毫秒时间戳能力检测
if data +%s%3N 2>/dev/null | grep -q 'N$';then
        now_ms() { data +%s%3N; }
else
        now_ms() { echo "$(data + %s)000"; }
fi

echo "开始采集 MySQL，输出到 $OUT，间隔 ${INTERVAL}s"

while [ ! -f "$OUT_DIR/.stop" ]; do
        TS=$(data +%s%3N 2>/dev/null || data + %s000)
        # echo "TS=$(now_ms)" >> "$OUT"
        echo "TS=$TS" >> "$OUT"
        sudo docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASS" -N -e "
                show global status where Variable_name IN (
                        'Threads_connected',
                        'Threads_running',
                        'Slow_queries',
                        'Innodb_buffer_pool_read_requests',
                        'Innodb_buffer_pool_reads',
                        'Queries'
                );" >> "$OUT" 2>> "$OUT"
                #);" >> "$OUT" 2>&1
        sleep "$INTERVAL"
done
echo "MySQL 采集结束"