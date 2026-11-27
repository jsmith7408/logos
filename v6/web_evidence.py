"""Operator-allowlisted HTTPS GET, public address pinning, no AI inference, no redirects."""
import socket, ssl, ipaddress, http.client, hashlib, time
from urllib.parse import urlsplit

class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self,host,ip):
        super().__init__(host,443,timeout=5,context=ssl.create_default_context()); self.ip=ip
    def connect(self):
        sock=socket.create_connection((self.ip,443),timeout=5)
        try: self.sock=self._context.wrap_socket(sock,server_hostname=self.host)
        except BaseException: sock.close(); raise

def fetch_public(url,allowed_hosts):
    if type(url) is not str or len(url)>2000 or type(allowed_hosts) not in (list,tuple,set) or not 1<=len(allowed_hosts)<=16: raise ValueError('invalid request')
    u=urlsplit(url); h=u.hostname
    if u.scheme!='https' or not h or u.username or u.password or u.port not in (None,443) or u.fragment or u.query or h not in allowed_hosts or not h.isascii() or h.endswith('.') or any(c in url for c in '\r\n\t'):
        raise ValueError('HTTPS allowlist, no credentials, query, or fragments')
    from network29 import check_document
    check_document(url,allowed_hosts)
    addresses=sorted({x[4][0] for x in socket.getaddrinfo(h,443,type=socket.SOCK_STREAM)})
    if not addresses or any(not ipaddress.ip_address(x).is_global for x in addresses): raise ValueError('non-public address')
    conn=PinnedHTTPS(h,addresses[0]); start=time.monotonic()
    try:
        conn.request('GET',u.path or '/',headers={'Accept':'text/plain, text/html','Accept-Encoding':'identity','User-Agent':'LOGOS-Research/0.28'})
        response=conn.getresponse(); ctype=response.getheader('Content-Type','').split(';')[0].strip().lower()
        if response.status!=200 or ctype not in ('text/plain','text/html') or response.getheader('Content-Encoding','identity').lower()!='identity': raise ValueError('unsupported response')
        data=bytearray()
        while True:
            if time.monotonic()-start>10: raise TimeoutError('read deadline')
            chunk=response.read1(min(8192,65537-len(data)))
            if not chunk: break
            data.extend(chunk)
            if len(data)>65536: raise ValueError('response limit')
        raw=bytes(data); content_sha=hashlib.sha256(raw).hexdigest(); key=hashlib.sha256((url+'\n'+content_sha).encode()).hexdigest()
        return {'id':key,'url':url,'sha256':content_sha,'text':raw.decode('utf-8','replace'),'bytes':len(raw),'content_type':ctype,'authenticated':False,'status':'unverified_web_snapshot','retrieved_unix':time.time()}
    finally: conn.close()
