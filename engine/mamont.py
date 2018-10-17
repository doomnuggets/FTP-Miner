import re
import traceback
from urllib.parse import urljoin, quote, unquote
from multiprocessing.pool import ThreadPool

import requests

from engine import Engine


class MamontEngine(Engine):

    def __init__(self):
        super(MamontEngine, self).__init__('Mamont', 'http://www.mmnt.ru/')

    def search(self, keyword):
        search_url = urljoin(self.base_url, f'/int/get?st={keyword}')
        response = requests.get(search_url)
        total_pages = self._extract_number_of_pages(response.text)
        if total_pages == 0:
            return

        for ftp_url in self._fetch_async(keyword, total_pages):
            yield ftp_url

    def _fetch_async(self, keyword, total_pages):
        base_url = f'http://www.mmnt.ru/int/get?in=f&st={keyword}&ot='
        urls = [base_url + str((i * 20) + 1) for i in range(total_pages+1)]
        pool = ThreadPool()
        for ftp_urls in pool.imap(self._process_url, urls):
            if any(ftp_urls):
                for ftp_url in ftp_urls:
                    yield ftp_url

    def _process_url(self, url):
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException:
            traceback.print_exc()
            return None
        return self._extract_ftp_urls(response.text)

    def _extract_ftp_urls(self, src):
        assert isinstance(src, str)
        return re.findall('<a href="(ftp.+?)\" target=', src)

    def _extract_number_of_pages(self, src):
        assert isinstance(src, str)
        try:
            return int(re.search('page <b>\d+</b> of <b>(\d+)</b>', src).group(1))
        except AttributeError:
            return 0
