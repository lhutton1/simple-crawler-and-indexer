import os
import re
import json
import time
import requests
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Comment

class Crawler:
    """
    Crawl a specified website and capture text.
    """
    def __init__(self):
        self.visited = {}
        self.frontier = set()

        self.crawl_delay = 5
        self.save_frequency = 5

    def crawl(self, index, initial_frontier, root_url, save_path):
        """
        Adds words to index by crawling an initial frontier.
        """
        if not len(initial_frontier):
            raise ValueError("Initial frontier empty. Please specify a starting point.")
        for url in initial_frontier:
            self.frontier.add(url)

        step = 0
        while len(self.frontier):
            url = self.frontier.pop()
            print(f"Crawling {url}, Pending {len(self.frontier)}...")

            html = requests.get(url).text
            soup = BeautifulSoup(html, "html.parser")

            page_id = index.insert_page(url)
            self.visited[url] = page_id

            for word in self.extract_text(soup):
                index.insert_word(word, page_id)
            links = self.extract_links(soup, root_url)
            for link in links:
                self.frontier.add(link)

            if step % self.save_frequency == 0:
                index.save_to_file(save_path)
            step += 1
            time.sleep(self.crawl_delay)

    def visible_text_tags(self, token):
        """
        Only capture text visible to the user.
        """
        hidden_tags = ["[document]", "script", "style", "title", "head", "meta"]
        if token.parent.name in hidden_tags:
            return False
        if isinstance(token, Comment):
            return False
        return True

    def extract_text(self, soup):
        """
        Get visible text on page and split into words.
        """
        raw_text = soup.findAll(text=True)
        raw_text = filter(self.visible_text_tags, raw_text)
        for token in raw_text:
            token = re.sub("[^a-zA-Z\n]+", " ", token).strip()
            if token == "":
               continue
            yield from token.split(" ")

    def extract_links(self, soup, crawl_url):
        """
        Extract links on the site and ensure they are absolute.
        """
        for link in soup.findAll("a"):
            url = link.get("href")
            url = urljoin(crawl_url, url)
            if url in self.visited:
                continue
            yield url
        

class InvertedIndex:
    """
    Create an inverted index which maintains the following data:
    page id -> page name
    word -> (page id -> word count)
    """
    def __init__(self):
        self.page_count = 0
        self.id_to_page = {}
        self.index = {}

    @classmethod
    def load_from_file(cls, file_path):
        """
        Load the index from file.
        """
        with open(file_path, "r") as f:
            data = json.load(f)
        inv_list = cls()
        inv_list.page_count = data["meta"]["page_count"]
        inv_list.id_to_page = data["meta"]["id_to_page"]
        inv_list.index = data["index"]
        return inv_list

    def save_to_file(self, file_path):
        """
        Save the index to file.
        """
        save_dict = {
            "meta": {
                "page_count": self.page_count,
                "id_to_page": self.id_to_page
            },
            "index": self.index
        }
        with open(file_path, "w") as f:
            json.dump(save_dict, f)

    def query(self, word):
        """
        Query they inverted index.
        """
        return self.index.get(word)

    def insert_page(self, page_name):
        """
        Insert a page and get its ID.
        """
        idx = self.page_count
        self.id_to_page[idx] = page_name
        self.page_count += 1
        return idx

    def insert_word(self, word, page_id, count=1):
        """
        Insert a word into the index.
        """
        if page_id not in self.id_to_page:
            raise ValueError("Page ID not recognised, has the page been added?")

        if word not in self.index:
            self.index[word] = {page_id: count}
        elif self.index[word].get(page_id) is None:
            self.index[word][page_id] = count
        else:
            self.index[word][page_id] += 1


