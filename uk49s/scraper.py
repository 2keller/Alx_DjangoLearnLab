import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import logging
import json
import re
from datetime import datetime, timedelta
import sys

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('uk49s_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

DB_NAME = "uk49s.db"

# Multiple data sources to try
DATA_SOURCES = [
    {
        'name': 'Bet49s Historical (JavaScript)',
        'url': 'https://www.bet49s.com/historical-results',
        'method': 'selenium',
        'selectors': {
            'wait_for': '.table-results, table, .results-table',
            'table': 'table tbody tr, .table-results tbody tr, .results-table tbody tr',
            'row_cells': 'td',
        }
    },
    {
        'name': '49sResult.co.uk',
        'url': 'https://www.49sresult.co.uk/',
        'method': 'requests',
        'selectors': {
            'table': 'table tbody tr, .results-table tbody tr',
            'row_cells': 'td',
        }
    },
    {
        'name': 'CompareTheLotto',
        'url': 'https://www.comparethelotto.com/49s-lotto-results',
        'method': 'requests',
        'selectors': {
            'table': '.results-table tbody tr, table tbody tr',
            'row_cells': 'td',
        }
    },
    {
        'name': 'National Lottery',
        'url': 'https://www.national-lottery.co.uk/results/49s',
        'method': 'requests',
        'selectors': {
            'table': 'table tbody tr, .results tbody tr',
            'row_cells': 'td, .result-cell',
        }
    }
]

class UK49sScraperComplete:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.setup_database()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1',
        })

    def setup_database(self):
        """Create the database table if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS numbers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    draw_type TEXT NOT NULL,
                    n1 INTEGER NOT NULL,
                    n2 INTEGER NOT NULL,
                    n3 INTEGER NOT NULL,
                    n4 INTEGER NOT NULL,
                    n5 INTEGER NOT NULL,
                    n6 INTEGER NOT NULL,
                    booster INTEGER,
                    source TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, draw_type)
                )
            """)
            conn.commit()
            conn.close()
            logging.info("✅ Database setup complete")
        except Exception as e:
            logging.error(f"❌ Database setup failed: {e}")

    def get_selenium_driver(self):
        """Set up a Chrome driver with webdriver-manager."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Use webdriver-manager to automatically download ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logging.info("✅ Selenium driver initialized successfully")
            return driver
            
        except Exception as e:
            logging.error(f"❌ Selenium setup failed: {e}")
            return None

    def scrape_with_selenium(self, source):
        """Scrape using Selenium for JavaScript-heavy sites."""
        driver = self.get_selenium_driver()
        if not driver:
            return []

        try:
            logging.info(f"🌐 Loading {source['name']} with Selenium...")
            driver.get(source['url'])
            
            # Wait for the page to load
            wait = WebDriverWait(driver, 30)
            
            # Try to wait for different elements that might contain the results
            selectors_to_try = source['selectors']['wait_for'].split(', ')
            element_found = False
            
            for selector in selectors_to_try:
                try:
                    logging.info(f"Waiting for selector: {selector}")
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    element_found = True
                    logging.info(f"✅ Found element with selector: {selector}")
                    break
                except TimeoutException:
                    logging.info(f"⏰ Timeout for selector: {selector}")
                    continue
            
            if not element_found:
                logging.warning(f"⚠️ No target elements found, trying to parse anyway...")
            
            # Additional wait for dynamic content
            time.sleep(5)
            
            # Try scrolling to load more content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get page source and parse
            page_source = driver.page_source
            logging.info(f"Page source length: {len(page_source)}")
            
            # Save page source for debugging
            with open(f'debug_{source["name"].replace(" ", "_")}.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            soup = BeautifulSoup(page_source, 'html.parser')
            results = self.parse_results(soup, source)
            
            return results
            
        except Exception as e:
            logging.error(f"❌ Selenium scraping failed for {source['name']}: {e}")
            return []
        finally:
            if driver:
                driver.quit()

    def scrape_with_requests(self, source):
        """Scrape using requests for static sites."""
        try:
            logging.info(f"🌐 Fetching {source['name']} with requests...")
            
            # Add some headers that might help
            headers = self.session.headers.copy()
            headers['Referer'] = 'https://www.google.com/'
            
            response = self.session.get(source['url'], timeout=30, headers=headers)
            response.raise_for_status()
            
            logging.info(f"Response status: {response.status_code}, Content length: {len(response.text)}")
            
            # Save page source for debugging
            with open(f'debug_{source["name"].replace(" ", "_")}.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = self.parse_results(soup, source)
            
            return results
            
        except requests.RequestException as e:
            logging.error(f"❌ Network error for {source['name']}: {e}")
            return []
        except Exception as e:
            logging.error(f"❌ Unexpected error for {source['name']}: {e}")
            return []

    def parse_results(self, soup, source):
        """Parse results from BeautifulSoup object."""
        results = []
        
        # Debug: Save the HTML for inspection
        logging.info(f"Parsing results for {source['name']}")
        
        # Try multiple selectors
        selectors = source['selectors']['table'].split(', ')
        rows = []
        
        for selector in selectors:
            rows = soup.select(selector.strip())
            if rows:
                logging.info(f"✅ Found {len(rows)} rows with selector: {selector}")
                break
        
        if not rows:
            logging.warning(f"❌ No rows found for {source['name']}")
            # Debug: show what we can find
            self.debug_page_structure(soup, source['name'])
            return []

        successful_parses = 0
        for i, row in enumerate(rows):
            try:
                cells = row.find_all(['td', 'th', 'div', 'span'])
                
                # Skip rows with too few cells
                if len(cells) < 6:
                    continue
                
                # Extract text from cells
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # Skip header rows
                header_indicators = ['date', 'draw type', 'numbers', 'results', 'ball', 'time', 'draw']
                if any(header.lower() in ' '.join(cell_texts).lower() for header in header_indicators):
                    logging.debug(f"Skipping header row: {cell_texts}")
                    continue
                
                # Skip empty rows
                if not any(cell_texts):
                    continue
                
                # Try to parse this row
                parsed_result = self.parse_row_data(cell_texts, source['name'])
                if parsed_result:
                    results.append(parsed_result)
                    successful_parses += 1
                    logging.debug(f"✅ Parsed row {i}: {parsed_result}")
                else:
                    logging.debug(f"❌ Failed to parse row {i}: {cell_texts}")
                    
            except Exception as e:
                logging.debug(f"Error parsing row {i}: {e}")
                continue
        
        logging.info(f"✅ Successfully parsed {successful_parses} results from {source['name']}")
        return results

    def debug_page_structure(self, soup, source_name):
        """Debug helper to understand page structure."""
        logging.info(f"🔍 Debugging page structure for {source_name}")
        
        # Look for tables
        tables = soup.find_all('table')
        logging.info(f"Found {len(tables)} tables")
        
        for i, table in enumerate(tables[:3]):  # Check first 3 tables
            rows = table.find_all('tr')
            logging.info(f"Table {i}: {len(rows)} rows")
            if rows:
                first_row_cells = rows[0].find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True) for cell in first_row_cells]
                logging.info(f"First row: {cell_texts}")
        
        # Look for divs that might contain results
        result_divs = soup.find_all('div', class_=re.compile(r'result|draw|lottery', re.I))
        logging.info(f"Found {len(result_divs)} potential result divs")
        
        # Look for any text that contains numbers that look like lottery results
        text_content = soup.get_text()
        number_patterns = re.findall(r'\b\d{1,2}[\s,]+\d{1,2}[\s,]+\d{1,2}[\s,]+\d{1,2}[\s,]+\d{1,2}[\s,]+\d{1,2}\b', text_content)
        logging.info(f"Found {len(number_patterns)} potential number sequences")
        if number_patterns:
            logging.info(f"Sample patterns: {number_patterns[:3]}")

    def parse_row_data(self, cell_texts, source_name):
        """Parse a row of cell texts into date, draw_type, numbers."""
        try:
            date = None
            draw_type = None
            numbers = []
            
            # Strategy 1: Sequential parsing (assuming standard order)
            for i, text in enumerate(cell_texts):
                # Look for date in first few cells
                if i < 3 and self.is_valid_date(text) and not date:
                    date = text
                    continue
                
                # Look for draw type
                if not draw_type:
                    cleaned_type = self.clean_draw_type(text)
                    if cleaned_type:
                        draw_type = cleaned_type
                        continue
                
                # Look for individual numbers
                if text.isdigit():
                    num = int(text)
                    if 1 <= num <= 49 and len(numbers) < 6:
                        numbers.append(num)
                
                # Look for comma-separated numbers in a single cell
                if ',' in text and not numbers:
                    potential_numbers = re.findall(r'\b\d{1,2}\b', text)
                    if len(potential_numbers) >= 6:
                        parsed_nums = []
                        for n in potential_numbers[:6]:
                            num = int(n)
                            if 1 <= num <= 49:
                                parsed_nums.append(num)
                        if len(parsed_nums) == 6:
                            numbers = parsed_nums
            
            # Strategy 2: If sequential didn't work, try pattern matching
            if not numbers:
                all_text = ' '.join(cell_texts)
                number_matches = re.findall(r'\b(\d{1,2})\b', all_text)
                potential_numbers = [int(n) for n in number_matches if 1 <= int(n) <= 49]
                if len(potential_numbers) >= 6:
                    numbers = potential_numbers[:6]
            
            # Validate we have all required data
            if date and draw_type and len(numbers) == 6:
                # Remove duplicates while preserving order
                seen = set()
                unique_numbers = []
                for num in numbers:
                    if num not in seen:
                        unique_numbers.append(num)
                        seen.add(num)
                
                if len(unique_numbers) >= 6:
                    numbers = unique_numbers[:6]
                    booster = numbers[5]  # Use 6th number as booster
                    return (date, draw_type, *numbers, booster, source_name)
            
            return None
            
        except Exception as e:
            logging.debug(f"Error parsing row data: {e}")
            return None

    def is_valid_date(self, date_text):
        """Check if text looks like a valid date."""
        if not date_text or len(date_text) < 6:
            return False
        
        # Common date patterns
        patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # DD/MM/YYYY or MM/DD/YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',    # YYYY/MM/DD
            r'\w{3,9}\s+\d{1,2},?\s+\d{4}',    # Month DD, YYYY
            r'\d{1,2}\s+\w{3,9}\s+\d{4}',     # DD Month YYYY
            r'\d{2}/\d{2}/\d{2}',              # DD/MM/YY
        ]
        
        return any(re.search(pattern, date_text) for pattern in patterns)

    def clean_draw_type(self, draw_type):
        """Clean and standardize draw type."""
        if not draw_type:
            return None
            
        draw_type = draw_type.lower().strip()
        
        # More comprehensive matching
        lunchtime_indicators = ['lunch', '12:49', '12.49', 'noon', 'midday', 'day', 'am']
        teatime_indicators = ['tea', 'evening', '17:49', '5:49', '17.49', '5.49', 'pm', '5pm', '17']
        
        if any(indicator in draw_type for indicator in lunchtime_indicators):
            return 'Lunchtime'
        elif any(indicator in draw_type for indicator in teatime_indicators):
            return 'Teatime'
        
        return None

    def scrape_all_sources(self):
        """Try scraping from all available sources."""
        all_results = []
        
        for source in DATA_SOURCES:
            try:
                logging.info(f"🎯 Trying {source['name']}...")
                
                if source['method'] == 'selenium':
                    results = self.scrape_with_selenium(source)
                else:
                    results = self.scrape_with_requests(source)
                
                if results:
                    all_results.extend(results)
                    logging.info(f"✅ Got {len(results)} results from {source['name']}")
                    
                    # Show a sample of what we got
                    if results:
                        sample = results[0]
                        logging.info(f"Sample result: {sample}")
                    
                    # If we got good results from one source, continue to try others for comparison
                else:
                    logging.warning(f"⚠️ No results from {source['name']}")
                
                # Small delay between sources
                time.sleep(3)
                
            except Exception as e:
                logging.error(f"❌ Failed to scrape {source['name']}: {e}")
                continue
        
        # Remove duplicates
        unique_results = []
        seen = set()
        for result in all_results:
            key = (result[0], result[1])  # date, draw_type
            if key not in seen:
                unique_results.append(result)
                seen.add(key)
        
        logging.info(f"📊 Total unique results: {len(unique_results)} (removed {len(all_results) - len(unique_results)} duplicates)")
        return unique_results

    def manual_data_entry(self):
        """Allow manual entry of recent results."""
        print("\n🔧 Manual Data Entry Mode")
        print("=" * 50)
        print("Enter recent UK49s results manually:")
        print("Format: date,draw_type,n1,n2,n3,n4,n5,n6")
        print("Example: 10/09/2024,Lunchtime,5,12,23,31,42,47")
        print("Type 'done' to finish, 'quit' to exit")
        
        results = []
        while True:
            entry = input("\nEnter result: ").strip()
            
            if entry.lower() == 'done':
                break
            elif entry.lower() in ['quit', 'exit']:
                return []
            
            try:
                parts = [p.strip() for p in entry.split(',')]
                if len(parts) >= 8:
                    date = parts[0]
                    draw_type = parts[1]
                    numbers = [int(parts[i]) for i in range(2, 8)]
                    
                    # Validate
                    if all(1 <= num <= 49 for num in numbers):
                        if draw_type.lower() in ['lunchtime', 'teatime']:
                            draw_type = draw_type.capitalize()
                            # Check for duplicates
                            if len(set(numbers)) == len(numbers):
                                result = (date, draw_type, *numbers, numbers[5], 'Manual Entry')
                                results.append(result)
                                print(f"✅ Added: {date} {draw_type} - {numbers}")
                            else:
                                print("❌ Numbers must be unique")
                        else:
                            print("❌ Draw type must be 'Lunchtime' or 'Teatime'")
                    else:
                        print("❌ Numbers must be between 1 and 49")
                else:
                    print("❌ Invalid format. Use: date,draw_type,n1,n2,n3,n4,n5,n6")
                    
            except ValueError:
                print("❌ Invalid format. Numbers must be integers.")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return results

    def get_sample_data(self):
        """Generate some sample data for testing."""
        print("\n🧪 Generating sample data for testing...")
        
        sample_results = [
            ('10/09/2024', 'Lunchtime', 5, 12, 23, 31, 42, 47, 47, 'Sample Data'),
            ('10/09/2024', 'Teatime', 8, 15, 28, 35, 41, 46, 46, 'Sample Data'),
            ('09/09/2024', 'Lunchtime', 3, 17, 22, 29, 38, 44, 44, 'Sample Data'),
            ('09/09/2024', 'Teatime', 7, 14, 25, 33, 40, 48, 48, 'Sample Data'),
            ('08/09/2024', 'Lunchtime', 2, 19, 26, 34, 39, 45, 45, 'Sample Data'),
            ('08/09/2024', 'Teatime', 9, 16, 24, 32, 43, 49, 49, 'Sample Data'),
            ('07/09/2024', 'Lunchtime', 4, 11, 21, 30, 37, 41, 41, 'Sample Data'),
            ('07/09/2024', 'Teatime', 6, 18, 27, 36, 44, 47, 47, 'Sample Data'),
            ('06/09/2024', 'Lunchtime', 1, 13, 20, 28, 35, 42, 42, 'Sample Data'),
            ('06/09/2024', 'Teatime', 10, 17, 23, 31, 38, 45, 45, 'Sample Data'),
        ]
        
        return sample_results

    def save_results(self, results):
        """Save results to database."""
        if not results:
            logging.warning("No results to save")
            return 0

        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Get existing to avoid duplicates
            cursor.execute("SELECT date, draw_type FROM numbers")
            existing = set((row[0], row[1]) for row in cursor.fetchall())
            
            new_results = []
            duplicates = 0
            
            for result in results:
                date, draw_type = result[0], result[1]
                if (date, draw_type) not in existing:
                    new_results.append(result)
                else:
                    duplicates += 1
            
            if new_results:
                cursor.executemany("""
                    INSERT OR IGNORE INTO numbers 
                    (date, draw_type, n1, n2, n3, n4, n5, n6, booster, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, new_results)
                
                conn.commit()
                saved_count = len(new_results)
            else:
                saved_count = 0
            
            conn.close()
            
            logging.info(f"📊 Results Summary:")
            logging.info(f"   - Total fetched: {len(results)}")
            logging.info(f"   - New saved: {saved_count}")
            logging.info(f"   - Duplicates skipped: {duplicates}")
            
            return saved_count
            
        except Exception as e:
            logging.error(f"❌ Database save error: {e}")
            return 0

    def check_database_status(self):
        """Check current database status."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM numbers")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT draw_type, COUNT(*) 
                FROM numbers 
                GROUP BY draw_type 
                ORDER BY draw_type
            """)
            by_draw_type = cursor.fetchall()
            
            cursor.execute("SELECT MIN(date), MAX(date) FROM numbers")
            date_range = cursor.fetchone()
            
            cursor.execute("""
                SELECT date, draw_type, n1, n2, n3, n4, n5, n6, source
                FROM numbers 
                ORDER BY rowid DESC 
                LIMIT 3
            """)
            recent_entries = cursor.fetchall()
            
            conn.close()
            
            print(f"\n📊 Current Database Status:")
            print(f"   Total records: {total_count}")
            if by_draw_type:
                for draw_type, count in by_draw_type:
                    print(f"   {draw_type}: {count}")
            if date_range[0]:
                print(f"   Date range: {date_range[0]} to {date_range[1]}")
            
            if recent_entries:
                print(f"\n📋 Recent Entries:")
                for entry in recent_entries:
                    date, draw_type, n1, n2, n3, n4, n5, n6, source = entry
                    print(f"   {date} {draw_type}: {n1}, {n2}, {n3}, {n4}, {n5}, {n6} (from {source})")
                    
        except Exception as e:
            logging.error(f"Error checking database: {e}")

