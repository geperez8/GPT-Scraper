# Scraping using method from here: https://www.zenrows.com/blog/selenium-cloudflare-bypass#seleniumbase
# Selenium base API for reference: https://seleniumbase.io/help_docs/method_summary/#seleniumbase-methods-api-reference

import random
from datetime import datetime, timedelta
from time import sleep
import requests
import json
import pandas as pd
from seleniumbase import Driver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import hashlib
import poplib
from email import parser
from newspaper import Article

# Base class for scraping - The ChatGPT and Perplexity Scrapers will inherit from this class
class BaseScraper:
    def __init__(self):
        # Set headless=False for debug so you can see what's happening in the browser, or headless=True to run it on a server
        self.driver = Driver(uc=True, headless=False)
        #self.driver.maximize_window()
        self.driver.set_window_size(1400, 1400)

    def __del__(self):
        if self.driver:
            self.driver.quit()

    def query(self, query):
        return None

    def scrape(self):
        return None

    def close(self):
        if self.driver:
            self.driver.quit()


class ChatGPTScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.url = "https://chatgpt.com/"
        

    # Prep the dataframe by adding the columns that will store the scraped data
    def prep_data(self, df):
        # Add columns to the dataframe to store the scraped data
        # Prompt is the input prompt that is used to query the model
        # Response_text is the response from the model
        # Response_citations is a JSON of the citations that the model cited in the response
        # Response_search_results is a JSON of the search results that the model cited in the response
        df[["prompt", "response_text", "response_citations", "response_search_results", "screenshot_path", "request_time"]] = None
        return df
        
    # Query the ChatGPT model with a prompt
    def query(self, query):
        try:
            self.driver.uc_open(self.url)
            sleep(random.uniform(1, 2))
            self.driver.send_keys("#prompt-textarea", query)
            sleep(random.uniform(1, 3))
            request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.driver.send_keys("#prompt-textarea", Keys.ENTER)
            sleep(random.uniform(20, 25))
            return request_time
            #sources_button = self.driver.find_element(By.CSS_SELECTOR, ".not-prose")
            
        except Exception as e:
            print(f"Exception{e}")
        
        return request_time

    # Collect the data from the ChatGPT model for one row of the input data frame this is applied to
    def scrape(self, row):
        #add a delay here so we don't hit the gpt-4o limit of 80 messages / 3 hrs. 
        sleep(random.uniform(110, 130))
        
        try:
            # Send the prompt to ChatGPT
            PROMPT = f'Tell me about "{row["headline"]}"'
            print (PROMPT)
            row["request_time"] = self.query(PROMPT)
            row["prompt"] = PROMPT

            # Extract the response HTML
            row["response_text"] = self.parse_response()
            
            # Open sources tab
            self.driver.uc_click("button.not-prose.group\\/footnote")
            #self.driver.click("//div[text()='Sources']/parent::button", by="xpath")
            sleep(random.uniform(3, 5))

            # And then extract all of the source information broken into citations and search results
            try:
                citations = self.parse_sources("Citations")
                row["response_citations"] = json.dumps(citations)
                
                search_results = self.parse_sources("More")
                row["response_search_results"] = json.dumps(search_results)
            except Exception as e:
                print(f"Exception {e}")
            
            print (row)
            
        except Exception as e:
            print(f"Exception {e}")

        return row
    
    # Helper to extract the response from the ChatGPT model
    def parse_response(self):
        response = self.driver.find_element(By.CSS_SELECTOR, ".markdown.prose").get_attribute("innerHTML")

        return response
    
    # Helper to extract the sources from the ChatGPT model
    def parse_sources(self, header_text):
        results = []

        # Find the section based on the header text
        header_element = self.driver.find_element(By.XPATH, f"//div[text()='{header_text}']")
        section = header_element.find_element(By.XPATH, "..")
        links = section.find_elements(By.TAG_NAME, "a")
        
        for link in links:
            url = link.get_attribute("href")
            url = url.replace("?utm_source=chatgpt.com", "")
            text_elements = link.find_elements(By.TAG_NAME, "div")
            headline = text_elements[1].text
            snippet = text_elements[2].text
            # Extract the date (assumes the date is the first part of the snippet)
            #date = snippet.split(" — ")[0] if " — " in snippet else ""
            #remaining_snippet = snippet[len(date) + 3:] if date else snippet
            results.append({
                "url": url,
                "headline": headline,
                "snippet": snippet,
            })
        return results




# Demo function to show how to instantiate and use the ChatGPTScraper.
def ChatGPTScraperTest():
    # Create a test dataframe -- just need a column a headlines for the prompt pattern used here
    headlines = ["Judge orders Trump administration to preserve Signal communications about Yemen operation"]
    df = pd.DataFrame(headlines, columns=["headline"])

    # Create a scraper instance
    scraper = ChatGPTScraper()

    # Prep the dataframe by adding the columns that will store the scraped data
    df = scraper.prep_data(df)

    # Call the scraper on each row of the dataframe
    df = df.apply(scraper.scrape, axis=1)

    # Close the scraper
    scraper.close()

    # Output the results to a CSV file with the new columns
    df.to_csv("test-scrape.csv", index=False)

ChatGPTScraperTest()

