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
from dotenv import load_dotenv
import uuid
import feedparser
import os

load_dotenv()

# Initialize with a default that does nothing
def _default_log(message, level="INFO"):
    pass

# Global variable that will be replaced with the real logger
log = _default_log

def initialize_logger(folder_path):
    """Initialize the global logger"""
    global log
    
    # Create the log file
    log_filename = f"scraper_log_{datetime.now().strftime('%m-%d-%y')}.log"
    log_path = os.path.join(folder_path, log_filename)
    timestamp = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    first_line = f"===== SCRAPER RUN STARTED AT {timestamp} =====\n\n"
    
    # Initialize the log file with a header
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(first_line)

    print(first_line)
    
    # Replace the global log function with the real implementation
    def actual_log(message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        # Print to console
        print(formatted_message)
        
        # Write to log file
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(formatted_message + "\n")
    
    # Replace the global function
    log = actual_log
    log("Logger initialized successfully", "INFO")
    
    return log_path

def finalize_logger(log_path):
    """Write final log message and perform any cleanup"""
    log("Finalizing logger and ending scraper session", "INFO")
    last_line = f"======= END OF LOG SESSION {datetime.now().strftime('%m-%d-%Y %H:%M:%S')} ======="
    if log != _default_log:  # Only if initialized
        with open(log_path, "a", encoding="utf-8") as log_file:  # Changed from "w" to "a" to append instead of overwrite
            log_file.write(last_line)
        print(last_line)

def get_google_trends_topics():
    log("Fetching Google Trends topics", "INFO")
    # Parse the RSS feed from Google Trends
    # The URL is for US trends; you can change the 'geo' parameter for other countries
    rss_url = "https://trends.google.com/trending/rss?geo=US"
    try:
        feed = feedparser.parse(rss_url)
        topics = []

        for entry in feed.entries:
            # Extract the title/topic and add it to the list
            topics.append(entry.title)
        
        log(f"Successfully retrieved {len(topics)} trending topics", "INFO")
        return topics
    except Exception as e:
        log(f"Error fetching Google Trends topics: {str(e)}", "ERROR")
        return []

def create_date_folder():
    log("Creating date-based folder structure", "INFO")
    try:
        # Get current date in YYYY-MM-DD format
        current_date = datetime.now().strftime("%m-%d-%Y")
        
        # Create the folder name using the date
        folder_path = os.path.join("data", current_date)
        
        # Create the folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            # Create subfolders for images and CSV files
            os.makedirs(os.path.join(folder_path, "screenshots"))
            log(f"Created folder structure: {folder_path}/screenshots", "INFO")
        else:
            log(f"Using existing folder structure: {folder_path}", "INFO")
        
        return folder_path, current_date
    except Exception as e:
        log(f"Error creating folders: {str(e)}", "ERROR")
        return None, None


# Base class for scraping - The ChatGPT and Perplexity Scrapers will inherit from this class
class BaseScraper:
    def __init__(self):
        log("Initializing BaseScraper", "INFO")
        try:
            # Set headless=False for debug so you can see what's happening in the browser, or headless=True to run it on a server
            self.driver = Driver(uc=True, headless=False, no_sandbox=True)
            #self.driver.maximize_window()
            self.driver.set_window_size(1400, 1400)
            log("WebDriver initialized successfully", "INFO")
        except Exception as e:
            log(f"Failed to initialize WebDriver: {str(e)}", "ERROR")
            raise e

    # Destructor to close the driver when the object is deleted
    def __del__(self):
        if hasattr(self, 'driver') and self.driver:
            log("Closing WebDriver in destructor", "DEBUG")
            self.driver.quit()

    # This is a placeholder for thefunction that will provide a query to the model
    def query(self, query):
        log(f"Base query method called with: {query[:50]}...", "DEBUG")
        return None

    # This is a placeholder for the function that will scrape the data from the model
    def scrape(self):
        log("Base scrape method called", "DEBUG")
        return None

    # Destructor to close the driver when the object is deleted
    def close(self):
        if hasattr(self, 'driver') and self.driver:
            log("Explicitly closing WebDriver", "INFO")
            self.driver.quit()


class ChatGPTScraper(BaseScraper):

    # Constructor for the ChatGPT scraper
    def __init__(self, date_folder):
        log("Initializing ChatGPTScraper", "INFO")
        # Initialize the base class
        super().__init__()

        # Set the URL for the ChatGPT model interface
        self.url = "https://chatgpt.com/"
        self.date_folder = date_folder
        log(f"ChatGPTScraper initialized with date_folder: {date_folder}", "INFO")

    # Prep the dataframe by adding the columns that will store the scraped data
    def prep_data(self, df):
        log("Preparing dataframe with necessary columns", "INFO")
        # Add columns to the dataframe to store the scraped data
        # Prompt is the input prompt that is used to query the model
        # Response_text is the response from the model
        # Response_citations is a JSON of the citations that the model cited in the response
        # Response_search_results is a JSON of the search results that the model cited in the response
        # Screenshot_path is the path to the screenshot of the response
        df[["id","prompt", "response_text", "response_citations", "response_search_results", "response_screenshot_path", "citation_screenshot_path", "request_time"]] = None
        log(f"Dataframe prepared with {len(df)} rows", "INFO")
        return df
        
    # Query the ChatGPT model with a prompt
    def query(self, query):
        log(f"Querying ChatGPT model with: {query[:50]}...", "INFO")
        try:
            # open the ChatGPT model interface
            log("Opening ChatGPT URL", "DEBUG")
            self.driver.uc_open(self.url)
            # wait for the page to load/human interaction simulation
            sleep_time = random.uniform(1, 6)
            log(f"Waiting for {sleep_time:.2f}s for page to load", "DEBUG")
            sleep(sleep_time)

            # get rid of the popups that appear on the page
            log("Attempting to close popups", "DEBUG")
            self.get_rid_of_popup()

            # click on the "web search" button to enable web search
            log("Enabling web search", "INFO")
            self.driver.click("button[aria-label='Search']", by="css selector")

            # wait for the page to load/human interaction simulation
            sleep_time = random.uniform(1, 4)
            log(f"Waiting for {sleep_time:.2f}s after enabling search", "DEBUG")
            sleep(sleep_time)

            # Populate the prompt text area with the query
            log("Entering query in text area", "DEBUG")
            self.driver.send_keys("#prompt-textarea", query)
            # wait for the page to load/human interaction simulation
            sleep_time = random.uniform(1, 3)
            log(f"Waiting for {sleep_time:.2f}s before submitting", "DEBUG")
            sleep(sleep_time)

            # log the time the request was made
            request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log(f"Request time recorded: {request_time}", "INFO")

            # Click the submit button to send the query
            log("Submitting query", "INFO")
            self.driver.send_keys("#prompt-textarea", Keys.ENTER)
            # wait for the page to load/human interaction simulation
            sleep_time = random.uniform(20, 25)
            log(f"Waiting for {sleep_time:.2f}s for response to load", "INFO")
            sleep(sleep_time)

            #return the request time
            return request_time
            #sources_button = self.driver.find_element(By.CSS_SELECTOR, ".not-prose")
            
        except Exception as e:
            log(f"Exception during query execution: {str(e)}", "ERROR")
        
        return request_time

    # Collect the data from the ChatGPT model for one row of the input data frame this is applied to
    def scrape(self, row):
        log(f"Starting scrape for topic: {row['trending_topic']}", "INFO")
        # add a delay here so we don't hit the -4o limit of 80 messages / 3 hrs. 
        sleep_time = random.uniform(110, 130)
        log(f"Rate limiting: sleeping for {sleep_time:.2f}s before next request", "INFO")
        sleep(sleep_time)
        
        try:
            # Establish an ID for the row
            row_id = str(uuid.uuid4())[:8]
            row["id"] = row_id
            log(f"Assigned row ID: {row_id}", "DEBUG")

            # Send the prompt to ChatGPT
            # Create prompt
            PROMPT = f'What does the internet say about {row["trending_topic"]} in the past week. '
            log(f"Created prompt: {PROMPT}", "INFO")

            # log request time and prompt
            log("Sending query to ChatGPT", "INFO")
            row["request_time"] = self.query(PROMPT)
            row["prompt"] = PROMPT

            # Extract the response HTML
            log("Parsing response text", "INFO")
            row["response_text"] = self.parse_response()
            log(f"Response length: {len(row['response_text'])} characters", "DEBUG")

            # Take a screenshot of the response
            log("Taking screenshot of response", "INFO")
            row["response_screenshot_path"] = self.take_screenshot(row_id, "response")
            log(f"Response screenshot saved to: {row['response_screenshot_path']}", "DEBUG")
            
            # Open sources tab
            log("Opening sources tab", "INFO")
            try:
                self.driver.uc_click("button.not-prose.group\\/footnote")
                sleep_time = random.uniform(3, 5)
                log(f"Waiting for {sleep_time:.2f}s for sources tab to load", "DEBUG")
                sleep(sleep_time)
            except Exception as e:
                log(f"Error opening sources tab: {str(e)}", "WARNING")

            # Take a screenshot of the sources
            log("Taking screenshot of citations", "INFO")
            row["citation_screenshot_path"] = self.take_screenshot(row_id, "citations")
            log(f"Citations screenshot saved to: {row['citation_screenshot_path']}", "DEBUG")

            # And then extract all of the source information broken into citations and search results
            try:
                # Get the citations and search results from the sources tab
                log("Parsing citation sources", "INFO")
                citations = self.parse_sources("Citations")
                row["response_citations"] = json.dumps(citations)
                log(f"Found {len(citations)} citations", "INFO")
                
                # Get the additional search results from the sources tab
                log("Parsing additional search results", "INFO")
                search_results = self.parse_sources("More")
                row["response_search_results"] = json.dumps(search_results)
                log(f"Found {len(search_results)} additional search results", "INFO")
            except Exception as e:
                log(f"Error parsing sources: {str(e)}", "ERROR")
            
            log(f"Completed scraping for topic: {row['trending_topic']}", "INFO")
            
        except Exception as e:
            log(f"Exception during scraping: {str(e)}", "ERROR")

        return row
    
    # Helper to extract the response from the ChatGPT model
    # gets all the HTML from the response area and returns it as a string
    def parse_response(self):
        log("Parsing response HTML", "DEBUG")
        try:
            # get the HTML of the response area
            response = self.driver.find_element(By.CSS_SELECTOR, ".markdown.prose").get_attribute("innerHTML")
            log(f"Successfully extracted response HTML ({len(response)} characters)", "DEBUG")
            # return the response HTML as a string
            return response
        except Exception as e:
            log(f"Error parsing response: {str(e)}", "ERROR")
            return ""
    
    def take_screenshot(self, id, type):
        log(f"Taking screenshot of type: {type} for ID: {id}", "DEBUG")
        try:
            # create path to the screenshot folder
            image_name = f"{id}_{type}.png"
            screenshot_path = os.path.join(self.date_folder, "screenshots", image_name)

            # take a screenshot
            self.driver.save_screenshot(screenshot_path)
            log(f"Screenshot saved to {screenshot_path}", "DEBUG")
            
            # return the path to the screenshot
            return screenshot_path
        except Exception as e:
            log(f"Error taking screenshot: {str(e)}", "ERROR")
            return None
    
    # this is a helper function to close the popups that appear on the page
    def get_rid_of_popup(self):
        log("Attempting to close popup", "DEBUG")
        # Close the popups that appear on the page
        try:
            self.driver.click("button[aria-label='Close']", by="css selector")
            sleep_time = random.uniform(1, 2)
            log(f"Popup closed, waiting {sleep_time:.2f}s", "DEBUG")
            sleep(sleep_time)
        except Exception as e:
            log(f"No popup found or couldn't close: {str(e)}", "DEBUG")

    # Helper to extract the sources from the ChatGPT model
    def parse_sources(self, header_text):
        log(f"Parsing sources from section: {header_text}", "DEBUG")
        results = []

        try:
            # Find the section based on the header text
            log(f"Looking for header element: '{header_text}'", "DEBUG")
            header_element = self.driver.find_element(By.XPATH, f"//div[text()='{header_text}']")

            # Get the parent section of the header element
            section = header_element.find_element(By.XPATH, "..")
            log("Found header section", "DEBUG")

            # Get all the links in the section
            links = section.find_elements(By.TAG_NAME, "a")
            log(f"Found {len(links)} links in section", "DEBUG")

            # Iterate through the links and extract the URL and text
            for i, link in enumerate(links):
                try:
                    # Get the URL and remove the tracking parameter
                    url = link.get_attribute("href")
                    url = url.replace("?utm_source=ChatGPT.com", "")

                    # Get the text elements within the link
                    text_elements = link.find_elements(By.TAG_NAME, "div")
                    
                    # extract the trending_topic and snippet from the text elements
                    trending_topic = text_elements[1].text
                    snippet = text_elements[2].text

                    # compile the results into a dictionary
                    results.append({
                        "url": url,
                        "trending_topic": trending_topic,
                        "snippet": snippet,
                    })
                    log(f"Parsed source {i+1}: {trending_topic[:30]}...", "DEBUG")
                except Exception as e:
                    log(f"Error parsing link {i+1}: {str(e)}", "WARNING")
            
            # return the dictionary of compiled results
            log(f"Successfully parsed {len(results)} sources", "INFO")
            return results
        except Exception as e:
            log(f"Error finding sources section '{header_text}': {str(e)}", "ERROR")
            return results
    
    def login(self, email, password):
        log(f"Attempting to login with email: {email}", "INFO")
        try:
            # Navigate to the main page
            self.driver.uc_open(self.url)
            log("Opened login URL", "DEBUG")

            # wait for page to load/human interaction simulation
            sleep_time = random.uniform(1, 3)
            log(f"Waiting {sleep_time:.2f}s for page to load", "DEBUG")
            sleep(sleep_time)

            # Click on login button
            log("Clicking login button", "DEBUG")
            button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.relative.btn-primary.btn-large.w-full")
            button.click()

            # wait for page to load/human interaction simulation
            sleep_time = random.uniform(20, 30)
            log(f"Waiting {sleep_time:.2f}s for login page to load", "INFO")
            sleep(sleep_time)
            
            # Find the email input field by its ID and input the email
            log("Entering email address", "DEBUG")
            email_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='email'][type='email']")
            email_input.clear()
            email_input.send_keys(email)

            # wait for page to load/human interaction simulation
            sleep_time = random.uniform(1, 3)
            log(f"Waiting {sleep_time:.2f}s before continuing", "DEBUG")
            sleep(sleep_time)

            #Find the continue button and click it
            log("Clicking continue button after email", "DEBUG")
            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Continue']"))
            )
            button.click()
            
            # wait for page to load/human interaction simulation
            sleep_time = random.uniform(1, 3)
            log(f"Waiting {sleep_time:.2f}s for password field", "DEBUG")
            sleep(sleep_time)

            # Find the email input field by its ID and input the password
            log("Entering password", "DEBUG")
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='password'][type='password']")
            password_input.clear()
            password_input.send_keys(password)

            # wait for page to load/human interaction simulation
            sleep_time = random.uniform(3, 8)
            log(f"Waiting {sleep_time:.2f}s before final submission", "DEBUG")
            sleep(sleep_time)

            #Find the continue button and click it
            log("Clicking continue button after password", "DEBUG")
            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Continue']"))
            )
            button.click()

            # We have now successfully logged in
            log("Login successful", "INFO")
            return True
        
        except Exception as e:
            log(f"Login failed: {str(e)}", "ERROR")
            return False

