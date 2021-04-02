import os
import json

import requests
from bs4 import BeautifulSoup

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
        self.scrape_url = "http://example.python-scraping.com/"
        self.relative_save_path = "./crawled_index.json"
        self.index = InvertedIndex()
        idx = self.index.insert_page("test")
        idx2 = self.index.insert_page("test1")
        idx3 = self.index.insert_page("test2")
        idx4 = self.index.insert_page("test3")
        self.index.insert_word("fish", idx)
        self.index.insert_word("fish", idx2)
        self.index.insert_word("fish", idx3)
        self.index.insert_word("fish", idx4)
        self.index.insert_word("cod", idx2)
        self.index.insert_word("parana", idx)
        self.index.insert_word("place", idx3)

    def build_index(self):
        """
        Crawl a webpage and create index.
        """
        if self.index:
            print("An index is already loaded. Building again will overwrite the current index.")
            option = input("Continue? (y/N): ").strip()
            if option != "y":
                return

        self.index = InvertedIndex()

        html = requests.get(self.scrape_url).text
        soup = BeautifulSoup(html, "html.parser")

        print(soup)

        self.index.save_to_file(self.relative_save_path)

    def load_index(self):
        """
        Load an index from file.
        """
        if self.index:
            print("An index is already loaded. Loading from file will overwrite the current index.")
            option = input("Continue? (y/N): ").strip()
            if option != "y":
                return

        try:
            self.index = InvertedIndex.load_from_file(self.relative_save_path)
            print("Successfully loaded index!")
        except FileNotFoundError:
            print(f"No index found in file system at {self.relative_save_path}. Has an index been built?")

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
        print("Page: ", end="")
        
        for i, page_id in enumerate(pages):
            page_string = self.index.id_to_page[page_id]
            if i < len(pages) - 1:
                print(f"{page_string}, ", end="")
            else:
                print(page_string)

    def help(self):
        """
        Display a series of commands for the tool.
        """
        print("\nBuilding a search tool.")
        print("Enter the desired command followed by any arguments.")
        print("----------------------------------------------------------------")
        print("> build\t\tcrawl the website and build index")
        print("> load\t\tload the index from file system")
        print("> print <word>\tprint the inverted index for a particular word")
        print("> find <phrase>\tfind a query in the index")
        print("> help\t\tdisplay list of commands")
        print("> exit\t\tstop the tool")
        print("----------------------------------------------------------------")

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
                self.build_index()
            elif command == "load":
                self.load_index()
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
