# springer_open_access_books_scrape

Scrape and download springer OpenAccess books

## scrape.py

This script scrapes the books available in https://link.springer.com/search?package=openaccess&facet-content-type="Book".
It generates two JSON Lines:
* springer_books_info.unicode.jsonl: the original information. It causes problems because it has non ASCII whitespaces. 
* springer_books_info.jsonl: a transcoded version of the original. We use unidecode to transliterate every character.

To execute just run:
```bash
./scrape.py
```
and it will generate the two JSONL.

## download.py

You can filter the the JSON Lines file anyway you want (for example to download books of just some categories or just the pdfs).

To execute just run:
```bash
./download.py springer_books_info.jsonl /path/to/download/directory/
```
and it will start downloading the books. 

It will create two directories inside /path/to/download/directory/, one for the pdfs and another for the epubs. Inside each of them, it will create one directory per category.

The name of the files is the concatenation of the eISBN of the book and the filename in the Content-Disposition header (we need to use the eISBN, since some files have the same Content-Disposition).
