# Scraping using method from here: https://www.zenrows.com/blog/selenium-cloudflare-bypass#seleniumbase
# Selenium base API for reference: https://seleniumbase.io/help_docs/method_summary/#seleniumbase-methods-api-reference

import random
from datetime import datetime
from time import sleep
import json
import pandas as pd
from seleniumbase import Driver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import feedparser
import os

load_dotenv()

def get_google_trends_topics():
    # Parse the RSS feed from Google Trends
    # The URL is for US trends; you can change the 'geo' parameter for other countries
    rss_url = "https://trends.google.com/trending/rss?geo=US"
    feed = feedparser.parse(rss_url)

    topics= []

    for entry in feed.entries:
        # Extract the title/topic and add it to the list
        topics.append(entry.title)

    return topics

def pretty_html(html_str):
    soup = BeautifulSoup(html_str, "html.parser")
    print(soup.prettify())

def create_date_folder():
    # Get current date in YYYY-MM-DD format
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Create the folder name using the date
    folder_name = current_date
    
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        # Create subfolders for images and CSV files
        os.makedirs(os.path.join(folder_name, "images"))
        os.makedirs(os.path.join(folder_name, "csv_files"))
        print(f"Created folder structure: {folder_name}/images and {folder_name}/csv_files")
    
    return folder_name


# Base class for scraping - The ChatGPT and Perplexity Scrapers will inherit from this class
class BaseScraper:
    def __init__(self):
        # Set headless=False for debug so you can see what's happening in the browser, or headless=True to run it on a server
        self.driver = Driver(uc=True, headless=False, no_sandbox=True)
        #self.driver.maximize_window()
        self.driver.set_window_size(1400, 1400)

    # Destructor to close the driver when the object is deleted
    def __del__(self):
        if self.driver:
            self.driver.quit()

    # This is a placeholder for thefunction that will provide a query to the model
    def query(self, query):
        return None

    # This is a placeholder for the function that will scrape the data from the model
    def scrape(self):
        return None

    # Destructor to close the driver when the object is deleted
    def close(self):
        if self.driver:
            self.driver.quit()


