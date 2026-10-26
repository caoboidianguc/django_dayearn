#!/usr/bin/env bash
set -o errexit

if [ -f "db.sqlite3.gz.b64" ]; then
    python -c "import base64, gzip; open('db.sqlite3','wb').write(gzip.decompress(base64.b64decode(open('db.sqlite3.gz.b64','rb').read())))"
fi

if [ -f "media.tar.gz.b64" ]; then
    python -c "import base64, io, tarfile; tarfile.open(fileobj=io.BytesIO(base64.b64decode(open('media.tar.gz.b64','rb').read())), mode='r:gz').extractall('.')"
fi

DISK_DIR="${RENDER_DISK_PATH:-/var/data}"

if [ -d "$DISK_DIR" ]; then
    mkdir -p "$DISK_DIR/media"
    NEED_SEED=$(python - "$DISK_DIR/db.sqlite3" << 'PYEOF'
import os, sqlite3, sys
p = sys.argv[1]
if not os.path.exists(p) or os.path.getsize(p) < 100000:
    print("1")
    sys.exit(0)
try:
    conn = sqlite3.connect(p)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ledger_khach")
    cnt = c.fetchone()[0]
    conn.close()
    print("0" if cnt > 0 else "1")
except Exception:
    print("1")
PYEOF
)
    if [ "$NEED_SEED" = "1" ]; then
        cp -f db.sqlite3 "$DISK_DIR/db.sqlite3"
    fi
    cp -rn media/* "$DISK_DIR/media/" 2>/dev/null || true
fi

python manage.py migrate --noinput
exec gunicorn dayearn.wsgi:application --bind 0.0.0.0:${PORT:-8000}
