"""Bounded HTTP adapters. Credentials are read from the environment at call time."""
import json
import os
import re
from dataclasses import dataclass
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from urllib.error import HTTPError, URLError

MAX_BODY = 2 * 1024 * 1024


class ProviderError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def transport(url, payload, headers, timeout):
    req = Request(url, data=canonical(payload).encode(), headers={
        'Content-Type': 'application/json', **headers}, method='POST')
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=timeout) as res:
            raw = res.read(MAX_BODY + 1)
    except HTTPError as exc:
        code = exc.code
        exc.close()
        raise ProviderError(f'http_{code}') from None
    except (URLError, OSError):
        raise ProviderError('network_error') from None
    if len(raw) > MAX_BODY:
        raise ProviderError('response_too_large')
    return raw


@dataclass(frozen=True)
class Provider:
    name: str
    model: str
    max_tokens: int = 1024
    timeout: float = 60

    def __post_init__(self):
        if self.name not in ('openai', 'gemini', 'grok', 'ollama'):
            raise ValueError('Unsupported provider')
        if not re.fullmatch(r'[A-Za-z0-9._:-]{1,160}', self.model):
            raise ValueError('Invalid model identifier')
        if type(self.max_tokens) is not int or not 1 <= self.max_tokens <= 4096:
            raise ValueError('Output cap must be 1–4096')
        if not 0 < self.timeout <= 120:
            raise ValueError('Timeout must be positive and at most 120 seconds')

    def prepare(self, prompt):
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 16000:
            raise ValueError('Prompt must be nonempty and at most 16000 characters')
        messages = [{'role': 'user', 'content': prompt}]
        if self.name == 'gemini':
            if ':' in self.model:
                raise ValueError('Invalid Gemini model')
            return ('https://generativelanguage.googleapis.com/v1beta/models/'
                    + self.model + ':generateContent',
                    {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                     'generationConfig': {'maxOutputTokens': self.max_tokens}})
        if self.name == 'ollama':
            return ('http://127.0.0.1:11434/api/chat',
                    {'model': self.model, 'messages': messages, 'stream': False,
                     'options': {'num_predict': self.max_tokens}})
        root = 'https://api.openai.com' if self.name == 'openai' else 'https://api.x.ai'
        return (root + '/v1/responses', {'model': self.model, 'input': prompt,
                'max_output_tokens': self.max_tokens, 'store': False})

    def headers(self):
        if self.name == 'ollama':
            return {}
        env = {'openai': 'OPENAI_API_KEY', 'gemini': 'GEMINI_API_KEY',
               'grok': 'XAI_API_KEY'}[self.name]
        key = os.environ.get(env)
        if not key or not key.strip() or '\n' in key or '\r' in key:
            raise ProviderError('missing_or_invalid_credential')
        return {'x-goog-api-key': key} if self.name == 'gemini' else {'Authorization': 'Bearer ' + key}

    def parse(self, raw):
        try:
            data = json.loads(raw)
            if self.name in ('openai', 'grok'):
                if data['status'] != 'completed':
                    raise ProviderError('incomplete_response')
                parts = [p['text'] for item in data['output'] if item.get('type') == 'message'
                         and item.get('role') == 'assistant'
                         for p in item['content'] if p.get('type') == 'output_text']
                model = data.get('model')
            elif self.name == 'gemini':
                candidate = data['candidates'][0]
                if candidate.get('finishReason') != 'STOP':
                    raise ProviderError('incomplete_response')
                parts = [p['text'] for p in candidate['content']['parts']
                         if 'text' in p and not p.get('thought', False)]
                model = data.get('modelVersion')
            else:
                if data.get('done') is not True or data.get('done_reason') != 'stop':
                    raise ProviderError('incomplete_response')
                parts = [data['message']['content']]
                model = data.get('model')
            answer = '\n'.join(parts).strip()
            if not answer:
                raise ProviderError('empty_answer')
            return {'answer': answer, 'reported_model': model if isinstance(model, str) else None}
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            raise ProviderError('invalid_response') from None
