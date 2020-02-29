from bs4 import BeautifulSoup
import os
import shutil
import json

class Recipe():
	def __init__(self, soup):
		self.name = ''
		self.intro = ''
		self.ingredient = {}
		self.img_url = ''
		self.soup = soup
		self.servings = ''
		self.time = ''

	def to_json(self):
		name_json = {"recipe_name": self.name}
		time_json = {"cook_time": self.time}
		servings_json = {"servings": self.servings}
		tags_json = {"tags": self.tags}
		intro_json = {"recipe_intro": self.intro}
		img_json = {"img_url": self.img_url}
		instructions_json = {"recipe_instructions" : self.recipe_instructions}

		return {**name_json, **intro_json, **img_json, **time_json, **servings_json,
			    **self.recipe_ingredients, **instructions_json, **tags_json}

	def scrape_recipe(self , soup):
		pass

	def get_img_url(self):
		return self.img_url

	def get_name(self):
		return self.name


class NYTRecipe(Recipe):
	def __init__(self, soup):
		self.name = ""
		self.intro = ""
		self.ingredient = {}
		self.img_url = " "
		self.soup = soup
		self.time = ""
		self.servings = ""
		self.tags=[]

	def scrape_recipe(self):
		self.scrape_name()
		self.scrape_intro()
		self.scrape_instructions()
		self.scrape_img()
		self.scrape_ingredients()
		self.scrape_yield()
		self.scrape_tags()

	def scrape_name(self):
		try:
			self.name = self.soup.article.header.div.h1.get("data-name")
		except Exception as e:
			print(f"Could not scrape name: {e}")
			self.name =  "None"

	def scrape_intro(self):
		try:
			self.intro = self.soup.find("div", class_="recipe-topnote-metadata").p.text
		except Exception as e:
			print(f"Could not scrape intro: {e}")
			self.intro =  "None"

	def scrape_instructions(self):
		try:
			self.recipe_instructions =  {i:step.text for i, step in enumerate(self.soup.find("ol", class_="recipe-steps").find_all("li"))}
		except Exception as e:
			print(f"Could not scrape instructions: {e}")
			self.recipe_instructions =  "None"

	def scrape_img(self):
		try:
			self.img_url = self.soup.find("div", class_="media-container").img.attrs['src']
		except Exception as e:
			print(f"Could not scrape img: {e}")
			self.img_url =  "None"

	def scrape_ingredients(self):
		parts_list = self.soup.find("div", class_="recipe-instructions").find_all("h4", class_="part-name")
		ingredient_lists = self.soup.find("div", class_="recipe-instructions").find_all("ul", class_="recipe-ingredients")
		if parts_list:
			self.recipe_ingredients = {"Ingredients":{}}
			for part,ingredient_list  in zip(parts_list, ingredient_lists):
				self.recipe_ingredients["Ingredients"][part.text] = self._ingredient_extractor(ingredient_list)

		else:
			self.recipe_ingredients = {"Ingredients": self._ingredient_extractor(ingredient_lists[0])}

	def scrape_tags(self):
		try:
			self.tags = [tag.text for tag in self.soup.find('div', class_="tags-nutrition-container").find_all('a', class_='tag')]
		except Exception as e:
			self.tags = []
			print(f"Failed to scrape tags: {e}")

	def scrape_yield(self):
		try:
			time_serving_soup = self.soup.find("ul", class_="recipe-time-yield")
			for thing in time_serving_soup.find_all('li'):
				if thing.find('span', class_="recipe-yield-time-label recipe-time"):
					self.time = thing.find('span', class_="recipe-yield-value").text.strip("\n")
				elif thing.find('span', class_="recipe-yield-time-label recipe-yield"):
					self.servings = thing.find('span', class_="recipe-yield-value").text.strip("\n")

		except Exception as e:
			print(f"Could not scrape time and servings.")
			self.time = "n/a"
			self.servings = "n/a "

	def _ingredient_extractor(self, ingredient_list):
		recipe_dict = {}
		ingredients = ingredient_list.findAll('span', class_='ingredient-name')
		quantitites = ingredient_list.findAll('span', class_='quantity')
		for ingredient, quantity in zip(ingredients, quantitites):
			recipe_dict[ingredient.text.strip()] = quantity.text.strip()

		return recipe_dict