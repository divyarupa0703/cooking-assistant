import os
import sys
import random
import requests
import speech_recognition as sr
import time
import pyttsx3
from bs4 import BeautifulSoup
import threading

class Recipe:
    def __init__(self, title, missed_ingredients, instructions, preparation_time, nutritional_info):
        self.title = title
        self.missed_ingredients = missed_ingredients
        self.instructions = instructions
        self.preparation_time = preparation_time
        self.nutritional_info = nutritional_info

recognizer = sr.Recognizer()   
engine = pyttsx3.init()


#speaking function below
def speak(text):
    engine.say(text)
    engine.runAndWait()

def stop_speaking():
    engine.stop()

timer_thread = None

#timer settings
def start_timer(duration):
    global timer_thread
    speak(f"Timer set for {duration} seconds.")
    timer_thread = threading.Timer(duration, timer_complete)
    timer_thread.start()

def stop_timer():
    global timer_thread
    if timer_thread:
        timer_thread.cancel()
        speak("Timer canceled.")
    else:
        speak("No timer is currently running.")

def timer_complete():
    speak("Timer is up!")

#commands are listened through voice
def listen_for_command():
    with sr.Microphone() as source:
        print("Listening for command...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio).lower()
        print("Command:", command)
        return command
    except sr.UnknownValueError:
        print("Sorry, I didn't catch that. Please try again.")
        return ""
    except sr.RequestError:
        print("Could not request results. Please check your internet connection.")
        return ""


#Data retreival from api
def fetch_recipes_from_api(ingredients):
    try:
        api_key = "a23b6cc8fe204e309e94a187bf9f8d81"
        endpoint = "https://api.spoonacular.com/recipes/findByIngredients"
        params = {
            "ingredients": ",".join(ingredients),
            "apiKey": api_key
        }
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (status codes >= 400)
        recipes = response.json()
        prepared_recipes = []
        for recipe in recipes:
            title = recipe.get("title", "")
            missed_ingredients = recipe.get("missedIngredients", [])
            instructions = fetch_recipe_instructions(recipe["id"])
            preparation_time = recipe.get("readyInMinutes", 0)
            nutritional_info = fetch_nutrition_from_dish_name(recipe["title"]) 
            prepared_recipe = Recipe(title, missed_ingredients, instructions, preparation_time, nutritional_info)
            prepared_recipes.append(prepared_recipe)
        return prepared_recipes
    except requests.exceptions.RequestException as e:
        print("Error fetching recipes:", e)
        return []

#instruction retreival
def fetch_recipe_instructions(recipe_id):
    try:
        endpoint = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        api_key = "6d23c2b227894d07a1bc9254a0cf4444"
        params = {
            "apiKey": api_key
        }
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (status codes >= 400)
        recipe_info = response.json()
        instructions = recipe_info.get("instructions")
        if instructions:
            # Check if instructions contain HTML tags
            if "<" in instructions:
                # If HTML tags are present, try to remove them
                soup = BeautifulSoup(instructions, "html.parser")
                cleaned_instructions = soup.get_text(separator="\n")
                return cleaned_instructions.split("\n")
            else:
                return instructions.split("\n")
        else:
            return []  # Return an empty list if instructions are not available
    except requests.exceptions.RequestException as e:
        print("Error fetching recipe instructions:", e)
        return []

#nutrition retreival
def fetch_nutrition_from_dish_name(dish_name):
    try:
        api_key = "6d23c2b227894d07a1bc9254a0cf4444"
        endpoint = "https://api.spoonacular.com/recipes/guessNutrition"
        params = {
            "title": dish_name,
            "apiKey": api_key
        }
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (status codes >= 400)
        nutrition_data = response.json()
        return nutrition_data
    except requests.exceptions.RequestException as e:
        print("Error fetching nutrition data:", e)
        return None

def extract_ingredients(command):
    words = command.split()
    recipe_index = words.index("recipe")
    ingredients = words[recipe_index + 1:]
    return ingredients



def generate_meal_plan(time_frame, target_calories=2000, diet=None, exclude=None):
    api_key = "6d23c2b227894d07a1bc9254a0cf4444"  
    url = "https://api.spoonacular.com/mealplanner/generate"
    params = {
        "timeFrame": time_frame,
        "targetCalories": target_calories,
        "diet": diet,
        "exclude": exclude,
        "apiKey": api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Failed to fetch meal plan.")
        return None

def display_meal_plan(meal_plan):
    if meal_plan:
        print("Generated Meal Plan:")
        for meal in meal_plan["meals"]:
            print(f"Title: {meal['title']}")
            print(f"Ready in Minutes: {meal['readyInMinutes']}")
            print(f"Servings: {meal['servings']}")
            print(f"Source URL: {meal['sourceUrl']}")
            print()




def display_recipe_titles(recipes):
    print("Suggested Recipes:")
    for idx, recipe in enumerate(recipes, start=1):
        print(f"{idx}. {recipe.title}")


def display_recipe(recipe):
    text_to_speak = f"\n{recipe.title} Recipe:\n\nIngredients:\n"
    for ingredient in recipe.missed_ingredients:
        ingredient_text = f"- {ingredient.get('amount', '')} {ingredient.get('unit', '')} {ingredient.get('name', '')}\n"
        text_to_speak += ingredient_text

    text_to_speak += "\nInstructions:\n"
    for step, instruction in enumerate(recipe.instructions, start=1):
        instruction_text = f"{step}. {instruction}\n"
        text_to_speak += instruction_text

    text_to_speak += f"\nPreparation Time: {recipe.preparation_time} minutes\n"
    
    speak(text_to_speak)
    print(text_to_speak)

# implementation of commands is done here
def execute_command(command):
    if "find recipe" in command:
        if "find recipe" in command:
          ingredients = extract_ingredients(command)
          recipes = fetch_recipes_from_api(ingredients)
        if recipes:
            display_recipe_titles(recipes)
            print("Please enter the number of the recipe to view details:")
            try:
                recipe_number = int(input("Enter the number of the recipe: "))
                recipe_index = recipe_number - 1
                if 0 <= recipe_index < len(recipes):
                    recipe = recipes[recipe_index]
                    display_recipe(recipe)
                    nutrition_data = fetch_nutrition_from_dish_name(recipe.title)
                    if nutrition_data:
                        print("\nEstimated Nutrition:")
                        print("Calories:", nutrition_data["calories"]["value"], "kcal")
                        print("Carbs:", nutrition_data["carbs"]["value"], "g")
                        print("Fat:", nutrition_data["fat"]["value"], "g")
                        print("Protein:", nutrition_data["protein"]["value"], "g")
                    else:
                        print("Failed to fetch nutrition data.")
                else:
                    print("Invalid recipe number.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        else:
            print("No recipes found with the provided ingredients.")
    elif "view recipe" in command:
        recipe_name = command.replace("view recipe", "").strip()
        nutrition_data = fetch_nutrition_from_dish_name(recipe_name)
        if nutrition_data:
            print("\nEstimated Nutrition:")
            print("Calories:", nutrition_data["calories"]["value"], "kcal")
            print("Carbs:", nutrition_data["carbs"]["value"], "g")
            print("Fat:", nutrition_data["fat"]["value"], "g")
            print("Protein:", nutrition_data["protein"]["value"], "g")
        else:
            print(f"Could not find nutrition data for the recipe '{recipe_name}'.")
    elif command == "generate meal plan":
        meal_plan = generate_meal_plan("day")  # Call the meal plan generator function
        if meal_plan:
            display_meal_plan(meal_plan)

    elif command == "exit":
        speak("Exiting the Recipe Generator App. Goodbye!")
        sys.exit()
    elif command == "stop speaking":
        stop_timer()
    elif command == "timer is up":
        speak("Timer is up!")
    else:
        print("Invalid command. Please try again.")

if __name__ == "__main__":
    print("Welcome to Jarvis, your virtual voice cooking assistant!")
    while True:
        command = listen_for_command()
        execute_command(command)
