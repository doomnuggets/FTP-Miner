import re
import bs4
import traceback
import base64
import urllib.parse
from multiprocessing.pool import ThreadPool
from itertools import product

import requests

from engine import Engine


class NapalmEngine(Engine):

    def __init__(self):
        super(NapalmEngine, self).__init__('Napalm', 'https://www.searchftps.net/')
        self._session = None

    def _init_session(self):
        session = requests.Session()
        session.headers['Referer'] = self.base_url
        session.headers['Host'] = 'www.searchftps.net'
        session.headers['Accept-Language'] = 'en-US;en;q=0.5'
        session.headers['Cache-Control'] = 'no-cache'
        session.headers['Connection'] = 'keep-alive'
        session.headers['DNT'] = '1'
        session.headers['Host'] = 'www.searchftps.net'
        session.headers['Pragma'] = 'no-cache'
        session.headers['Upgrade-Insecure-Requests'] = '1'
        session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'
        session.get(self.base_url + 'about')  # grab the session cookie.
        return session

    def search(self, keyword):
        encoded_keyword = urllib.parse.quote_plus(keyword)
        if not self._session:
            self._session = self._init_session()
            for ftp_url in self._fetch_async(encoded_keyword):
                yield ftp_url

    def _fetch_async(self, encoded_keyword):
        response = self._session.post(self.base_url,
                                      data={'action': 'result',
                                            'args': f'k={encoded_keyword}&t=and&o=none&s=0'})
        if 'No files found.' in response.text:
            return
        hashes = set(self._extract_hashes(response.text))
        next_page_payload = self._extract_next_page_post_args(response.text)

        while next_page_payload is not None:
            response = self._session.post(self.base_url, data=next_page_payload)
            hashes.update(self._extract_hashes(response.text))
            next_page_payload = self._extract_next_page_post_args(response.text)

        pool = ThreadPool()
        for ftp_url in pool.imap(self._resolve_hash, hashes):
            yield ftp_url

        self._session.close()
        self._session = None

    def _resolve_hash(self, hash_):
        try:
            response = self._session.post(self.base_url,
                                          data={'action': 'content',
                                                'args': f'type=f&hash={hash_}'})
        except requests.exceptions.RequestException:
            traceback.print_exc()
            return None

        b64_encoded_ftp_url = re.search('decodeURIComponent\(escape\(decode\(\'([a-zA-Z0-9=]+)\'\)\)\);', response.text).group(1)
        return base64.b64decode(b64_encoded_ftp_url).decode('utf8', errors='replace')

    def _extract_hashes(self, src):
        # javascript:go('content', {'type': 'f', 'hash': 'ldsjgliedsgoij123io1rjofolij'})
        return re.findall('javascript:go\(\'content\', {\'type\':\'f\', \'hash\':\'(\w+)\'}\)', src)

    def _extract_next_page_post_args(self, src):
        try:
            pattern = 'Back\<\/a\>.*class="btn"\s+href="javascript:go.+?\{(.+?)\}.+?Next'
            next_btn_raw = re.search(pattern, src, re.DOTALL).group(1)
        except AttributeError:
            return None
        args_raw = next_btn_raw.split(',')
        args = []
        for arg_raw in args_raw:
            key, value = arg_raw.split(':', 1)  # " 'k':'v' "
            key = key.strip()[1:-1]  # Remove surrounding quotes.
            value = value.strip()[1:-1]  # Remove surrounding quotes.
            args.append(key + '=' + value)
        args_str = '&'.join(args)
        return {'action': 'result', 'args': args_str}

    def __del__(self):
        if self._session is not None:
            self._session.close()
