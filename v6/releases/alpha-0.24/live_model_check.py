"""Explicit opt-in smoke test of an already installed loopback model; no downloads."""
import argparse
import sqlite3
from types import SimpleNamespace
from acquisition import Acquisition
from providers import OllamaProvider, ProviderError


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('model', help='already installed local model name')
    args = p.parse_args()
    with sqlite3.connect(':memory:') as db:
        acquisition = Acquisition(SimpleNamespace(db=db))
        try:
            report = acquisition.extract('Text: Oak is a Tree.', 'local-smoke', local_model=OllamaProvider(args.model))
        except ProviderError as exc:
            print('LIVE VALIDATION UNAVAILABLE:', exc)
            return 2
        ok = (report.get('status') == 'candidate' and report.get('subject') == 'Oak' and report.get('predicate') == 'is a' and report.get('object') == 'Tree' and report.get('route') == 'local_model' and report.get('provider_attempts') == 1 and report.get('authenticated') is False)
        print('LIVE SMOKE PASS' if ok else 'LIVE SMOKE FAIL', report)
        return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
