from newsapi import NewsApiClient
from dotenv import load_dotenv
import json
import os
from pygooglenews import GoogleNews
import urllib.request

load_dotenv()


def gnews_get_headlines():
    apikey = os.getenv("GNEWS_API_KEY")
    gnews_categories = ['general', 'world', 'nation', 'business', 'technology', 'entertainment', 'sports', 'science', 'health'] # adds general
    category = gnews_categories[2]
    url = f"https://gnews.io/api/v4/top-headlines?category={category}&lang=en&country=us&max=10&apikey={apikey}"

    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
        articles = data["articles"]

        headlines = []

        for i in range(len(articles)):
            curr_article = articles[i]
            
            # add title to headlines
            headlines.append(curr_article["title"])
        
        return headlines

print(gnews_get_headlines())

# Function for getting headlines
def newsapi_get_headlines():
    # get API key from environment variable
    API_KEY = os.getenv("NEWS_API_KEY")

    # Init
    newsapi = NewsApiClient(api_key=API_KEY)

    news_api_categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology'] # missing world and nation

    # get top headlines
    top_headlines = newsapi.get_top_headlines(language='en',
                                              category='business',
                                              country='us')
    
    headlines = []

    # Loop through the articles and get the title of each one
    for article in top_headlines['articles']:
        headlines.append(article['title'])
    
    return headlines


def pygooglenews_get_headlines():
    # Initialize GoogleNews object
    gn = GoogleNews(lang='en', country='US')

    goole_news_topics = ['WORLD', 'NATION', 'BUSINESS', 'TECHNOLOGY', 'ENTERTAINMENT', 'SCIENCE', 'SPORTS', 'HEALTH',] # missing general

    headlines = gn.topic_headlines('BUSINESS', proxies=None, scraping_bee = None)

    # Extract titles from the articles
    titles = []
    for article in headlines['entries']:
        title = article.title

        # remove source from title
        if ' - ' in title:
            # Split the title at the first occurrence of '-'
            split_title = title.split(' - ')
            
            # remove the last value in array
            split_title.pop(-1)

            # Join the remaining parts back into a string
            title = '-'.join(split_title)
        
        titles.append(title)
    
    return titles