# Demo function to show how to instantiate and use the ChatGPTScraper.
def ChatGPTScraperTest():
    global log
    log("Starting ChatGPTScraperTest", "INFO")
    
    # Create a date folder to store the results
    log("Creating date folder for results", "INFO")
    folder_path, date = create_date_folder()
    if not folder_path:
        log("Failed to create folder structure, aborting test", "ERROR")
        return

    # Initialize the logger
    log_path = initialize_logger(folder_path)
    log(f"Logger initialized at {log_path}", "INFO")

    # Create a test dataframe -- just need a column a trending_topics for the prompt pattern used here
    # What trending_topics will we use? -> We are using trending topics from Google Trends
    # Get trending topics from Google Trends
    log("Getting trending topics from Google Trends", "INFO")
    topics = get_google_trends_topics()
    if not topics:
        log("No trending topics found, aborting test", "ERROR")
        return
        
    log(f"Using first trending topic: {topics[0]}", "INFO")
    df = pd.DataFrame(topics, columns=["trending_topic"])

    log("Creating Scraper instance", "INFO")
    # Create a scraper instance
    try:
        scraper = ChatGPTScraper(folder_path)
    except Exception as e:
        log(f"Failed to create scraper: {str(e)}", "ERROR")
        finalize_logger(log_path)
        return

    # Prep the dataframe by adding the columns that will store the scraped data
    log("Preparing dataframe for scraping", "INFO")
    df = scraper.prep_data(df)

    log("Beginning Scraping Process", "INFO")
    # Call the scraper on each row of the dataframe
    try:
        df = df.apply(scraper.scrape, axis=1)
        log("Scraping completed successfully", "INFO")
    except Exception as e:
        log(f"Error during scraping process: {str(e)}", "ERROR")

    # # Close the scraper
    log("Closing scraper", "INFO")
    try:
        scraper.close()
    except Exception as e:
        log(f"Error closing scraper: {str(e)}", "WARNING")

    # Output the results to a CSV file with the new columns
    log("Saving results to CSV", "INFO")
    try:
        csv_name = os.path.join(folder_path, f'{date}_scrape_results.csv')
        log(f"Saving results to {csv_name}", "INFO")
        df.to_csv(csv_name, index=False)
        log(f"Successfully saved results to CSV: {len(df)} rows", "INFO")
    except Exception as e:
        log(f"Error saving results to CSV: {str(e)}", "ERROR")

    log("ChatGPTScraper test completed", "INFO")
    finalize_logger(log_path)

if __name__ == "__main__":
    ChatGPTScraperTest()