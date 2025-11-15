#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from time import sleep
from tqdm import tqdm
import socket
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ジャンルとエリアの設定
GENRE = "グルメ"
AREA = "奈良県"
BASE_URL = f"https://www.mapion.co.jp/s/q={GENRE}%20{AREA}/t=spot"
ADD_URL = "/?area=29201"

def robust_get(url, max_retries=3, timeout=30):
    """Robust get function with retry logic and multiple fallbacks"""
    session = requests.Session()
    
    # Try different headers to avoid blocking
    headers_list = [
        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    ]
    
    for attempt in range(max_retries):
        try:
            # Try different headers
            headers = headers_list[attempt % len(headers_list)]
            
            # Add more parameters to handle connection issues
            response = session.get(
                url,
                headers=headers,
                timeout=timeout,
                verify=False,  # Skip SSL verification if needed
                allow_redirects=True
            )
            
            if response.status_code == 200:
                return response
            else:
                print(f"Status code {response.status_code} on attempt {attempt + 1}")
                
        except (requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                socket.gaierror) as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                sleep(2 ** attempt)  # Exponential backoff
            else:
                raise Exception(f"Failed to connect after {max_retries} attempts: {str(e)}")
    
    return None

def scrape_with_retry(urls):
    """Scrape with error handling for connection issues"""
    pattern = r"^0\d{1,4}-\d{1,4}-\d{3,4}$|^0\d{9,10}$"
    results = []
    failed_urls = []
    
    for i, url in enumerate(tqdm(urls, desc="Scraping pages")):
        try:
            print(f"\nProcessing URL {i+1}/{len(urls)}: {url}")
            
            # Test connection first
            try:
                ip = socket.gethostbyname('www.mapion.co.jp')
                print(f"DNS resolved: www.mapion.co.jp -> {ip}")
            except socket.gaierror as e:
                print(f"DNS resolution failed: {e}")
                failed_urls.append((url, str(e)))
                continue
            
            response = robust_get(url)
            if response is None:
                print(f"Failed to get response for URL: {url}")
                failed_urls.append((url, "No response"))
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            section = soup.find("div", id="NumberSection")
            
            if section is None:
                print(f"Could not find NumberSection in page {url}")
                # Try alternative approach - maybe the page structure changed
                cards = soup.find_all("dl")
            else:
                cards = section.find_all("dl")
            
            items = []
            for card in cards:
                # Extract name
                name = " - "
                try:
                    name = card.find('a').text.replace('\u3000', ' ').strip()
                except:
                    name = " - "
                
                # Extract address
                address = " - "
                try:
                    address = card.find_all('dd')[2].text
                except:
                    try:
                        address = card.find("li", class_="dataAdr").text.strip()
                    except:
                        address = " - "
                
                # Extract phone
                phone = " - "
                try:
                    phone = card.find_all('dd')[3].text.strip()
                except:
                    try:
                        phone = card.find("li", class_="dataTel").text.strip()
                    except:
                        phone = " - "
                
                if re.match(pattern, phone):
                    items.append({
                        "会社名": name,
                        "住所": address,
                        "電話番号": phone
                    })
            
            results.extend(items)
            print(f"Found {len(items)} valid items on page {i+1}")
            
            sleep(2)  # Increased delay between requests
            
        except Exception as e:
            print(f"Error processing URL {url}: {str(e)}")
            failed_urls.append((url, str(e)))
            continue
    
    return results, failed_urls

if __name__ == "__main__":
    print("Starting robust scraper...")
    
    try:
        # Test connection first
        print("Testing connection to mapion...")
        response = robust_get(BASE_URL + ADD_URL)
        if response is None:
            print("Initial connection test failed!")
            exit(1)
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Try to get total pages
        try:
            total_pages = (int(soup.find_all("p", class_="subTitle")[0].find_all("span")[1].text.split('件')[0]) - 1 ) // 20 + 1
        except:
            print("Could not determine total pages, using default value")
            total_pages = 5  # Default to 5 pages if we can't determine the total
        
        max_pages = min(total_pages, 100)
        urls = [f"{BASE_URL}/p={page}{ADD_URL}" for page in range(1, max_pages + 1)]
        
        print(f"Will scrape {max_pages} pages")
        
        # Scrape with retry
        results, failed_urls = scrape_with_retry(urls)
        
        print(f"\nScraping completed!")
        print(f"Total items found: {len(results)}")
        print(f"Failed URLs: {len(failed_urls)}")
        
        if failed_urls:
            print("\nFailed URLs:")
            for url, error in failed_urls:
                print(f"  {url}: {error}")
        
        # Remove duplicates and save
        if results:
            df = pd.DataFrame(results)
            print(f"\nBefore deduplication: {len(df)} items")
            
            initial_dupes = df.duplicated().sum()
            print(f"Found {initial_dupes} duplicate rows")
            
            df = df.drop_duplicates().reset_index(drop=True)
            print(f"After deduplication: {len(df)} items")
            
            # Save to CSV
            output_file = f"data_sub/{GENRE}_{AREA}.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Data saved to: {output_file}")
        else:
            print("No results to save")
            
    except Exception as e:
        print(f"Script failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
