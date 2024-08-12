import streamlit as st
import time
import random
import pandas as pd
from playwright.sync_api import sync_playwright

# Initialize Playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    browser.close()

def delay():
    time.sleep(random.randint(3, 10))

def extract_product_info(page):
    try:
        page.wait_for_selector("#gridItemRoot", timeout=20000)
        
        grid_items = page.query_selector_all("#gridItemRoot")
        
        products = []
        for item in grid_items:
            product = {}
            
            # Extract ranking
            rank_element = item.query_selector(".zg-bdg-text")
            product['ranking'] = rank_element.inner_text().strip('#') if rank_element else 'N/A'
            
            # Extract product URL and name
            link_element = item.query_selector("a.a-link-normal[href*='/dp/']")
            product['url'] = link_element.get_attribute('href') if link_element else 'N/A'
            name_element = item.query_selector("div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
            product['name'] = name_element.inner_text().strip() if name_element else 'N/A'
            
            # Extract rating
            rating_element = item.query_selector("div.a-icon-row a.a-link-normal")
            product['rating'] = rating_element.get_attribute('title').split()[0] if rating_element else 'N/A'
            
            # Extract number of reviews
            reviews_element = item.query_selector("span.a-size-small")
            product['reviews'] = reviews_element.inner_text().replace(',', '') if reviews_element else '0'
            
            # Extract price
            price_element = item.query_selector("span._cDEzb_p13n-sc-price_3mJ9Z")
            product['price'] = price_element.inner_text().strip('$') if price_element else 'N/A'
            
            products.append(product)
        
        return products
    except Exception as e:
        st.error(f"Error extracting product info: {str(e)}")
        return []

def scrape_amazon(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            time.sleep(5)  # Wait for 5 seconds after page load
            products = extract_product_info(page)
            browser.close()
            return products
    except Exception as e:
        st.error(f"Error during scraping: {str(e)}")
        return None

st.title('Amazon Best Sellers Scraper')

url = st.text_input('Enter the Amazon Best Sellers URL:')

if st.button('Scrape Data'):
    if url:
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
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