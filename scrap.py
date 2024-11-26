import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_attractions(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve the page: Status code {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    attractions = []
    
    print(soup.prettify())
    
    for item in soup.find_all('div', class_='css-1p6a9px'):
        title = item.find('a', class_='css-1n4w9b1').get_text(strip=True) if item.find('a', class_='css-1n4w9b1') else 'No title'
        rating = item.find('span', class_='css-1h1j0y3').get_text(strip=True) if item.find('span', class_='css-1h1j0y3') else 'No rating'
        description = item.find('div', class_='css-1p9ibgf').get_text(strip=True) if item.find('div', class_='css-1p9ibgf') else 'No description'
        
        attractions.append({
            'Title': title,
            'Rating': rating,
            'Description': description
        })
    
    return attractions

url = 'https://www.tripadvisor.com/Attractions-g294229-Activities-Jakarta_Java.html'

attractions_data = get_attractions(url)

if attractions_data:
    df = pd.DataFrame(attractions_data)

    df.to_csv('jakarta_attractions.csv', index=False)
    print("Data has been successfully scraped and saved to jakarta_attractions.csv")
else:
    print("No data retrieved.")

