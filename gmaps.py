from flask import Flask, request, jsonify
import openai
import pandas as pd
import io
import requests
import os
from dotenv import dotenv_values, load_dotenv

app = Flask(__name__)

# Set your OpenAI and Google Maps API keys here
config = dotenv_values(".env")
print(config)
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
print("Google Maps API Key:", google_maps_api_key)
class ResponseFormatter:
    def __init__(self, message, statusCode, recommendations=None, error=None):
        self.message = message
        self.statusCode = statusCode
        self.recommendations = recommendations or []
        self.error = error

    def format_response(self):
        response = {
            "message": self.message,
            "statusCode": self.statusCode,
            "recommendations": self.recommendations
        }
        if self.error:
            response["error"] = self.error
        return response

def load_categories(csv_path):
    try:
        categories_df = pd.read_csv(csv_path)
        category_keywords = {}
        for _, row in categories_df.iterrows():
            category = row['category']
            keywords = row['keywords']
            if pd.notnull(keywords):
                keywords_list = [keyword.strip().lower() for keyword in str(keywords).split(',') if keyword.strip()]
                category_keywords[category] = keywords_list
        return category_keywords
    except Exception as e:
        raise ValueError(f"Error loading categories: {str(e)}")

def categorize_prompt(user_prompt, category_keywords):
    user_prompt = user_prompt.lower()
    for category, keywords in category_keywords.items():
        if any(keyword in user_prompt for keyword in keywords):
            return category
    return "Category not available"

def recommend_attractions(latitude, longitude, user_prompt):
    if not google_maps_api_key:
        return [{"name": "Error", "description": "Google Maps API key is not set", "rating": "N/A"}]
    
    try:
        places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            'location': f'{latitude},{longitude}',
            'radius': 5000,  
            'keyword': user_prompt,
            'key': google_maps_api_key
        }
        
        print("API Request Parameters:", params)

        response = requests.get(places_url, params=params)
        response.raise_for_status()  

        results = response.json().get('results', [])
        print("API Response:", response.json())  
        
        if not results:
            return [{"name": "No results found", "description": "", "rating": "N/A"}]

        recommendations = []
        for result in results:
            name = result.get('name', 'No name available')
            description = result.get('vicinity', 'No description available')
            rating = result.get('rating', 'No rating available')
            
            recommendations.append({
                "name": name,
                "description": description,
                "rating": rating
            })
        
        return recommendations

    except requests.exceptions.RequestException as e:
        return [{"name": "Error", "description": f"An error occurred with the API request: {str(e)}", "rating": "N/A"}]

@app.route('/')
def home():
    formatter = ResponseFormatter(message="success", statusCode=200)
    return jsonify(formatter.format_response())

@app.route('/recommendations', methods=['POST'])
def recommendations():
    data = request.get_json()

    prompt_csv = data.get('prompt_csv')
    user_data_csv = data.get('user_data_csv')
    category_csv_path = './data/flask_datasets/categories.csv'

    if not prompt_csv or not user_data_csv:
        formatter = ResponseFormatter(
            message="Please provide both prompt_csv and user_data_csv",
            statusCode=400,
            error="Missing CSV files"
        )
        return jsonify(formatter.format_response())

    try:
        users_df = pd.read_csv(io.StringIO(prompt_csv))
        locations_df = pd.read_csv(io.StringIO(user_data_csv))
        
        category_keywords = load_categories(category_csv_path)

        merged_df = pd.merge(users_df, locations_df, on='user_id')
        
        structured_recommendations = []
        
        for _, row in merged_df.iterrows():
            user_id = row['user_id']
            location_name = row['location_name']
            latitude = row['latitude']
            longitude = row['longitude']
            user_prompt = row.get('user_prompt', '')
            
            category = categorize_prompt(user_prompt, category_keywords)
            
            recommendations = recommend_attractions(latitude, longitude, user_prompt)
            
            if recommendations[0]['name'] == "Error":
                formatter = ResponseFormatter(
                    message="failed",
                    statusCode=500,
                    error=recommendations[0]['description']
                )
                return jsonify(formatter.format_response())
            
            structured_recommendations_for_user = []
            for idx, rec in enumerate(recommendations):
                structured_recommendations_for_user.append({
                    "rank": idx + 1,
                    "name": rec['name'],
                    "description": rec['description'],
                    "rating": rec['rating'],
                    "category": category
                })
            
            structured_recommendations.extend(structured_recommendations_for_user)
        
        formatter = ResponseFormatter(
            message="success",
            statusCode=200,
            recommendations=structured_recommendations
        )
        return jsonify(formatter.format_response())
    
    except Exception as e:
        formatter = ResponseFormatter(
            message="failed",
            statusCode=500,
            error=str(e)
        )
        return jsonify(formatter.format_response())

if __name__ == '__main__':
    app.run(debug=True)
