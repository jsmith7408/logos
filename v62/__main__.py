import argparse
import json
from v62.collector import Collector
from v62.providers import Provider


def main():
    p = argparse.ArgumentParser(description='Collect model responses without validating their truth.')
    p.add_argument('--db', required=True)
    p.add_argument('--prompt', required=True)
    p.add_argument('--provider', action='append', required=True, metavar='NAME=MODEL')
    p.add_argument('--max-tokens', type=int, default=1024)
    p.add_argument('--allow-network', action='store_true')
    args = p.parse_args()
    if not args.allow_network:
        p.error('Live requests may incur costs; explicitly set --allow-network')
    try:
        providers = [Provider(*v.split('=', 1), max_tokens=args.max_tokens) for v in args.provider]
    except (TypeError, ValueError) as exc:
        p.error(str(exc))
    collector = Collector(args.db)
    try:
        print(json.dumps(collector.run(args.prompt, providers, allow_network=True), indent=2))
    finally:
        collector.close()


if __name__ == '__main__':
    main()
