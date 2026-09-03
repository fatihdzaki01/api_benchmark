#!/bin/sh
# Benchmark API bertahap (headless) pakai Locust.
#
# Untuk tiap jumlah user: locust jalan -t <run_time> detik, hasilnya:
#   results/<prefix>_<users>_users.html          (laporan HTML penuh)
# CSV hanya disimpan sementara di /tmp buat deteksi batas (tidak masuk results).
# Di akhir, semua run diringkas jadi:
#   results/<prefix>_ringkasan_seconds.html      (tabel latensi dalam satuan second)
#
# Env:
#   LOCUST_HOST           target host, mis. http://api-single:8000 atau http://nginx:80
#   LOCUST_USERS_LIST     daftar jumlah user pisah koma, default "100,1000,10000"
#   LOCUST_RUN_TIME       durasi tiap run, default 5m
#   LOCUST_SPAWN_RATE     "auto" (= users/60, ramp ~1 menit) atau angka tetap
#   SCENARIO_PREFIX       prefix nama file, default "s1"
#   LOCUST_MAX_ERROR_PCT  stop kalau error agregat > nilai ini (%), default 10
#   LOCUST_MAX_P99_S      stop kalau p99 agregat > nilai ini (detik), default 60
#   RESULTS_DIR           folder hasil, default /app/results

set -u

HOST="${LOCUST_HOST:-}"
LIST="${LOCUST_USERS_LIST:-100,1000,10000}"
RUN_TIME="${LOCUST_RUN_TIME:-5m}"
SPAWN="${LOCUST_SPAWN_RATE:-auto}"
PREFIX="${SCENARIO_PREFIX:-s1}"
RESULTS_DIR="${RESULTS_DIR:-/app/results}"
MAX_ERR="${LOCUST_MAX_ERROR_PCT:-10}"
MAX_P99="${LOCUST_MAX_P99_S:-60}"

export LOCUST_MAX_ERROR_PCT="$MAX_ERR"
export LOCUST_MAX_P99_S="$MAX_P99"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
CSV_LIST=""

echo "=============================="
echo "  API BENCHMARK (headless)"
echo "=============================="
echo "Target        : ${HOST:-<KOSONG>}"
echo "Users list    : $LIST"
echo "Run time      : $RUN_TIME per run"
echo "Spawn rate    : $SPAWN  (auto = users/60/s)"
echo "Prefix        : $PREFIX"
echo "Stop jika     : error > ${MAX_ERR}%  ATAU  p99 > ${MAX_P99}s"
echo "Results dir   : $RESULTS_DIR"
echo

if [ -z "$HOST" ]; then
    echo "ERROR: env LOCUST_HOST tidak di-set." >&2
    exit 1
fi

mkdir -p "$RESULTS_DIR"

LIMIT=""
for USERS in $(echo "$LIST" | tr ',' ' '); do
    NAME="${PREFIX}_${USERS}_users"

    if [ "$SPAWN" = "auto" ]; then
        RATE=$((USERS / 60))
        [ "$RATE" -lt 1 ] && RATE=1
    else
        RATE="$SPAWN"
    fi

    echo
    echo "--------------------------------------------------"
    echo "  RUN $NAME | users=$USERS | spawn=${RATE}/s | $RUN_TIME"
    echo "--------------------------------------------------"

    locust -f /app/locustfile.py \
        --headless \
        -H "$HOST" \
        -u "$USERS" \
        -r "$RATE" \
        -t "$RUN_TIME" \
        --csv "$TMP_DIR/$NAME" \
        --html "$RESULTS_DIR/$NAME.html"

    CSV_LIST="$CSV_LIST $TMP_DIR/${NAME}_stats.csv"

    if python /app/make_summary.py check "$TMP_DIR/${NAME}_stats.csv"; then
        echo ">> $NAME: masih OK, lanjut ke user berikutnya."
    else
        LIMIT="$USERS"
        echo ">> BATAS KEMAMPUAN tercapai pada percobaan $NAME, hentikan ladder."
        break
    fi
done

echo
echo "======================================================"
echo "  MEMBUAT RINGKASAN (satuan second)"
echo "======================================================"
python /app/make_summary.py build "$RESULTS_DIR" "$PREFIX" $CSV_LIST

echo
if [ -n "$LIMIT" ]; then
    echo "RESULT: sistem masih OK sampai sebelum percobaan ${LIMIT} users (batas terdeteksi di ${LIMIT} users)."
else
    echo "RESULT: tidak ada yang jebol pada daftar users: $LIST"
fi
