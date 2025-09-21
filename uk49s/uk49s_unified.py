#!/usr/bin/env python3
"""
UK49s Lottery Analyzer - Unified Version
A comprehensive tool for scraping, analyzing, and predicting UK49s lottery results.
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import sys
import time
import logging
import json
import re
import csv
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from itertools import combinations
import os

# Selenium imports (optional - only if needed)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not available. Web scraping will use requests only.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('uk49s.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class UK49sUnified:
    def __init__(self, db_name="uk49s.db"):
        self.db_name = db_name
        self.setup_database()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

    def setup_database(self):
        """Create the database with a unified schema."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Create a unified table structure
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS draws (
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
                    source TEXT DEFAULT 'Unknown',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, draw_type)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON draws(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_draw_type ON draws(draw_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_numbers ON draws(n1, n2, n3, n4, n5, n6)")
            
            conn.commit()
            conn.close()
            logging.info("✅ Database setup complete")
        except Exception as e:
            logging.error(f"❌ Database setup failed: {e}")

    def import_csv_data(self, csv_file="lotto-draw-history.csv"):
        """Import data from CSV file."""
        if not os.path.exists(csv_file):
            logging.warning(f"CSV file {csv_file} not found")
            return 0
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            imported_count = 0
            duplicates = 0
            
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    try:
                        # Parse the date
                        date_str = row['DrawDate']
                        # Convert DD-MMM-YYYY to DD/MM/YYYY format
                        date_obj = datetime.strptime(date_str, '%d-%b-%Y')
                        formatted_date = date_obj.strftime('%d/%m/%Y')
                        
                        # Extract numbers
                        numbers = [
                            int(row['Ball 1']),
                            int(row['Ball 2']),
                            int(row['Ball 3']),
                            int(row['Ball 4']),
                            int(row['Ball 5']),
                            int(row['Ball 6'])
                        ]
                        
                        booster = int(row['Bonus Ball'])
                        
                        # Determine draw type (this CSV seems to be for a different lottery)
                        # We'll use a generic type for now
                        draw_type = "Main Draw"
                        
                        # Insert into database
                        cursor.execute("""
                            INSERT OR IGNORE INTO draws 
                            (date, draw_type, n1, n2, n3, n4, n5, n6, booster, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (formatted_date, draw_type, *numbers, booster, 'CSV Import'))
                        
                        if cursor.rowcount > 0:
                            imported_count += 1
                        else:
                            duplicates += 1
                            
                    except (ValueError, KeyError) as e:
                        logging.warning(f"Skipping invalid row: {e}")
                        continue
            
            conn.commit()
            conn.close()
            
            logging.info(f"✅ CSV Import: {imported_count} new records, {duplicates} duplicates")
            return imported_count
            
        except Exception as e:
            logging.error(f"❌ CSV import failed: {e}")
            return 0

    def get_selenium_driver(self):
        """Set up Chrome driver with webdriver-manager."""
        if not SELENIUM_AVAILABLE:
            return None
            
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
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logging.info("✅ Selenium driver initialized")
            return driver
            
        except Exception as e:
            logging.error(f"❌ Selenium setup failed: {e}")
            return None

    def scrape_uk49s_results(self):
        """Scrape UK49s results from multiple sources."""
        sources = [
            {
                'name': 'Bet49s',
                'url': 'https://www.bet49s.com/historical-results',
                'method': 'selenium' if SELENIUM_AVAILABLE else 'requests'
            },
            {
                'name': '49sResult',
                'url': 'https://www.49sresult.co.uk/',
                'method': 'requests'
            }
        ]
        
        all_results = []
        
        for source in sources:
            try:
                logging.info(f"🌐 Scraping {source['name']}...")
                
                if source['method'] == 'selenium' and SELENIUM_AVAILABLE:
                    results = self._scrape_with_selenium(source)
                else:
                    results = self._scrape_with_requests(source)
                
                if results:
                    all_results.extend(results)
                    logging.info(f"✅ Got {len(results)} results from {source['name']}")
                else:
                    logging.warning(f"⚠️ No results from {source['name']}")
                    
                time.sleep(2)  # Be polite to servers
                
            except Exception as e:
                logging.error(f"❌ Failed to scrape {source['name']}: {e}")
                continue
        
        return all_results

    def _scrape_with_selenium(self, source):
        """Scrape using Selenium."""
        driver = self.get_selenium_driver()
        if not driver:
            return []
        
        try:
            driver.get(source['url'])
            time.sleep(5)  # Wait for page to load
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            return self._parse_results(soup, source['name'])
            
        except Exception as e:
            logging.error(f"Selenium scraping error: {e}")
            return []
        finally:
            if driver:
                driver.quit()

    def _scrape_with_requests(self, source):
        """Scrape using requests."""
        try:
            response = self.session.get(source['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_results(soup, source['name'])
            
        except Exception as e:
            logging.error(f"Requests scraping error: {e}")
            return []

    def _parse_results(self, soup, source_name):
        """Parse results from BeautifulSoup object."""
        results = []
        
        # Try different selectors for tables
        selectors = [
            'table tbody tr',
            '.table-results tbody tr',
            '.results-table tbody tr',
            'table tr'
        ]
        
        rows = []
        for selector in selectors:
            rows = soup.select(selector)
            if rows:
                break
        
        if not rows:
            logging.warning(f"No table rows found for {source_name}")
            return []
        
        for row in rows:
            try:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 6:
                    continue
                
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # Skip header rows
                if any(header in ' '.join(cell_texts).lower() for header in ['date', 'draw', 'numbers', 'results']):
                    continue
                
                # Try to parse the row
                parsed = self._parse_row(cell_texts)
                if parsed:
                    results.append(parsed + (source_name,))
                    
            except Exception as e:
                logging.debug(f"Error parsing row: {e}")
                continue
        
        return results

    def _parse_row(self, cell_texts):
        """Parse a row of cell texts into draw data."""
        try:
            date = None
            draw_type = None
            numbers = []
            
            for text in cell_texts:
                # Look for date
                if not date and self._is_valid_date(text):
                    date = text
                    continue
                
                # Look for draw type
                if not draw_type:
                    cleaned_type = self._clean_draw_type(text)
                    if cleaned_type:
                        draw_type = cleaned_type
                        continue
                
                # Look for numbers
                if text.isdigit():
                    num = int(text)
                    if 1 <= num <= 49 and len(numbers) < 6:
                        numbers.append(num)
            
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
                    return (date, draw_type, *numbers, booster)
            
            return None
            
        except Exception as e:
            logging.debug(f"Error parsing row data: {e}")
            return None

    def _is_valid_date(self, date_text):
        """Check if text looks like a valid date."""
        if not date_text or len(date_text) < 6:
            return False
        
        patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'\w{3,9}\s+\d{1,2},?\s+\d{4}',
        ]
        
        return any(re.search(pattern, date_text) for pattern in patterns)

    def _clean_draw_type(self, draw_type):
        """Clean and standardize draw type."""
        if not draw_type:
            return None
            
        draw_type = draw_type.lower().strip()
        
        lunchtime_indicators = ['lunch', '12:49', '12.49', 'noon', 'midday', 'day', 'am']
        teatime_indicators = ['tea', 'evening', '17:49', '5:49', '17.49', '5.49', 'pm', '5pm', '17']
        
        if any(indicator in draw_type for indicator in lunchtime_indicators):
            return 'Lunchtime'
        elif any(indicator in draw_type for indicator in teatime_indicators):
            return 'Teatime'
        
        return None

    def save_results(self, results):
        """Save results to database."""
        if not results:
            return 0
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            saved_count = 0
            duplicates = 0
            
            for result in results:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO draws 
                        (date, draw_type, n1, n2, n3, n4, n5, n6, booster, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, result)
                    
                    if cursor.rowcount > 0:
                        saved_count += 1
                    else:
                        duplicates += 1
                        
                except Exception as e:
                    logging.warning(f"Error saving result: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            logging.info(f"📊 Saved {saved_count} new results, {duplicates} duplicates skipped")
            return saved_count
            
        except Exception as e:
            logging.error(f"❌ Database save error: {e}")
            return 0

    def get_database_stats(self):
        """Get database statistics."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM draws")
            total_draws = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT date) FROM draws")
            unique_dates = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(date), MAX(date) FROM draws")
            date_range = cursor.fetchone()
            
            cursor.execute("SELECT draw_type, COUNT(*) FROM draws GROUP BY draw_type")
            by_draw_type = cursor.fetchall()
            
            cursor.execute("SELECT date, draw_type, n1, n2, n3, n4, n5, n6, source FROM draws ORDER BY rowid DESC LIMIT 3")
            recent_entries = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_draws': total_draws,
                'unique_dates': unique_dates,
                'date_range': date_range,
                'by_draw_type': by_draw_type,
                'recent_entries': recent_entries
            }
            
        except Exception as e:
            logging.error(f"Error getting database stats: {e}")
            return None

    def most_frequent_numbers(self, limit=10, draw_type=None):
        """Find most frequent numbers."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            where_clause = "WHERE draw_type = ?" if draw_type else ""
            params = [draw_type] if draw_type else []
            
            all_numbers = []
            for col in ["n1", "n2", "n3", "n4", "n5", "n6"]:
                query = f"SELECT {col} FROM draws {where_clause}"
                cursor.execute(query, params)
                all_numbers.extend([row[0] for row in cursor.fetchall() if row[0] is not None])
            
            conn.close()
            
            if not all_numbers:
                return []
            
            counter = Counter(all_numbers)
            return counter.most_common(limit)
            
        except Exception as e:
            logging.error(f"Error getting frequent numbers: {e}")
            return []

    def most_frequent_pairs(self, limit=10, draw_type=None):
        """Find most frequent pairs."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            where_clause = "WHERE draw_type = ?" if draw_type else ""
            params = [draw_type] if draw_type else []
            
            query = f"""
                SELECT date, draw_type, n1, n2, n3, n4, n5, n6 
                FROM draws {where_clause}
                ORDER BY date
            """
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            pairs_count = Counter()
            
            for row in rows:
                numbers = [row[i] for i in range(2, 8) if row[i] is not None]
                for pair in combinations(sorted(numbers), 2):
                    pairs_count[pair] += 1
            
            return pairs_count.most_common(limit)
            
        except Exception as e:
            logging.error(f"Error getting frequent pairs: {e}")
            return []

    def hot_cold_analysis(self, recent_draws=50, draw_type=None):
        """Analyze hot and cold numbers."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            where_clause = "WHERE draw_type = ?" if draw_type else ""
            params = [draw_type] if draw_type else []
            
            query = f"""
                SELECT n1, n2, n3, n4, n5, n6 
                FROM draws {where_clause}
                ORDER BY date DESC
                LIMIT ?
            """
            params.append(recent_draws)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            recent_numbers = []
            for row in rows:
                recent_numbers.extend([num for num in row if num is not None])
            
            counter = Counter(recent_numbers)
            total_numbers = len(recent_numbers)
            
            hot_numbers = counter.most_common(10)
            cold_numbers = counter.most_common()[:-11:-1]
            
            return {
                'hot': hot_numbers,
                'cold': cold_numbers,
                'total_recent_numbers': total_numbers,
                'recent_draws_analyzed': len(rows)
            }
            
        except Exception as e:
            logging.error(f"Error in hot/cold analysis: {e}")
            return None

    def generate_sample_data(self):
        """Generate sample data for testing."""
        import random
        
        sample_results = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(20):
            date = (base_date + timedelta(days=i)).strftime('%d/%m/%Y')
            draw_type = 'Lunchtime' if i % 2 == 0 else 'Teatime'
            
            # Generate 6 unique random numbers
            numbers = random.sample(range(1, 50), 6)
            booster = numbers[5]
            
            sample_results.append((date, draw_type, *numbers, booster, 'Sample Data'))
        
        return sample_results

    def export_analysis(self, filename=None, draw_type=None):
        """Export analysis to JSON."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            draw_suffix = f"_{draw_type}" if draw_type else "_all"
            filename = f"uk49s_analysis{draw_suffix}_{timestamp}.json"
        
        analysis = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'draw_type': draw_type,
                'database_stats': self.get_database_stats()
            },
            'most_frequent_numbers': self.most_frequent_numbers(20, draw_type),
            'most_frequent_pairs': self.most_frequent_pairs(15, draw_type),
            'hot_cold_analysis': self.hot_cold_analysis(50, draw_type)
        }
        
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        logging.info(f"✅ Analysis exported to {filename}")
        return filename

