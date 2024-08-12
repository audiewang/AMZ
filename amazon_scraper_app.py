import streamlit as st
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def delay():
    time.sleep(random.randint(3, 10))

def extract_product_info(driver):
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "gridItemRoot"))
        )
        
        grid_items = driver.find_elements(By.ID, "gridItemRoot")
        
        products = []
        for item in grid_items:
            product = {}
            
            # Extract ranking
            rank_element = item.find_element(By.CLASS_NAME, "zg-bdg-text")
            product['ranking'] = rank_element.text.strip('#')
            
            # Extract product URL and name
            link_element = item.find_element(By.CSS_SELECTOR, "a.a-link-normal[href*='/dp/']")
            product['url'] = link_element.get_attribute('href')
            name_element = item.find_element(By.CSS_SELECTOR, "div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
            product['name'] = name_element.text.strip()
            
            # Extract rating
            try:
                rating_element = item.find_element(By.CSS_SELECTOR, "div.a-icon-row a.a-link-normal")
                rating = rating_element.get_attribute('title')
                product['rating'] = rating.split()[0] if rating else 'N/A'
            except:
                product['rating'] = 'N/A'
            
            # Extract number of reviews
            try:
                reviews_element = item.find_element(By.CSS_SELECTOR, "span.a-size-small")
                product['reviews'] = reviews_element.text.replace(',', '')
            except:
                product['reviews'] = '0'
            
            # Extract price
            try:
                price_element = item.find_element(By.CSS_SELECTOR, "span._cDEzb_p13n-sc-price_3mJ9Z")
                product['price'] = price_element.text.strip('$')
            except:
                product['price'] = 'N/A'
            
            products.append(product)
        
        return products
    except Exception as e:
        st.error(f"Error extracting product info: {str(e)}")
        return []

def scrape_amazon(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        st.success("ChromeDriver initialized successfully")
    except Exception as e:
        st.error(f"Error initializing ChromeDriver: {str(e)}")
        return None

    try:
        driver.get(url)
        time.sleep(5)  # Wait for 5 seconds after page load
        products = extract_product_info(driver)
        
        driver.quit()
        return products
    except Exception as e:
        st.error(f"Error during scraping: {str(e)}")
        driver.quit()
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
3. Wait for the scraping to complete (you'll see a progress bar)
4. Once completed, you can view the data and download it as a CSV file
""")