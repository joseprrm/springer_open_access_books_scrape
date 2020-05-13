#!/usr/bin/env python3
import sys
import json
import pathlib
import argparse

import requests


def parse_arguments():
    parser = argparse.ArgumentParser(description='Donwloads free books from springer')
    parser.add_argument('json', nargs=1, help='json with the book information')
    parser.add_argument('download_directory', nargs=1, help='download directory')

    args = parser.parse_args()
    return args.json[0], args.download_directory[0]


def get_books(json_filename):
    lines = []
    with open(json_filename, 'r') as f:
        lines = f.readlines()

    books = [json.loads(line) for line in lines]
    return books


def ensure_category_directory_exists(book, download_directory):
        category = book['category']
        category_directory =  download_directory.joinpath(pathlib.Path(category))
        category_directory.mkdir(parents=True, exist_ok=True)
        return category_directory


def download_book(book, filetype, filetype_directory):
        category_directory = ensure_category_directory_exists(book, filetype_directory)
        try:
            url = book['urls'][filetype]['url']
        except Exception as e:
            print(f"{filetype} file not found for book", book['full_title'] ,'. Skipping.')
            return

        filename = "_".join([book['eisbn'], book['urls'][filetype]['Content-Disposition']])
        # to avoid files with / in Content-Disposition
        filename = filename.replace('/', '_')
        file_ = category_directory.joinpath(pathlib.Path(filename))

        if not file_.exists():
            print("Downloading", book['full_title'])
            response = requests.get(url)
            with file_.open(mode='wb') as f:
                print("Writing", file_)
                f.write(response.content)
            print("Done")
        else:
            print(file_, "already exists, we skip it")


def main():
    json_, download_directory = parse_arguments()

    download_directory = pathlib.Path(download_directory)
    pdf_directory = download_directory.joinpath(pathlib.Path('pdf'))
    epub_directory = download_directory.joinpath(pathlib.Path('epub'))

    books = get_books(json_)
    for book in books:
        download_book(book, 'pdf', pdf_directory)
        download_book(book, 'epub', epub_directory)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