class SearchTool:
    """
    Search tool. Creates a searchable index by crawling a web page.
    """
    def __init__(self):
        self.s = requests.Session()
        self.initial_url = "http://example.python-scraping.com/"
        self.relative_save_path = "./crawled_index.json"
        self.index = None
        self.crawler = Crawler()

    def build_index(self, crawl_url, save_path):
        """
        Crawl a webpage and create index.
        """
        if self.index:
            print("An index is already loaded. Building again will overwrite the current index.")
            option = input("Continue? (y/N): ").strip()
            if option != "y":
                return

        self.index = InvertedIndex()
        self.crawler.crawl(self.index, 
                           [crawl_url], 
                           crawl_url, 
                           save_path)
        self.index.save_to_file(save_path)

    def load_index(self, path):
        """
        Load an index from file.
        """
        if self.index:
            print("An index is already loaded. Loading from file will overwrite the current index.")
            option = input("Continue? (y/N): ").strip()
            if option != "y":
                return

        try:
            self.index = InvertedIndex.load_from_file(path)
            print("Successfully loaded index!")
        except FileNotFoundError:
            print(f"No index found in file system at {path}. Has an index been built?")

    def print_index(self, word):
        """
        Print the index of a single word.
        """
        word_index = self.index.query(word)

        if not word_index:
            print("Requested word was not found in index.")
            return

        print(f"Results for word: {word}")
        for page_id, count in word_index.items():
            print(f"Page: {self.index.id_to_page[page_id]}, Word Count: {count}")

    def query_index(self, query):
        """
        Query the index based on an input phrase.
        """
        pages = set()

        for word in query:
            result = self.index.query(word)
            if not result:
                continue
            if len(pages) == 0:
                pages = result.keys()
            pages = pages & self.index.query(word).keys()

        query_string = " ".join(query)

        if len(pages) == 0:
            print("No results to show. Please check your query.")
            return

        print(f"Results for query: '{query_string}'")
        print("Page:")
        
        for i, page_id in enumerate(pages):
            page_string = self.index.id_to_page[page_id]
            if i < len(pages) - 1:
                print(f"\t{page_string},")
            else:
                print(f"\t{page_string}")

    def help(self):
        """
        Display a series of commands for the tool.
        """
        print("\nBuilding a search tool.")
        print("Enter the desired command followed by any arguments.")
        print("----------------------------------------------------------------------------------------------")
        print("> build <optional: crawl url, save path>\tcrawl the website and build index")
        print("> load \t<optional: load path>\t\t\tload the index from file system")
        print("> print <word>\t\t\t\t\tprint the inverted index for a particular word")
        print("> find \t<phrase>\t\t\t\tfind a query in the index")
        print("> help\t\t\t\t\t\tdisplay list of commands")
        print("> exit\t\t\t\t\t\tstop the tool")
        print("----------------------------------------------------------------------------------------------")

    def get_command(self):
        """
        Get a command to execute from options presented in the help screen.
        """
        d.help()
        get_command = True

        while(get_command):
            prompt_marker = ">>> "
            input_list = input(prompt_marker).strip().split()

            if not input_list:
                continue

            command = input_list[0]
            if command == "build":
                crawl_url = input_list[1] if len(input_list) > 1 \
                    else self.initial_url
                save_path = input_list[2] if len(input_list) > 2 \
                    else self.relative_save_path
                self.build_index(crawl_url, save_path)
            elif command == "load":
                load_path = input_list[1] if len(input_list) > 1 \
                    else self.relative_save_path
                self.load_index(load_path)
            elif command == "print":
                if len(input_list) != 2:
                    print("No word argument found.")
                    continue
                if not self.index:
                    print("No index to print from. Please load or build a new index.")
                    continue
                self.print_index(input_list[1])
            elif command == "find":
                if len(input_list) < 2:
                    print("No phrase argument found.")
                    continue
                if not self.index:
                    print("No index to print from. Please load or build a new index.")
                    continue
                self.query_index(input_list[1:])
            elif command == "help":
                d.help()
            elif command == "exit":
                break
            else:
                print("Command not found, type 'help' to display list of commands.")


if __name__ == "__main__":
    d = SearchTool()
    d.get_command()
