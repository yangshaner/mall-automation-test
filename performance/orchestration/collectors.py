# orchestration/collectors.py

import logging
import os
import signal
import subprocess


from performance.config import Config

logger = logging.getLogger(__name__)



MYSQL_SCRIPT = r"""
which mysql >/dev/null 2>&1 || exit 0
# Cannot pass -p with an empty password, otherwise mysql waits for interactive input and the child process hangs
if [ -n "$MYSQL_PASS" ]; then MP="-p$MYSQL_PASS"; else MP=""; fi
: > {mysql_log}
while true; do
    ts=$(date +%s)
    printf 'TS=%s\n' "$ts" >> {mysql_log}
    mysql -u"$MYSQL_USER" $MP -P"$MYSQL_PORT" -N -e \
        "SHOW GLOBAL STATUS WHERE Variable_name IN (
            'Threads_connected','Threads_running',
            'Innodb_buffer_pool_read_requests','Innodb_buffer_pool_reads',
            'Slow_queries','Queries'
        );" >> {mysql_log} 2>&1
    sleep 5
done
"""

REDIS_SCRIPT = r"""
which redis-cli >/dev/null 2>&1 || exit 0
: > {redis_log}
while true; do
    ts=$(date +%s)
    printf 'TS=%s\n' "$ts" >> {redis_log}
    redis-cli -h"${{REDIS_ADDR%%:*}}" -p"${{REDIS_ADDR##*:}}" info stats | \
        grep -E '^(keyspace_hits|keyspace_misses|evicted_keys|instantaneous_ops_per_sec):' >> {redis_log}
    redis-cli -h"${{REDIS_ADDR%%:*}}" -p"${{REDIS_ADDR##*:}}" info memory | \
        grep -E '^(used_memory|used_memory_human|maxmemory):' >> {redis_log}
    sleep 5
done
"""


class MiddlewareCollector:

    def __init__(self, output_dir="metrics_output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.procs = []
        self._alive = True

    def _env(self):
        env = os.environ.copy()
        env["MYSQL_USER"] = Config.MYSQL_USER
        env["MYSQL_PASS"] = Config.MYSQL_PASS
        env["MYSQL_PORT"] = str(Config.MYSQL_PORT)
        env["REDIS_ADDR"] = Config.REDIS_ADDR
        return env


    def start(self):
        if os.name != "posix":
            logger.warning("[middleware] non-POSIX platform, skip MySQL/Redis collection.")
            return

        sh_bin = self._locate_sh()
        if not sh_bin:
            logger.warning("[middleware] sh not found, skip MySQL/Redis collection.")
            return

        mysql_log = os.path.join(self.output_dir, "mysql_metrics.log")
        redis_log = os.path.join(self.output_dir, "redis_metrics.log")

        env = self._env()
        self.procs.append(subprocess.Popen(
            [sh_bin, "-c", MYSQL_SCRIPT.format(mysql_log=mysql_log, redis_log=redis_log)],
            env=env,
            stdout=subprocess.DEVNULL,
        ))
        self.procs.append(subprocess.Popen(
            [sh_bin, "-c", REDIS_SCRIPT.format(mysql_log=mysql_log, redis_log=redis_log)],
            env=env,
            stdout=subprocess.DEVNULL,
        ))


        signal.signal(signal.SIGTERM, self._sigterm_handler)
        logger.info(f"[middleware] collector started, mysql log -> {mysql_log}, redis log -> {redis_log}")

    @staticmethod
    def _locate_sh():
        for candidate in ("/bin/sh", "/usr/bin/sh"):
            if os.path.exists(candidate):
                return candidate
        try:
            return subprocess.check_output(["which", "sh"], text=True).strip() or None
        except Exception:
            return None

    def _sigterm_handler(self, signum, frame):
        self._alive = False

    def poll_alive(self):
        for i, p in enumerate(self.procs):
            if p.poll() is not None:
                logger.warning(f"[middleware] sub-proc[{i}] pid={p.pid} exited with code {p.returncode}, "
                               f"log file may be incomplete.")


    def stop(self):
        for p in self.procs:
            if p.poll() is not None:
                continue
            try:
                p.terminate()
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    p.kill()
                    p.wait(timeout=2)
                except Exception:
                    pass
        self.procs.clear()
        logger.info("[middleware] collector stopped.")



_collector = None


def start_middleware_collector(output_dir="metrics_output"):
    global _collector
    if _collector is not None:
        return _collector
    _collector = MiddlewareCollector(output_dir)
    _collector.start()
    return _collector


def stop_middleware_collector():
    global _collector
    if _collector is not None:
        _collector.stop()
        _collector = None
