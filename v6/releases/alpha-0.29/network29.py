"""Narrow native research egress policy; not an OS sandbox."""
from urllib.parse import urlsplit
# Only explicitly reviewed document hosts; no model/API service hosts.
DOCUMENT_HOSTS=frozenset({'www.gutenberg.org','www.nist.gov','www.nasa.gov','www.noaa.gov','www.w3.org','www.ietf.org','www.rfc-editor.org','example.com'})
def check_document(url,allowed):
    h=urlsplit(url).hostname
    if h not in DOCUMENT_HOSTS or h not in allowed: raise ValueError('document host not permitted by native policy')
    if any(x in urlsplit(url).path.lower().split('/') for x in ('api','chat','inference','generate','completions')): raise ValueError('inference/API path not permitted')
