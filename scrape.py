import json
import sys

import unidecode

from page import ClusterPage, BookPage

def recursively_unidecode(data):
    if isinstance(data, dict):
        return {k: recursively_unidecode(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [recursively_unidecode(e) for e in data]
    elif isinstance(data, str):
        return unidecode.unidecode(data)
    else:
        return data


def main():
    json_unicode_filename = 'springer_books_info.unicode.jsonl'
    json_filename = 'springer_books_info.jsonl'

    try:
        json_unicode_file = open(json_unicode_filename, 'w')
        json_file = open(json_filename, 'w')

        cluster = ClusterPage(1)
        number_of_cluster_pages = cluster.number_of_cluster_pages
        for i in range(1, number_of_cluster_pages + 1):
            cluster = ClusterPage(i)
            for url in cluster.book_page_urls:
                book_page = BookPage(url)

                book = book_page.to_dict()
                json_unicode = json.dumps(book, ensure_ascii=False)

                book = recursively_unidecode(book)
                json_ = json.dumps(book)

                print(json_unicode, file=json_unicode_file)
                print(json_, file=json_file)

    except KeyboardInterrupt:
        print()
    except Exception as e:
        print(e, file=sys.stderr)
    else:
        json_unicode_file.close()
        json_file.close()


if __name__ == "__main__":
    main()
