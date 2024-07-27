import pandas as pd

def load_categories(csv_path):
    categories_df = pd.read_csv(csv_path)
    category_keywords = {}
    for _, row in categories_df.iterrows():
        category = row['category']
        keywords = row['keywords']
        if pd.notnull(keywords):
            keywords_list = [keyword.strip().lower() for keyword in keywords.split(',') if keyword.strip()]
            category_keywords[category] = keywords_list
            print(f"Loaded category: {category} with keywords: {keywords_list}")  
    return category_keywords

def categorize_prompt(user_prompt, category_keywords):
    user_prompt = user_prompt.lower()
    print(f"User Prompt: {user_prompt}")  
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in user_prompt:
                return category
    return "Category not available"

# Example CSV path
category_csv_path = './data/flask_datasets/categories.csv'
category_keywords = load_categories(category_csv_path)

# Test user prompts
test_prompts = [
    "Find a nice restaurant with a barbecue menu.",
    "Looking for a family-friendly place with activities for kids.",
    "Recommendations for a romantic cafe with a scenic view.",
    "Suggest some outdoor adventures like hiking and rafting.",
    "Looking for a cultural parade or festival."
]

for prompt in test_prompts:
    category = categorize_prompt(prompt, category_keywords)
    print(f"Prompt: '{prompt}' -> Category: {category}")
