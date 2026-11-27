"""Experimental local CLI; never admits V5 evidence."""
import argparse, json, os, secrets, stat
from orchestration31 import run
from audit31 import retrieve

def keyfile(path, create=False):
    flags = os.O_NOFOLLOW | os.O_NONBLOCK
    if create:
        fd = os.open(path, flags | os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(secrets.token_bytes(32)); f.flush(); os.fsync(f.fileno())
        return None
    with os.fdopen(os.open(path, flags | os.O_RDONLY), 'rb') as f:
        s = os.fstat(f.fileno())
        if not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or s.st_mode & 0o077:
            raise ValueError('unsafe key file')
        key = f.read(33)
        if len(key) != 32: raise ValueError('invalid key length')
        return key

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--key', required=True); p.add_argument('--db', required=True)
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('init'); sub.add_parser('solve').add_argument('question')
    sub.add_parser('retrieve').add_argument('id')
    a = p.parse_args(argv)
    if a.cmd == 'init':
        keyfile(a.key, True); result = {'initialized': True}
    elif a.cmd == 'solve': result = run(a.db, a.question, keyfile(a.key))
    else: result = retrieve(a.db, a.id, keyfile(a.key))
    print(json.dumps(result, allow_nan=False))

if __name__ == '__main__': main()