def print_analysis(analyzer, draw_type=None):
    """Print formatted analysis results."""
    print(f"\n{'='*60}")
    print(f"🎰 UK49s Analysis Results")
    if draw_type:
        print(f"📊 Draw Type: {draw_type}")
    else:
        print(f"📊 Draw Type: All")
    print(f"{'='*60}")
    
    # Database stats
    stats = analyzer.get_database_stats()
    if stats:
        print(f"\n📊 Database Statistics:")
        print(f"   Total draws: {stats['total_draws']}")
        print(f"   Unique dates: {stats['unique_dates']}")
        if stats['date_range'][0]:
            print(f"   Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")
        if stats['by_draw_type']:
            for draw_type_name, count in stats['by_draw_type']:
                print(f"   {draw_type_name}: {count}")
    
    # Most frequent numbers
    numbers = analyzer.most_frequent_numbers(15, draw_type)
    if numbers:
        print(f"\n🔢 Most Frequent Numbers:")
        for i, (num, freq) in enumerate(numbers, 1):
            print(f"   {i:2d}. Number {num:2d}: {freq:4d} times")
    
    # Most frequent pairs
    pairs = analyzer.most_frequent_pairs(10, draw_type)
    if pairs:
        print(f"\n👥 Most Frequent Pairs:")
        for i, (pair, freq) in enumerate(pairs, 1):
            print(f"   {i:2d}. ({pair[0]:2d}, {pair[1]:2d}): {freq:3d} times")
    
    # Hot and cold analysis
    hot_cold = analyzer.hot_cold_analysis(50, draw_type)
    if hot_cold:
        print(f"\n🔥 Hot Numbers (Last {hot_cold['recent_draws_analyzed']} draws):")
        for i, (num, freq) in enumerate(hot_cold['hot'][:8], 1):
            percentage = (freq / hot_cold['total_recent_numbers']) * 100
            print(f"   {i:2d}. Number {num:2d}: {freq:2d} times ({percentage:.1f}%)")
        
        print(f"\n🧊 Cold Numbers (Last {hot_cold['recent_draws_analyzed']} draws):")
        for i, (num, freq) in enumerate(hot_cold['cold'][:8], 1):
            percentage = (freq / hot_cold['total_recent_numbers']) * 100
            print(f"   {i:2d}. Number {num:2d}: {freq:2d} times ({percentage:.1f}%)")

