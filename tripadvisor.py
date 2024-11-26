import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import random

proxies = [
    'http://135.148.233.152:3129',
    'http://72.10.160.94:18345',
    'http://189.240.60.169:9090'
]

def get_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    proxy = random.choice(proxies)
    proxy_dict = {
        'http': proxy,
        'https': proxy
    }
    
    try:
        response = requests.get(url, headers=headers, proxies=proxy_dict, timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            print(f"Failed to retrieve page: Status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

def parse_attractions(content):
    bsobj = bs(content, 'lxml')
    places = []
    ratings = []
    reviews = []
    categories = []

    for item in bsobj.find_all('div', {'class': 'XfVdV o YQJrd'}):
        places.append(item.text.strip())

    for svg in bsobj.find_all('svg', {'class': 'UctUV d H0 hzzSG'}):
        title_element = svg.find('title')
        if title_element:
            ratings.append(title_element.get_text(strip=True))

    for rev in bsobj.find_all('span', {'class': 'biGQs _P pZUbB hmDzD'}):
        reviews.append(rev.get_text(strip=True))

    for cat in bsobj.find_all('span', {'class': 'biGQs _P pZUbB avBIb hmDzD'}):
        categories.append(cat.get_text(strip=True))

    return places, ratings, reviews, categories

url = 'https://www.tripadvisor.com/Attractions-g294229-Activities-Jakarta_Java.html'

page_content = get_page(url)
if page_content:
    places, ratings, reviews, categories = parse_attractions(page_content)

    data = {'Place': places, 'Ratings': ratings, 'Number of Reviews': reviews, 'Category': categories}
    df = pd.DataFrame(data)

    df.to_csv('jakarta_attractions.csv', index=False)
    print("Data has been successfully scraped and saved to jakarta_attractions.csv")
else:
    print("Failed to retrieve data.")
