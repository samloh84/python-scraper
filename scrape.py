from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from furl import furl
from pprint import pprint
from pydash import _
from requests import ConnectionError
from requests_futures.sessions import FuturesSession
import argparse
import pydash
import re
import requests


def parse_html_for_urls(response):
    urls = []

    try:
        if response.headers.get('content-type').startswith('text/html'):
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a'):
                href = link.get('href')
                if href is not None:
                    f = furl(response.url).join(href)
                    f.remove(query=True, fragment=True)
                    urls.append(f.url)
    except:
        pass

    return urls


def scrape(**kwargs):
    starting_urls = kwargs.pop('starting_urls', [])
    next_url_filters = kwargs.pop('next_url_filters', [])
    parse_urls_callbacks = kwargs.pop('parse_urls_callbacks', [parse_html_for_urls])
    max_depth = kwargs.pop('max_depth', None)
    session = kwargs.pop('session', None)
    max_workers = kwargs.pop('max_workers', 10)

    if session is None:
        session = requests.Session()

    futures_session = FuturesSession(executor=ThreadPoolExecutor(max_workers=max_workers), session=session)

    if not isinstance(starting_urls, list):
        starting_urls = [starting_urls]

    if not isinstance(next_url_filters, list):
        next_url_filters = [next_url_filters]

    if not kwargs.has_key('headers'):
        kwargs['headers'] = {}
    if not kwargs['headers'].has_key('user-agent'):
        kwargs['headers'][
            'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'

    retrieved_url_dict = {}
    url_queue = set(starting_urls)

    compiled_next_url_filters = [re.compile(next_url_filter) for next_url_filter in next_url_filters]

    current_depth = 0

    while len(url_queue) > 0:
        request_array = map(lambda queued_url: futures_session.get(queued_url, **kwargs), url_queue)

        responses = []
        new_url_queue = []

        for request in request_array:
            try:
                response = request.result()
                print('Retrieved ' + response.url)

                retrieved_url_dict[response.url] = retrieved_url_obj = {
                    'url': response.url,
                    'depth': current_depth,
                    'response': response
                }

                parsed_urls = [parse_urls_callback(response) for parse_urls_callback in parse_urls_callbacks]
                parsed_urls = _.flatten(parsed_urls)
                retrieved_url_obj['parsed_urls'] = parsed_urls

                if max_depth is None or current_depth < max_depth:
                    for parsed_url in parsed_urls:
                        if pydash.collections.every(compiled_next_url_filters,
                                                    lambda compiled_next_url_filter: compiled_next_url_filter.search(
                                                        parsed_url) is None):
                            continue

                        if parsed_url in retrieved_url_dict.keys():
                            continue

                        new_url_queue.append(parsed_url)

            except ConnectionError as e:
                print e.message
                if 'BadStatusLine' in e.message:
                    new_url_queue.append(e.request.url)
            except Exception as e:
                print e.message

        current_depth += 1
        url_queue = new_url_queue

    return retrieved_url_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape URLs')
    parser.add_argument('--next_url_filters', action='append')
    parser.add_argument('--max_depth', action='store', type=int)
    parser.add_argument('starting_urls', metavar='starting_url', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    pprint(args)

    pprint(args.next_url_filters)

    results = scrape(starting_urls=args.starting_urls, next_url_filters=args.next_url_filters, max_depth=args.max_depth)

    pprint(results)