def main():
    """Main function with interactive menu."""
    print("🎰 UK49s Lottery Analyzer - Unified Version")
    print("=" * 60)
    
    analyzer = UK49sUnified()
    
    while True:
        print(f"\n{'='*50}")
        print("🎰 UK49s Lottery Analyzer")
        print("="*50)
        print("1️⃣  Import CSV Data")
        print("2️⃣  Scrape Web Results")
        print("3️⃣  Generate Sample Data")
        print("4️⃣  Analyze All Draws")
        print("5️⃣  Analyze Lunchtime Only")
        print("6️⃣  Analyze Teatime Only")
        print("7️⃣  Export Analysis")
        print("8️⃣  Database Statistics")
        print("9️⃣  Exit")
        print("-" * 50)
        
        choice = input("Choose an option: ").strip()
        
        if choice == "1":
            print("\n📁 Importing CSV data...")
            count = analyzer.import_csv_data()
            print(f"✅ Imported {count} records from CSV")
            
        elif choice == "2":
            print("\n🌐 Scraping web results...")
            results = analyzer.scrape_uk49s_results()
            if results:
                saved = analyzer.save_results(results)
                print(f"✅ Scraped and saved {saved} new results")
            else:
                print("❌ No results found")
                
        elif choice == "3":
            print("\n🧪 Generating sample data...")
            sample_data = analyzer.generate_sample_data()
            saved = analyzer.save_results(sample_data)
            print(f"✅ Generated and saved {saved} sample records")
            
        elif choice == "4":
            print_analysis(analyzer, None)
            
        elif choice == "5":
            print_analysis(analyzer, "Lunchtime")
            
        elif choice == "6":
            print_analysis(analyzer, "Teatime")
            
        elif choice == "7":
            draw_type = input("Export for which draw type? (Lunchtime/Teatime/All): ").strip()
            if draw_type.lower() == "all":
                draw_type = None
            elif draw_type not in ["Lunchtime", "Teatime"]:
                draw_type = None
            filename = analyzer.export_analysis(draw_type=draw_type)
            print(f"✅ Analysis exported to: {filename}")
            
        elif choice == "8":
            stats = analyzer.get_database_stats()
            if stats:
                print(f"\n📊 Database Statistics:")
                print(f"   Total draws: {stats['total_draws']}")
                print(f"   Unique dates: {stats['unique_dates']}")
                if stats['date_range'][0]:
                    print(f"   Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")
                if stats['by_draw_type']:
                    for draw_type_name, count in stats['by_draw_type']:
                        print(f"   {draw_type_name}: {count}")
                if stats['recent_entries']:
                    print(f"\n📋 Recent Entries:")
                    for entry in stats['recent_entries']:
                        date, draw_type, n1, n2, n3, n4, n5, n6, source = entry
                        print(f"   {date} {draw_type}: {n1}, {n2}, {n3}, {n4}, {n5}, {n6} (from {source})")
            
        elif choice == "9":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
