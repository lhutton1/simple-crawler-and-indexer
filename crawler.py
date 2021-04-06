import os
import re
import json
import time
import requests
from urllib.parse import urljoin
from collections import deque
from queue import PriorityQueue

from bs4 import BeautifulSoup
from bs4.element import Comment

class Crawler:
    """
    Crawl a specified website and capture text.
    """
    def __init__(self):
        self.visited = {}
        self.frontier = deque()

        self.crawl_delay = 5
        self.save_frequency = 5

    def crawl(self, index, initial_frontier, root_url, save_path):
        """
        Adds words to index by crawling an initial frontier.
        """
        if not len(initial_frontier):
            raise ValueError("Initial frontier empty. Please specify a starting point.")
        for url in initial_frontier:
            self.visited[url] = None
            self.frontier.append(url)

        step = 0
        while len(self.frontier):
            url = self.frontier.popleft()
            print(f"Crawling {url}, Pending {len(self.frontier)}...")

            html = requests.get(url).text
            soup = BeautifulSoup(html, "html.parser")

            links = list(self.extract_links(soup, root_url))
            for link in links:
                if link in self.visited:
                    continue
                self.visited[link] = None
                self.frontier.append(link)

            # score page by using the total number of links found
            page_id = index.insert_page(url, len(links))
            self.visited[url] = page_id

            for word in self.extract_text(soup):
                index.insert_word(word, page_id)

            if step % self.save_frequency == 0:
                index.save_to_file(save_path)
            step += 1
            time.sleep(self.crawl_delay)

    def visible_text_tags(self, token):
        """
        Only capture text visible to the user.
        """
        hidden_tags = ["[document]", "script", "style", "head", "meta"]
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
            yield url
        

class InvertedIndex:
    """
    Create an inverted index which maintains the following data:
    page id -> page name, score
    word -> page id, word count
    """
    def __init__(self):
        self.page_count = 0
        self.pages = {}
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
        inv_list.pages = data["meta"]["pages"]
        inv_list.index = data["index"]
        return inv_list

    def save_to_file(self, file_path):
        """
        Save the index to file.
        """
        save_dict = {
            "meta": {
                "page_count": self.page_count,
                "pages": self.pages
            },
            "index": self.index
        }
        with open(file_path, "w") as f:
            json.dump(save_dict, f)

    def query(self, query):
        """
        Get inverted lists of words from query found in index.
        """
        for word in query:
            inverted_list = self.index.get(word)
            if inverted_list:
                yield inverted_list

    def insert_page(self, page_name, score=0):
        """
        Insert a page and get its ID.
        """
        idx = self.page_count
        # JSON insists keys are strings.
        self.pages[str(idx)] = [page_name, score]
        self.page_count += 1
        return idx

    def insert_word(self, word, page_id):
        """
        Insert a word into the index.
        """
        # JSON insists use of string values for keys
        page_id = str(page_id)
        if page_id not in self.pages:
            raise ValueError("Page ID not recognised, has the page been added?")

        if word not in self.index:
            self.index[word] = [[page_id, 1]]
        elif self.index[word][-1][0] == page_id:
            self.index[word][-1][1] += 1  
        else:
            self.index[word].append([page_id, 1])
            

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
        word_index = self.index.query([word])

        if not word_index:
            print("Requested word was not found in index.")
            return

        print(f"Results for word: {word}")
        for page_id, count in word_index.items():
            print(f"Page: {self.index.pages[str(page_id)][0]}, Word Count: {count}")

    def query_index(self, query):
        """
        Query the index based on an input phrase using
        document-at-a-time retrieval with some optimisation.

        Ranking is based on: sum_i(g_i * f_i),
        where f is the ranking of the page and g is the value of 
        the query token on the ith token.

        In this case:
            f = number of links (<a> tags) on the page
            g = number of the word in ith token on the page
        """
        inverted_lists = list(self.index.query(query))
        if len(inverted_lists) == 0:
            print("No results to show. Please check your query.")
            return

        # rather than iterate over all documents,
        # iterate over only the documents that are
        # in the query lists.
        current_offsets = [0] * len(inverted_lists)
        rank = PriorityQueue()
        initial_page_id = min(l[0][0] for l in inverted_lists)

        page_id = initial_page_id
        next_page_id = 0
        while next_page_id < self.index.page_count:
            score = 0
            next_page_id = self.index.page_count
            for i, l in enumerate(inverted_lists):
                offset = current_offsets[i]
                word_count = 0
                if l[offset][0] == page_id:
                    word_count = l[offset][1]
                    current_offsets[i] += 1
                score += word_count

                if len(l) > page_id + 1:
                    n = l[page_id + 1][0]
                    next_page_id = min(n, next_page_id)

            page_rank = self.index.pages[str(page_id)][1]
            score = score * page_rank
            # use a negative score to keep maximum values at top of queue
            rank.put((-score, page_id))
            page_id = next_page_id

        query_string = " ".join(query)
        print(f"Results for query: '{query_string}'")
        
        count = 0
        while not rank.empty():
            score, page_id = rank.get()
            page_string = self.index.pages[str(page_id)][0]
            count += 1
            # remember we used negative score so invert back
            print(f"{count}. {page_string}, rank: {-score}")

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
