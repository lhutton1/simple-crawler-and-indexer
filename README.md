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

You will be presented with a menu. Type the command you wish to execute followed by any arguments. For example:

```
>>> print Kingdom
Results for word: Kingdom
Page: http://example.python-scraping.com/places/default/continent/EU, Word Count: 1
Page: http://example.python-scraping.com/places/default/view/United-Kingdom-233, Word Count: 1
Page: http://example.python-scraping.com/places/default/iso/GB, Word Count: 1
Page: http://example.python-scraping.com/places/default/index/23, Word Count: 1
```

To leave the tool type ‘exit’ in the command selection. And type ‘help’ to display the commands again.
