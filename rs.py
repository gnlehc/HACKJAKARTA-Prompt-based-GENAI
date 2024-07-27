from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

openai.api_key = 'YOUR_API_KEY'

def recommend_attractions(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=200,
        temperature=0.7,
        n=1,
        stop=None
    )
    return response.choices[0].text.strip()

@app.route('/recommend', methods=['POST'])
def recommend():
    user_prompt = request.json.get('prompt')
    if not user_prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    recommendations = recommend_attractions(user_prompt)
    return jsonify({'recommendations': recommendations})

if __name__ == '__main__':
    app.run(debug=True)
