# Simple web crawler and search engine
Web services and web data coursework for crawling [example.python-scraping.com](http://example.python-scraping.com). This tool extracts data on the site by crawling it and builds an inverted index. This can then be used to search by phrase and display relevant pages. 

# Usage
First the virtual environment should be built and the requirements in ‘requirements.txt’ should be installed. Execute the following commands in the project directory.

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

Now the tool can be started. If the tool complains about certain packages not being installed, the previous step was not completed correctly.

```bash
python crawler.py
```

You will be presented with a menu. Type the command you wish to execute followed by any arguments. For example printing a chosen word and corresponding word count:

```
>>> print Kingdom
Results for word: Kingdom
Page: http://example.python-scraping.com/places/default/continent/EU, Word Count: 1
Page: http://example.python-scraping.com/places/default/view/United-Kingdom-233, Word Count: 1
Page: http://example.python-scraping.com/places/default/iso/GB, Word Count: 1
Page: http://example.python-scraping.com/places/default/index/23, Word Count: 1
```

Or searching for a query:
```
>>> Results for query: 'Example'
1. http://example.python-scraping.com/places/default/continent/AF, rank: 126
2. http://example.python-scraping.com/places/default/continent/EU, rank: 118
3. http://example.python-scraping.com/places/default/continent/AS, rank: 102
4. http://example.python-scraping.com/places/default/continent/NA, rank: 94
5. http://example.python-scraping.com/places/default/continent/OC, rank: 62
```

To leave the tool type ‘exit’ in the command selection. And type ‘help’ to display the commands again.
