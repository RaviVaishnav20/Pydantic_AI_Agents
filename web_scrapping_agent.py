import datetime
import pandas as pd
from httpx import Client
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from pydantic_ai.exceptions import UnexpectedModelBehavior
from load_models import OPENAI_MODEL # GEMINI_MODEL
import os 

class Product(BaseModel):
    bramd_name: str = Field(title='Brand Name', description='The brand name of the product')
    product_name: str = Field(title='Product Name', description='The name of the product')
    price: str | None = Field(title='Price', description='The price of the product')
    rating_count: int | None = Field(title='Rating Count', description='The rating count of the product')

class Results(BaseModel):
    dataset: list[Product] = Field(title='Dataset', description='The list of products')

web_scraping_agent = Agent(
    name='Web Scraping Agent',
    model=OPENAI_MODEL,
    system_prompt=("""
    Your task is to convert list of string to dictionaries.

    Step 1. Fetch the HTML text from the given URL using the fetch_html_text() function
    Step 2. Takes the output from the Step 1 and clean it up for the final output
    """),

    retries=2,
    output_type=Results,
    model_settings= ModelSettings(
        max_tokens=8000,
        temperature=0.1
    ),
)

@web_scraping_agent.tool_plain(retries=1)
def fetch_html_text(url: str) -> str:
    """
    Fetches the HTML text from a given URL.
    For debugging, it can also read from 'soup.txt' if the file exists.
    """
    static_file_path = 'soup.txt'
    html_content = ""

    # Option 1: Read from static file if it exists (for debugging)
    if os.path.exists(static_file_path):
        print(f"Reading HTML from local file: {static_file_path}")
        try:
            with open(static_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            print(f'Successfully loaded HTML from {static_file_path}')
        except Exception as e:
            print(f"Error reading {static_file_path}: {e}")
            # Fallback to web fetch if reading fails
            html_content = ""

    # Option 2: Fetch from URL if static file doesn't exist or reading failed
    if not html_content:
        print("Calling URL:", url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5',
        }
        with Client(headers=headers) as client:
            response = client.get(url, timeout=20)
            if response.status_code != 200:
                return f"Failed to fetch the HTML text from {url}. Status code: {response.status_code}"
            html_content = response.text

            # Always save the fetched HTML to soup.txt for future debugging
            with open(static_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f'Fetched HTML saved to {static_file_path}')

    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        # This line will now correctly process either the fetched HTML or the loaded static file HTML
        return soup.get_text().replace('\n','').replace('\r','')
    else:
        return "No HTML content to process."

# @web_scraping_agent.tool_plain(retries=1)
# def fetch_html_text(url: str) -> str:
#     """
#     Fetches the HTML text from a given URL

#     args:
#         url: str - The page's URL to fetch the HTML text from

#     returns:
#         str: The HTML text from the given URL
#     """

#     print("Calling URL:", url)
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#         'Accept-Language': 'en-US, en;q=0.5',
#     }
#     with Client(headers=headers) as client:
#         response = client.get(url, timeout=20)
#         if response.status_code != 200:
#             return f"Failed to fetch the HTML text from {url}. Status code: {response.status_code}"

#         soup = BeautifulSoup(response.text, 'html.parser')
#         with open('soup.txt', 'w', encoding='utf-8') as f:
#             f.write(soup.get_text())
#         print('Soup file saved')
#         return soup.get_text().replace('\n','').replace('\r','')

@web_scraping_agent.output_validator
def validate_result(result: Results) -> Results:
    print('Validating result')
    if isinstance(result, Results):
        print('Validation passed')
        return result
    print("Validation failed")
    return None

def main() -> None:
    prompt = 'https://www.flipkart.com/search?q=laptop&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off&p%5B%5D=facets.price_range.from%3D75000&p%5B%5D=facets.price_range.to%3DMax&sort=price_desc'
    # prompt = 'https://www.noon.com/uae-en/search/?q=macbook&originalQuery=macbook&sort[by]=price&sort[dir]=desc&limit=50&page=1&isCarouselView=false'
    try:
        response = web_scraping_agent.run_sync(prompt)
        if response is None:
            # raise UnexpectedModelBehavior('No data returned from the model')
            return None

        print('-' * 50)
        print('Input_tokens:', response.usage().request_tokens)
        print('Output_tokens:', response.usage().response_tokens)
        print('Total_tokens:', response.usage().total_tokens)
        print(response)
        lst = []
        for item in response.output.dataset:
            lst.append(item.model_dump())

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        df = pd.DataFrame(lst)
        df.to_csv(f"product_listings_{timestamp}.csv", index=False)
    except UnexpectedModelBehavior as e:
        print(e)

if __name__ == "__main__":
    main()
            