import argparse

from engine.mamont import MamontEngine
from engine.napalm import NapalmEngine



def main(args):
    all_engines = [NapalmEngine(), MamontEngine()]

    try:
        for engine in all_engines:
            if args.show_banner:
                print(f'---[[ {engine.name} ]]---')
            for search_result in engine.search(args.search):
                print(search_result)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-s', '--search', help='The keyword(s) to search for.', required=True)
    ap.add_argument('-b', '--show-banner', help='Show engine banner above search results.', default=False, action='store_true')
    args = ap.parse_args()
    main(args)