def main():
    """Main function."""
    print("🎰 UK49s Complete Scraper with Selenium")
    print("=" * 60)
    
    scraper = UK49sScraperComplete()
    
    # Check current database status
    scraper.check_database_status()
    
    print("\nOptions:")
    print("1️⃣ Auto-scrape from all sources (with Selenium)")
    print("2️⃣ Manual data entry")
    print("3️⃣ Generate sample data (for testing)")
    print("4️⃣ Auto-scrape + manual fallback")
    print("5️⃣ Check database status only")
    
    choice = input("\nChoose option (1-5): ").strip()
    
    if choice == '5':
        return
    
    all_results = []
    
    if choice in ['1', '4']:
        print(f"\n🌐 Starting auto-scrape from {len(DATA_SOURCES)} sources...")
        print("This may take a few minutes...")
        all_results = scraper.scrape_all_sources()
        
        if not all_results and choice == '4':
            print("\n⚠️ Auto-scrape found no results. Switching to manual entry...")
            manual_results = scraper.manual_data_entry()
            all_results.extend(manual_results)
    
    elif choice == '2':
        all_results = scraper.manual_data_entry()
    
    elif choice == '3':
        all_results = scraper.get_sample_data()
        print("✅ Generated sample data for testing")
    
    if all_results:
        saved_count = scraper.save_results(all_results)
        print(f"\n✅ Successfully saved {saved_count} new results!")
        
        # Show updated status
        scraper.check_database_status()
        
    else:
        print("\n❌ No results obtained.")
        print("\n💡 Next steps:")
        print("   1. Try option 3 to generate sample data for testing")
        print("   2. Try option 2 for manual data entry")
        print("   3. Check the debug HTML files created in your directory")
        print("   4. Check the log file 'uk49s_scraper.log' for details")

if __name__ == "__main__":
    main()