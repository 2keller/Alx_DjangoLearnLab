import sqlite3
import requests
from bs4 import BeautifulSoup
import sys
import time
from datetime import datetime
from collections import Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_NAME = "uk49s.db"
BASE_URL = "https://www.bet49s.com/historical-results"

class UK49sAnalyzer:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.create_tables()

    def create_tables(self):
        """Create the database and numbers table if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS numbers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    draw_type TEXT,
                    n1 INTEGER,
                    n2 INTEGER,
                    n3 INTEGER,
                    n4 INTEGER,
                    n5 INTEGER,
                    n6 INTEGER,
                    booster INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, draw_type)
                )
            """)
            conn.commit()
            conn.close()
            logging.info("✅ Database and table are ready.")
        except Exception as e:
            logging.error(f"❌ Error creating tables: {e}")

    def check_existing_data(self):
        """Check how many records already exist in the database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM numbers")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def scrape_results(self):
        """Scrape historical results from Bet49s and save to database."""
        existing_count = self.check_existing_data()
        logging.info(f"🌐 Current database has {existing_count} records")
        logging.info("🌐 Fetching UK 49s results from Bet49s...")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(BASE_URL, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"❌ Error fetching data: {e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table.tablepress tbody tr")
        if not rows:
            logging.warning("❌ No results found on the page.")
            return

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        count = 0
        duplicates = 0

        for row in rows:
            columns = row.find_all("td")
            if len(columns) < 8:
                continue
            
            try:
                date = columns[0].text.strip()
                draw_type = columns[1].text.strip()
                
                # Extract numbers more carefully
                numbers = []
                for i in range(2, 8):  # columns 2-7 should contain the 6 numbers
                    num_text = columns[i].text.strip()
                    if num_text.isdigit():
                        numbers.append(int(num_text))
                    else:
                        logging.warning(f"Invalid number format: {num_text}")
                        break
                
                if len(numbers) != 6:
                    continue
                
                # The booster is usually the 6th number, not column 7
                booster = numbers[5] if len(numbers) == 6 else 0
                main_numbers = numbers[:5] if len(numbers) == 6 else numbers

                # Use INSERT OR IGNORE to handle duplicates
                cursor.execute("""
                    INSERT OR IGNORE INTO numbers 
                    (date, draw_type, n1, n2, n3, n4, n5, n6, booster)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (date, draw_type, *numbers, booster))
                
                if cursor.rowcount > 0:
                    count += 1
                else:
                    duplicates += 1
                    
                time.sleep(0.1)  # Be polite to the server
                
            except Exception as e:
                logging.warning(f"Error processing row: {e}")
                continue

        conn.commit()
        conn.close()
        
        logging.info(f"✅ Processed {count} new draws, {duplicates} duplicates skipped")
        return count

    def most_frequent_numbers(self, limit=10, draw_type=None):
        """Calculate most frequent numbers across all draws or specific draw type."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        where_clause = ""
        params = []
        if draw_type:
            where_clause = "WHERE draw_type = ?"
            params.append(draw_type)
        
        all_numbers = []
        for col in ["n1", "n2", "n3", "n4", "n5", "n6"]:
            query = f"SELECT {col} FROM numbers {where_clause}"
            cursor.execute(query, params)
            all_numbers.extend([row[0] for row in cursor.fetchall() if row[0] is not None])
        
        conn.close()
        
        if not all_numbers:
            return []
        
        counter = Counter(all_numbers)
        return counter.most_common(limit)

    def least_frequent_numbers(self, limit=10):
        """Calculate least frequent numbers."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        all_numbers = []
        for col in ["n1", "n2", "n3", "n4", "n5", "n6"]:
            cursor.execute(f"SELECT {col} FROM numbers")
            all_numbers.extend([row[0] for row in cursor.fetchall() if row[0] is not None])
        
        conn.close()
        
        if not all_numbers:
            return []
        
        counter = Counter(all_numbers)
        return counter.most_common()[-limit:]

    def get_draw_types(self):
        """Get all available draw types."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT draw_type FROM numbers ORDER BY draw_type")
        draw_types = [row[0] for row in cursor.fetchall()]
        conn.close()
        return draw_types

    def display_statistics(self):
        """Display comprehensive statistics."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Basic stats
        cursor.execute("SELECT COUNT(*) FROM numbers")
        total_draws = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT date) FROM numbers")
        unique_dates = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(date), MAX(date) FROM numbers")
        date_range = cursor.fetchone()
        
        draw_types = self.get_draw_types()
        
        conn.close()
        
        print(f"\n📊 Database Statistics:")
        print(f"   Total draws: {total_draws}")
        print(f"   Unique dates: {unique_dates}")
        print(f"   Date range: {date_range[0]} to {date_range[1]}")
        print(f"   Draw types: {', '.join(draw_types)}")

    def analyze_results(self):
        """Enhanced analysis with multiple options."""
        if self.check_existing_data() == 0:
            print("❌ No data available. Please scrape results first.")
            return
        
        while True:
            print("\n📈 Analysis Options:")
            print("1️⃣  Most Frequent Numbers")
            print("2️⃣  Least Frequent Numbers")
            print("3️⃣  Statistics by Draw Type")
            print("4️⃣  Database Statistics")
            print("5️⃣  Back to Main Menu")
            
            choice = input("Choose analysis option: ").strip()
            
            if choice == "1":
                self._display_frequent_numbers()
            elif choice == "2":
                self._display_least_frequent_numbers()
            elif choice == "3":
                self._display_by_draw_type()
            elif choice == "4":
                self.display_statistics()
            elif choice == "5":
                break
            else:
                print("❌ Invalid choice. Try again.")

    def _display_frequent_numbers(self):
        limit = input("How many top numbers to display? (default 10): ").strip()
        limit = int(limit) if limit.isdigit() else 10
        top = self.most_frequent_numbers(limit)
        
        if not top:
            print("❌ No data available.")
            return
            
        print(f"\n🔹 Top {limit} Most Frequent Numbers:")
        for i, (num, count) in enumerate(top, 1):
            print(f"   {i:2d}. Number {num:2d}: {count:4d} times")

    def _display_least_frequent_numbers(self):
        limit = input("How many least frequent numbers to display? (default 10): ").strip()
        limit = int(limit) if limit.isdigit() else 10
        bottom = self.least_frequent_numbers(limit)
        
        if not bottom:
            print("❌ No data available.")
            return
            
        print(f"\n🔸 {limit} Least Frequent Numbers:")
        for i, (num, count) in enumerate(reversed(bottom), 1):
            print(f"   {i:2d}. Number {num:2d}: {count:4d} times")

    def _display_by_draw_type(self):
        draw_types = self.get_draw_types()
        if not draw_types:
            print("❌ No draw types available.")
            return
        
        print("\nAvailable draw types:")
        for i, draw_type in enumerate(draw_types, 1):
            print(f"   {i}. {draw_type}")
        
        try:
            choice = int(input("Select draw type (number): ")) - 1
            if 0 <= choice < len(draw_types):
                selected_type = draw_types[choice]
                top = self.most_frequent_numbers(10, selected_type)
                print(f"\n🔹 Most Frequent Numbers for {selected_type}:")
                for i, (num, count) in enumerate(top, 1):
                    print(f"   {i:2d}. Number {num:2d}: {count:4d} times")
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")

def main():
    analyzer = UK49sAnalyzer()
    
    while True:
        print("\n" + "="*50)
        print("🎰 UK 49s Lottery Analyzer")
        print("="*50)
        print("1️⃣  Update Database (Scrape New Results)")
        print("2️⃣  Analyze Results")
        print("3️⃣  Database Statistics")
        print("4️⃣  Exit")
        print("-" * 50)
        
        choice = input("Choose an option: ").strip()

        if choice == "1":
            analyzer.scrape_results()
        elif choice == "2":
            analyzer.analyze_results()
        elif choice == "3":
            analyzer.display_statistics()
        elif choice == "4":
            print("👋 Exiting. Goodbye!")
            sys.exit()
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    main()