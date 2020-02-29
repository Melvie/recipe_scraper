import multiprocessing as multiproc
from bs4 import BeautifulSoup
from recipe import NYTRecipe
from untils import ThreadPool

import requests 
import os
import shutil
import json

BASE_URL = "https://cooking.nytimes.com"

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
    #TODO convert scraper into class, need better way of handling base_url for different sites
    return recipes

def process_recipe(recipe_url):
    try:
        soup = mkSoup(recipe_url)
        recipe  = NYTRecipe(soup)
        recipe.scrape_recipe()
        save_recipe_info(recipe)

    except Exception as e:
        print(f"Failed to scrape recipe: {e}")

def process_page(page_url):
    recipes = get_recipes(mkSoup(page_url))

    pool = ThreadPool(8)
    pool.map(process_recipe, recipes)
    pool.wait_completion()
    page_num = page_url.split("=")[2]
    print(f"### Scraping Page #{page_num} complete. ###")

def scrape_nyt(start_page, end_page):
    recipe_page_urls = [f"https://cooking.nytimes.com/search?q=&page={i}" for i in range(start_page,end_page+1)]
    p = multiproc.Pool(10)
    p.map(process_page, recipe_page_urls)
    p.terminate()
    p.join()

def main():
    scrape_nyt(11, 410)
    # process_page("https://cooking.nytimes.com/search?q=&page=11")
    # with open("recipe_page.html") as file:
	#     soup = BeautifulSoup(file, features="html.parser")

    # recipe = NYTRecipe(soup)
    # recipe.scrape_yield()
    # recipe.scrape_tags()
    # print(f"Time: {recipe.time}\nServings: {recipe.servings}\nTags: {recipe.tags}")


if __name__ == "__main__":
    main()