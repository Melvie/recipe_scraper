import multiprocessing as multiproc
from bs4 import BeautifulSoup
from recipe import NYTRecipe
from queue import Queue
from threading import Thread

import requests 
import os
import shutil
import json

BASE_URL = "https://cooking.nytimes.com"


class Worker(Thread):
    """ Thread executing tasks from a given tasks queue """
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                # An exception happened in this thread
                print(e)
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()

class ThreadPool:
    """ Pool of threads consuming tasks from a queue """
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """ Add a task to the queue """
        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        """ Add a list of tasks to the queue """
        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        """ Wait for completion of all the tasks in the queue """
        self.tasks.join()


def retrieve_image(link, file_path):
	if link == 'None':
		return

    r = requests.get(link, stream=True)
    if r.status_code == 200:
        with open(file_path, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

def write_recipe_json(recipe, path):
    try:
        with open(path, 'w') as fp:
            json.dump(recipe, fp)

    except error as e:
        print(f"Write to file failed: {e}")

def save_recipe_info(recipe):
    formatted_name = recipe.get_name().replace(" ", "_").replace("\\","/")
    base_path = os.path.join(os.getcwd(), 'Recipes', formatted_name)
    if not os.path.exists(base_path):
        os.mkdir(base_path)
        write_recipe_json(recipe.to_json(), os.path.join(base_path,f"{formatted_name}.json"))
        retrieve_image(recipe.get_img_url(), os.path.join(base_path, f"{formatted_name}.jpg"))
        print(f"New Recipe: {recipe.get_name()} retrieved.")

    else:
        print(f"Recipe: {recipe.get_name()} already retrieved.")

def mkSoup(url):
    r = requests.get(url, auth=(os.environ['NYT_USER'], os.environ['NYT_PASS']))
    if r.status_code == 404:
        print(f"Page: {url} not found.")

    elif r.status_code == 200:
        return BeautifulSoup(r.content, features="html.parser")

def get_recipes(soup):
    recipe_articles= soup.findAll("article", class_="card recipe-card")
    recipes = [BASE_URL+recipe.find("a").get("href") for recipe in recipe_articles]

    return recipes

def process_recipe(recipe_url):
    try:
        soup = mkSoup(recipe_url)
        recipe  = NYTRecipe(soup)
        save_recipe_info(recipe)

    except Exception as e:
        print(f"Failed to scrape recipe: {e}")

def process_page(page_url):
    recipes = get_recipes(mkSoup(page_url))

    pool = ThreadPool(8)
    pool.map(process_recipe, recipes)
    pool.wait_completion()
    print(f"### Scraping Page #{page_url[-1]} complete. ###")

def main():
    ## get recipe urls

    start_page = 100
    number_of_pages = 321
    recipe_page_urls = [f"https://cooking.nytimes.com/search?q=&page={i}" for i in range(start_page,start_page+number_of_pages)]
    p = multiproc.Pool(number_of_pages//10)
    p.map(process_page, recipe_page_urls)
    p.terminate()
    p.join()
    # for i in range(1,2):
    #   url = f"https://cooking.nytimes.com/search?q=&page={i}"

    #   recipes = get_recipes(mkSoup(url))

    #   p = multiproc.Pool(24)
    #   p.map(scrape_n_save, recipes)
    #   p.terminate()
    #   p.join()
    #   print(f"Page {i} scraped.")



if __name__ == "__main__":
    main()