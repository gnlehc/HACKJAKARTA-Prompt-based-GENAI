from flask import Flask, request, jsonify
import openai
import pandas as pd
import io

app = Flask(__name__)

# Set your OpenAI API key here
openai.api_key = 'sk-proj-RaPQwENoFDL6ohssuHd6T3BlbkFJBMXifkXqdxRwp4iXFWHA'

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
    categories_df = pd.read_csv(csv_path)
    category_keywords = {}
    for _, row in categories_df.iterrows():
        category = row['category']
        keywords = row['keywords']
        if pd.notnull(keywords):
            keywords_list = [keyword.strip().lower() for keyword in str(keywords).split(',') if keyword.strip()]
            category_keywords[category] = keywords_list
    return category_keywords


def categorize_prompt(user_prompt, category_keywords):
    user_prompt = user_prompt.lower()
    for category, keywords in category_keywords.items():
        if any(keyword in user_prompt for keyword in keywords):
            return category
    return "Category not available"


def recommend_attractions(user_id, location_name, latitude, longitude, user_prompt):
    try:
        prompt = f"""
        Generate personalized recommendations based on the following user details and location:
        
        User ID: {user_id}
        Location Name: {location_name}
        Latitude: {latitude}
        Longitude: {longitude}
        User Prompt: {user_prompt}

        Provide recommendations for nearby places or services that fit the user's preferences.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
            stream=False
        )

        recommendations_text = response.choices[0].message['content'].strip()
        return recommendations_text

    except Exception as e:
        return f"An error occurred: {str(e)}"

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
        # Load CSV data from string
        users_df = pd.read_csv(io.StringIO(prompt_csv))
        locations_df = pd.read_csv(io.StringIO(user_data_csv))
        
        # Load category keywords from CSV
        category_keywords = load_categories(category_csv_path)

        # Debugging: Print loaded category keywords
        print("Category Keywords:", category_keywords)
        
        # Merge users and locations data
        merged_df = pd.merge(users_df, locations_df, on='user_id')
        
        structured_recommendations = []
        
        for _, row in merged_df.iterrows():
            user_id = row['user_id']
            location_name = row['location_name']
            latitude = row['latitude']
            longitude = row['longitude']
            user_prompt = row.get('user_prompt', '')
            
            # Debugging: Print user prompt
            print("User Prompt:", user_prompt)
            
            category = categorize_prompt(user_prompt, category_keywords)
            
            # Debugging: Print categorized category
            print("Categorized Category:", category)
            
            recommendations_text = recommend_attractions(user_id, location_name, latitude, longitude, user_prompt)
            
            structured_recommendations_for_user = []
            lines = recommendations_text.split('\n')
            
            # Initialize rank counter
            rank = 1
            
            for line in lines:
                line = line.strip()
                
                if line and not line.startswith("These recommendations"):
                    if line.startswith(f"{rank}. "):
                        # Extract name and description
                        content = line[len(f"{rank}. "):].strip()
                        description_index = content.find(" - ")
                        if description_index != -1:
                            name = content[:description_index].strip()
                            description = content[description_index + 2:].strip()
                        else:
                            name = content
                            description = "Description not available"
                        
                        structured_recommendations_for_user.append({
                            "rank": rank,
                            "name": name,
                            "description": description,
                            "category": category
                        })
                        rank += 1
            
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
