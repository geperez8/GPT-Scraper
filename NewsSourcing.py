from dotenv import load_dotenv
import json
import os
import urllib.request
def gnews_get_headlines():
    apikey = os.getenv("GNEWS_API_KEY")
    gnews_categories = ['general', 'world', 'nation', 'business', 'technology', 'entertainment', 'sports', 'science', 'health']
    category = categories[2]  # Change this to the desired category
    url = f"https://gnews.io/api/v4/top-headlines?category={category}&lang=en&country=us&max=10&apikey={apikey}"

    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
        print(json.dumps(data['articles'], indent=4))
        articles = data["articles"]

        for i in range(len(articles)):
            # articles[i].title
            print(f"Title: {articles[i]['title']}")
            # articles[i].description
            print(f"Description: {articles[i]['description']}")
            # You can replace {property} below with any of the article properties returned by the API.
            # articles[i].{property}
            # print(f"{articles[i]['{property}']}")

gnews_get_headlines()
