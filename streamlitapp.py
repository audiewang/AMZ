import streamlit as st
import time
import random
import pandas as pd
import requests
from bs4 import BeautifulSoup

def scrape_amazon(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        products = extract_product_info(soup)
        return products
    except Exception as e:
        st.error(f"Error during scraping: {str(e)}")
        return None

def extract_product_info(soup):
    products = []
    grid_items = soup.find_all('div', {'id': 'gridItemRoot'})
    
    for item in grid_items:
        product = {}
        
        # Extract ranking
        rank_element = item.find('span', class_='zg-bdg-text')
        product['ranking'] = rank_element.text.strip('#') if rank_element else 'N/A'
        
        # Extract product URL and name
        link_element = item.find('a', class_='a-link-normal', href=lambda x: x and '/dp/' in x)
        if link_element:
            product['url'] = 'https://www.amazon.com' + link_element['href']
            name_element = link_element.find('div', class_='_cDEzb_p13n-sc-css-line-clamp-3_g3dy1')
            product['name'] = name_element.text.strip() if name_element else 'N/A'
        else:
            product['url'] = 'N/A'
            product['name'] = 'N/A'
        
        # Extract rating
        rating_element = item.find('a', class_='a-link-normal', title=lambda x: x and 'out of 5 stars' in x)
        product['rating'] = rating_element['title'].split()[0] if rating_element else 'N/A'
        
        # Extract number of reviews
        reviews_element = item.find('span', class_='a-size-small')
        product['reviews'] = reviews_element.text.replace(',', '') if reviews_element else '0'
        
        # Extract price
        price_element = item.find('span', class_='_cDEzb_p13n-sc-price_3mJ9Z')
        product['price'] = price_element.text.strip('$') if price_element else 'N/A'
        
        products.append(product)
    
    return products

st.title('Amazon Best Sellers Scraper')

url = st.text_input('Enter the Amazon Best Sellers URL:')

if st.button('Scrape Data'):
    if url:
        try:
            products = scrape_amazon(url)
            
            if products:
                df = pd.DataFrame(products)
                st.success('Scraping completed successfully!')
                st.write(df)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name="amazon_best_sellers.csv",
                    mime="text/csv",
                )
            else:
                st.error('Scraping failed. Please check the logs for more information.')
        except Exception as e:
            st.error(f'An error occurred: {str(e)}')
    else:
        st.warning('Please enter a valid URL')

st.markdown("""
### Instructions:
1. Enter the URL of an Amazon Best Sellers page (e.g., https://www.amazon.com/Best-Sellers-Computers-Accessories/zgbs/pc/)
2. Click 'Scrape Data' to start the scraping process
3. Wait for the scraping to complete
4. Once completed, you can view the data and download it as a CSV file
""")