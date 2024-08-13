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
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
        )
        
        products = []
        items = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
        
        for item in items:
            product = {}
            
            # Extract ranking
            try:
                rank_element = item.find_element(By.CSS_SELECTOR, "span.zg-bdg-text")
                product['ranking'] = rank_element.text.strip('#')
            except:
                product['ranking'] = 'N/A'
            
            # Extract product URL and name
            try:
                link_element = item.find_element(By.CSS_SELECTOR, "a.a-link-normal[href*='/dp/']")
                product['url'] = link_element.get_attribute('href')
                name_element = item.find_element(By.CSS_SELECTOR, "span.a-size-medium")
                product['name'] = name_element.text.strip()
            except:
                product['url'] = 'N/A'
                product['name'] = 'N/A'
            
            # Extract rating
            try:
                rating_element = item.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
                product['rating'] = rating_element.get_attribute('innerHTML').split()[0]
            except:
                product['rating'] = 'N/A'
            
            # Extract number of reviews
            try:
                reviews_element = item.find_element(By.CSS_SELECTOR, "span.a-size-small[aria-label]")
                product['reviews'] = reviews_element.text.replace(',', '')
            except:
                product['reviews'] = '0'
            
            # Extract price
            try:
                price_element = item.find_element(By.CSS_SELECTOR, "span.a-price-whole")
                product['price'] = price_element.text.replace(',', '')
            except:
                product['price'] = 'N/A'
            
            products.append(product)
        
        return products
    except Exception as e:
        st.error(f"Error extracting product info: {str(e)}")
        return []

def scrape_category(driver, url):
    all_products = []
    while url:
        driver.get(url)
        delay()
        products = extract_product_info(driver)
        all_products.extend(products)
        
        # Check for next page
        try:
            next_page = driver.find_element(By.CSS_SELECTOR, "li.a-last a")
            url = next_page.get_attribute('href')
        except:
            url = None
    
    return all_products

def scrape_summary_page(driver, url):
    driver.get(url)
    delay()
    
    summary_data = []
    
    # Wait for the page to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h2.a-carousel-heading"))
    )
    
    # Find all department headers
    department_headers = driver.find_elements(By.CSS_SELECTOR, "h2.a-carousel-heading")
    
    # Find all product cards
    product_cards = driver.find_elements(By.CSS_SELECTOR, "li.a-carousel-card")
    
    current_department = ""
    for card in product_cards:
        try:
            # Check if we've moved to a new department
            header = card.find_element(By.XPATH, "./preceding::h2[@class='a-carousel-heading'][1]")
            if header.text != current_department:
                current_department = header.text.strip()
            
            # Extract rank
            rank = card.find_element(By.CSS_SELECTOR, "span.zg-bdg-text").text.strip("#")
            
            # Extract product name
            name = card.find_element(By.CSS_SELECTOR, "div[class*='p13n-sc-truncate-desktop-type2']").text.strip()
            
            # Extract rating
            try:
                rating_element = card.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
                rating = rating_element.get_attribute("innerHTML")
            except:
                rating = "N/A"
            
            # Extract review count
            try:
                reviews = card.find_element(By.CSS_SELECTOR, "span.a-size-small[aria-label]").text.replace(',', '')
            except:
                reviews = "N/A"
            
            # Extract price
            try:
                price = card.find_element(By.CSS_SELECTOR, "span[class*='p13n-sc-price']").text.strip()
            except:
                price = "N/A"
            
            summary_data.append({
                'Department': current_department,
                'Rank': rank,
                'Product Name': name,
                'Rating': rating,
                'Reviews': reviews,
                'Price': price
            })
        except Exception as e:
            st.warning(f"Error extracting product info: {str(e)}")
    
    return summary_data


def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        st.success("ChromeDriver initialized successfully")
        return driver
    except Exception as e:
        st.error(f"Error initializing ChromeDriver: {str(e)}")
        return None

st.title('Amazon Best Sellers Scraper')

summary_url = "https://www.amazon.com/Best-Sellers/zgbs/ref=zg_bs_unv_pc_0_1"
custom_url = st.text_input('Enter a specific Amazon Best Sellers category URL (optional):')

if st.button('Scrape Data'):
    driver = initialize_driver()
    if driver:
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Scrape summary page
            status_text.text("Scraping summary page...")
            summary_data = scrape_summary_page(driver, summary_url)
            summary_df = pd.DataFrame(summary_data)
            st.success('Summary page scraping completed successfully!')
            st.write(summary_df)
            
            csv = summary_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download summary data as CSV",
                data=csv,
                file_name="amazon_best_sellers_summary.csv",
                mime="text/csv",
            )
            
            # Scrape custom category if URL is provided
            if custom_url:
                status_text.text("Scraping custom category...")
                category_products = scrape_category(driver, custom_url)
                if category_products:
                    category_df = pd.DataFrame(category_products)
                    st.success('Custom category scraping completed successfully!')
                    st.write(category_df)
                    
                    csv = category_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download custom category data as CSV",
                        data=csv,
                        file_name="amazon_best_sellers_custom_category.csv",
                        mime="text/csv",
                    )
                else:
                    st.error('Custom category scraping failed. Please check the URL and try again.')
            
            driver.quit()
        except Exception as e:
            st.error(f'An error occurred: {str(e)}')
            driver.quit()
    else:
        st.error('Failed to initialize ChromeDriver. Please check your setup.')

st.markdown("""
### Instructions:
1. The scraper will automatically fetch data from the Amazon Best Sellers summary page.
2. If you want to scrape a specific category, enter its URL in the text box above.
3. Click 'Scrape Data' to start the scraping process.
4. Wait for the scraping to complete (you'll see progress updates).
5. Once completed, you can view the data and download it as a CSV file.

Note: Web scraping may violate Amazon's terms of service. Use this script responsibly and in compliance with Amazon's policies.
""")