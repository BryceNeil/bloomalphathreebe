
from pydantic import BaseModel
from io import BytesIO
import requests

class ImageDescription(BaseModel):
    description: str

import requests

def search_and_download_image(description):
    print("Searching and downloading image...")

    # Your Custom Search JSON API key and CSE ID
    API_KEY = 'AIzaSyCM25-G78V03FwcHA-OspNjOpej_qgwTE8'
    CSE_ID = 'c5548d48e52cc4107'

    # Google Custom Search JSON API endpoint
    API_ENDPOINT = 'https://www.googleapis.com/customsearch/v1'
    
    # Parameters for the API request
    params = {
        'key': API_KEY,
        'cx': CSE_ID,
        'q': f'Diagram of a {description}', # Be sure the description has the right information
        'searchType': 'image',
        'num': 1  # Number of images to return (1-10)
    }

    try:
        response = requests.get(API_ENDPOINT, params=params)
        response.raise_for_status()

        # Parsing the response to get the first image URL
        search_results = response.json()
        if not search_results.get('items'):
            raise ValueError("No images found for the given description.")

        image_url = search_results['items'][0]['link']
        print("DEBUG IMG URL: ", image_url)
        return download_image(image_url)

    except requests.RequestException as e:
        print(f"Error during image search: {e}")
        raise

    except ValueError as e:
        print(e)
        raise



def download_image(url):
    print("Downloading image...")
    response = requests.get(url)
    if response.status_code == 200:
        print("Image downloaded")
        return BytesIO(response.content)
    else:
        raise Exception("Failed to download image")