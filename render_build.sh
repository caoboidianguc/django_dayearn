#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

if [ -f "db.sqlite3.gz.b64" ]; then
    python -c "import base64, gzip; open('db.sqlite3','wb').write(gzip.decompress(base64.b64decode(open('db.sqlite3.gz.b64','rb').read())))"
fi

if [ -f "media.tar.gz.b64" ]; then
    python -c "import base64, io, tarfile; tarfile.open(fileobj=io.BytesIO(base64.b64decode(open('media.tar.gz.b64','rb').read())), mode='r:gz').extractall('.')"
fi

python manage.py collectstatic --noinput
