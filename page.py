import time
import urllib
import re
import ast
from abc import ABC, abstractmethod
from functools import cached_property

from bs4 import BeautifulSoup
import requests


class Page(ABC):
    BASE_URL = 'https://link.springer.com'

    def relative_to_absolute(url):
        return urllib.parse.urljoin(Page.BASE_URL, url)

    def download(self, url):
        time.sleep(1)
        url = Page.relative_to_absolute(url)
        reponse = requests.get(url)
        return reponse

    @cached_property
    def soup(self):
        response = self.download(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup


class ClusterPage(Page):
    # we refer to the pages where the books are listed as cluster pages
    # WARNING -> you have to format it with a page number
    CLUSTER_URL = 'search/page/{}?facet-content-type="Book"&package=openaccess'

    def __init__(self, page_number):
        self.url = ClusterPage.CLUSTER_URL.format(page_number)

    @cached_property
    def book_page_urls(self):
        lis = self.soup.findAll('li', class_='has-cover')
        urls = [li.find('a')['href'] for li in lis]
        return urls

    @cached_property
    def number_of_cluster_pages(self):
        span = self.soup.find('span', class_='number-of-pages')
        number_of_cluster_pages = int(span.text)
        return number_of_cluster_pages


class BookPage(Page):
    def __init__(self, url):
        self.url = url

    @cached_property
    def title(self):
        page_title = self._page_title
        title = page_title.find('h1').text
        return title

    @cached_property
    def subtitle(self):
        try:
            page_title = self._page_title
            subtitle = page_title.find('h2').text
            return subtitle
        except BaseException:
            return None

    @cached_property
    def authors(self):
        div = self._main_container.find('div', class_='persons__list')
        spans = div.findAll('span', class_='authors__name')
        authors = [span.text for span in spans]
        return authors

    @cached_property
    def urls(self):
        items = self._main_container.findAll(
            'div', class_='cta-button-container__item')
        urls = [item.find('a')['href'] for item in items]
        urls = [Page.relative_to_absolute(url) for url in urls]
        urls_dict = {}
        for url in urls:
            try:
                content_disposition = requests.head(url).headers.get('Content-Disposition').split("=")[1]
            except:
                # if there isn't Content-Disposition, it means that the link is not available 
                # see book with doi 10.1007/978-3-319-03137-8
                continue
            file_dict = {'url': url, 'Content-Disposition': content_disposition}
            if re.match(r'.*\.pdf', url):
                urls_dict['pdf'] = file_dict
            elif re.match(r'.*\.epub', url):
                urls_dict['epub'] = file_dict
            else:
                urls_dict['unknown'] = file_dict
                print('Unknown url detected')
        return urls_dict

    @cached_property
    def category(self):
        return self._data_layer["content"]["category"]["pmc"]["primarySubject"]

    @cached_property
    def eisbn(self):
        return self._data_layer["content"]["book"]["eisbn"]

    @cached_property
    def doi(self):
        return self._data_layer["content"]["book"]["doi"]

    @cached_property
    def keywords(self):
        return self._data_layer.get("kwrd")  # it can be missing

    @cached_property
    def _page_title(self):
        return self._main_container.find('div', class_='page-title')

    @cached_property
    def _main_container(self):
        return self.soup.find('div', class_='main-container')

    @cached_property
    def _data_layer(self):
        return self._get_data_layer()

    def to_dict(self):
        # https://stackoverflow.com/questions/14263872/only-add-to-a-dict-if-a-condition-is-met
        class DictNoNone(dict):
            def __setitem__(self, key, value):
                if key in self or value is not None:
                    dict.__setitem__(self, key, value)

        book_info = {
            'full_title': DictNoNone({'title': self.title}),
            'authors': self.authors,
            'urls': self.urls,
            'category': self.category,
            'eisbn': self.eisbn,
            'doi': self.doi,
        }

        book_info = DictNoNone(book_info)
        book_info['full_title']['subtitle'] = self.subtitle
        book_info['keywords'] = self.keywords

        return book_info

    def _get_data_layer(self):
        def get_raw_json():
            # I dont know why .text returns an empty string, it didn't do that before.
            # we can use .contesnts and get the first element to get the script
            script = self.soup.find('script').contents[0]
            match = re.search(r'\[{.*;', script, re.DOTALL)
            raw_json = match.group(0)
            return raw_json

        def remove_empty_lines(lines):
            return (line for line in lines if line != "")

        def remove_spaces_at_the_beginning(lines):
            return (re.sub("^ +", "", line) for line in lines)

        def remove_lines_with_krux_references(lines):
            return (line for line in lines if not re.search(r': Krux\.', line))

        """
        Every book page has a javascript script with a variable dataLayer that
        holds a json with the book information. We can't just load the json
        because it has references to a javascript variable and uses single
        quotes for keys, which are not valid in json.
        Since we can't directly load the json, we will load it as a python
        dict.
        """
        raw_json = get_raw_json()
        lines = raw_json.splitlines()
        lines = remove_lines_with_krux_references(lines)
        lines = remove_empty_lines(lines)
        lines = remove_spaces_at_the_beginning(lines)

        raw_dict_ = "".join(lines)

        # we dont need the [ and ]; characters
        raw_dict_ = raw_dict_[1:-2]

        # in the book "International Perspectives on Early Childhood Education
        # and Development" there is a malformed string which causes errors when
        # trying to parse the dictionary, we fix it here:
        raw_dict_ = raw_dict_.replace(
            '""glocal"_pedagogy"',
            '"\\"glocal\\"_pedagogy"')

        dict_ = ast.literal_eval(raw_dict_)
        return dict_