class ChatGPTScraper(BaseScraper):

    # Constructor for the ChatGPT scraper
    def __init__(self):
        # Initialize the base class
        super().__init__()

        # Set the URL for the ChatGPT model interface
        self.url = "https://chatgpt.com/"

    # Prep the dataframe by adding the columns that will store the scraped data
    def prep_data(self, df):
        # Add columns to the dataframe to store the scraped data
        # Prompt is the input prompt that is used to query the model
        # Response_text is the response from the model
        # Response_citations is a JSON of the citations that the model cited in the response
        # Response_search_results is a JSON of the search results that the model cited in the response
        # ? Screenshot_path is the path to the screenshot of the response
        df[["prompt", "response_text", "response_citations", "response_search_results", "screenshot_path", "request_time"]] = None
        return df
        
    # Query the ChatGPT model with a prompt
    def query(self, query):
        try:
            # open the ChatGPT model interface
            self.driver.uc_open(self.url)
            # wait for the page to load/human interaction simulation
            sleep(random.uniform(1, 6))

            # get rid of the popups that appear on the page
            self.get_rid_of_popup()

            # click on the "web search" button to enable web search
            self.driver.click("button[aria-label='Search']", by="css selector")

            # wait for the page to load/human interaction simulation
            sleep(random.uniform(1, 4))

            # Populate the prompt text area with the query
            self.driver.send_keys("#prompt-textarea", query)
            # wait for the page to load/human interaction simulation
            sleep(random.uniform(1, 3))

            # log the time the request was made
            request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Click the submit button to send the query
            self.driver.send_keys("#prompt-textarea", Keys.ENTER)
            # wait for the page to load/human interaction simulation
            sleep(random.uniform(20, 25))

            #return the request time
            return request_time
            #sources_button = self.driver.find_element(By.CSS_SELECTOR, ".not-prose")
            
        except Exception as e:
            print(f"Exception{e}")
        
        return request_time

    # Collect the data from the ChatGPT model for one row of the input data frame this is applied to
    def scrape(self, row):
        #add a delay here so we don't hit the gpt-4o limit of 80 messages / 3 hrs. 
        # ! Only comment out if we are testing out a single prompt
        sleep(random.uniform(110, 130))
        
        try:
            # Send the prompt to ChatGPT

            # Create prompt
            PROMPT = f'Tell me about "{row["headline"]}"'
            print(PROMPT)

            # log request time and prompt
            row["request_time"] = self.query(PROMPT)
            row["prompt"] = PROMPT

            # Extract the response HTML
            row["response_text"] = self.parse_response()

            # take a screenshot of the response area
            self.driver.save_screenshot('response.png')
            
            # Open sources tab
            self.driver.uc_click("button.not-prose.group\\/footnote")
            #self.driver.click("//div[text()='Sources']/parent::button", by="xpath")
            sleep(random.uniform(3, 5))

            # And then extract all of the source information broken into citations and search results
            try:
                # Get the citations and search results from the sources tab
                citations = self.parse_sources("Citations")
                row["response_citations"] = json.dumps(citations)
                
                # Get the additional search results from the sources tab
                search_results = self.parse_sources("More")
                row["response_search_results"] = json.dumps(search_results)
            except Exception as e:
                print(f"Exception {e}")
            
            print (row)
            
        except Exception as e:
            print(f"Exception {e}")

        return row
    
    # Helper to extract the response from the ChatGPT model
    # gets all the HTML from the response area and returns it as a string
    def parse_response(self):
        # get the HTML of the response area
        response = self.driver.find_element(By.CSS_SELECTOR, ".markdown.prose").get_attribute("innerHTML")

        # return the response HTML as a string
        return response
    
    # this is a helper function to close the popups that appear on the page
    def get_rid_of_popup(self):
        # Close the popups that appear on the page
        try:
            self.driver.click("button[aria-label='Close']", by="css selector")
            sleep(random.uniform(1, 2))
        except Exception as e:
            print(f"Pop up not found: \n{e}")

    # Helper to extract the sources from the ChatGPT model
    def parse_sources(self, header_text):
        results = []

        # Find the section based on the header text
        header_element = self.driver.find_element(By.XPATH, f"//div[text()='{header_text}']")

        # Get the parent section of the header element
        section = header_element.find_element(By.XPATH, "..")

        # Get all the links in the section
        links = section.find_elements(By.TAG_NAME, "a")

        # Iterate through the links and extract the URL and text
        for link in links:
            # Get the URL and remove the tracking parameter
            url = link.get_attribute("href")
            url = url.replace("?utm_source=chatgpt.com", "")

            # Get the text elements within the link
            text_elements = link.find_elements(By.TAG_NAME, "div")
            
            # extract the headline and snippet from the text elements
            headline = text_elements[1].text
            snippet = text_elements[2].text

            # compile the results into a dictionary
            results.append({
                "url": url,
                "headline": headline,
                "snippet": snippet,
            })
        
        # return the dictionary of compiled results
        return results





# Demo function to show how to instantiate and use the ChatGPTScraper.
def ChatGPTScraperTest():
    # Create a test dataframe -- just need a column a headlines for the prompt pattern used here
    # What headlines will we use? -> We are using trending topics from Google Trends
    # Get trending topics from Google Trends
    topics = get_google_trends_topics()
    df = pd.DataFrame(topics, columns=["headline"])

    # Create a scraper instance
    scraper = ChatGPTScraper()

    # Prep the dataframe by adding the columns that will store the scraped data
    df = scraper.prep_data(df)

    # Call the scraper on each row of the dataframe
    df = df.apply(scraper.scrape, axis=1)

    # # Close the scraper
    scraper.close()

    # Output the results to a CSV file with the new columns
    # ? Single csv vs multiple csvs?
    # ? What should the name be?
    df.to_csv("test-scrape.csv", index=False)

ChatGPTScraperTest()

