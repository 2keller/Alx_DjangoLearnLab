import sqlite3
from collections import Counter, defaultdict
from itertools import combinations
import json
from datetime import datetime, timedelta

DB_NAME = "uk49s.db"

class UK49sAnalyzer:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.schema_type = self._detect_schema()
    
    def _detect_schema(self):
        """Detect which database schema is being used."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Check if we have the normalized schema (draws + numbers tables)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('draws', 'numbers')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        if 'draws' in tables and 'numbers' in tables:
            return 'normalized'
        else:
            return 'denormalized'  # Single table with n1, n2, n3, etc.
    
    def get_all_numbers_data(self, draw_type=None):
        """Get all numbers from draws regardless of schema type."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if self.schema_type == 'normalized':
            if draw_type:
                cursor.execute("""
                    SELECT d.date, d.draw_type, n.number, d.id as draw_id
                    FROM draws d
                    JOIN numbers n ON d.id = n.draw_id
                    WHERE d.draw_type = ?
                    ORDER BY d.date, d.draw_type, n.position
                """, (draw_type,))
            else:
                cursor.execute("""
                    SELECT d.date, d.draw_type, n.number, d.id as draw_id
                    FROM draws d
                    JOIN numbers n ON d.id = n.draw_id
                    ORDER BY d.date, d.draw_type, n.position
                """)
        else:
            # Denormalized schema
            if draw_type:
                cursor.execute("""
                    SELECT date, draw_type, n1, n2, n3, n4, n5, n6, id
                    FROM numbers
                    WHERE draw_type = ?
                    ORDER BY date
                """, (draw_type,))
            else:
                cursor.execute("""
                    SELECT date, draw_type, n1, n2, n3, n4, n5, n6, id
                    FROM numbers
                    ORDER BY date
                """)
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def most_frequent_numbers(self, limit=10, draw_type=None):
        """Find most frequent individual numbers."""
        if self.schema_type == 'normalized':
            return self._most_frequent_numbers_normalized(limit, draw_type)
        else:
            return self._most_frequent_numbers_denormalized(limit, draw_type)
    
    def _most_frequent_numbers_normalized(self, limit, draw_type):
        """For normalized schema."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if draw_type:
            cursor.execute("""
            SELECT n.number, COUNT(*) AS frequency
            FROM numbers n
            JOIN draws d ON n.draw_id = d.id
            WHERE d.draw_type = ?
            GROUP BY n.number
            ORDER BY frequency DESC, n.number ASC
            LIMIT ?
            """, (draw_type, limit))
        else:
            cursor.execute("""
            SELECT number, COUNT(*) AS frequency
            FROM numbers
            GROUP BY number
            ORDER BY frequency DESC, number ASC
            LIMIT ?
            """, (limit,))

        results = cursor.fetchall()
        conn.close()
        return results
    
    def _most_frequent_numbers_denormalized(self, limit, draw_type):
        """For denormalized schema (single table)."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        where_clause = "WHERE draw_type = ?" if draw_type else ""
        params = [draw_type] if draw_type else []
        
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
    
    def most_frequent_pairs(self, limit=10, draw_type=None):
        """Find most frequent pairs of numbers."""
        if self.schema_type == 'normalized':
            return self._most_frequent_pairs_normalized(limit, draw_type)
        else:
            return self._most_frequent_pairs_denormalized(limit, draw_type)
    
    def _most_frequent_pairs_normalized(self, limit, draw_type):
        """For normalized schema."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if draw_type:
            cursor.execute("""
            SELECT n1.number, n2.number, COUNT(*) AS pair_count
            FROM numbers n1
            JOIN numbers n2 
              ON n1.draw_id = n2.draw_id AND n1.number < n2.number
            JOIN draws d ON n1.draw_id = d.id
            WHERE d.draw_type = ?
            GROUP BY n1.number, n2.number
            ORDER BY pair_count DESC, n1.number ASC, n2.number ASC
            LIMIT ?
            """, (draw_type, limit))
        else:
            cursor.execute("""
            SELECT n1.number, n2.number, COUNT(*) AS pair_count
            FROM numbers n1
            JOIN numbers n2 
              ON n1.draw_id = n2.draw_id AND n1.number < n2.number
            GROUP BY n1.number, n2.number
            ORDER BY pair_count DESC, n1.number ASC, n2.number ASC
            LIMIT ?
            """, (limit,))

        results = cursor.fetchall()
        conn.close()
        return results
    
    def _most_frequent_pairs_denormalized(self, limit, draw_type):
        """For denormalized schema."""
        data = self.get_all_numbers_data(draw_type)
        pairs_count = Counter()
        
        for row in data:
            if self.schema_type == 'denormalized':
                # row format: (date, draw_type, n1, n2, n3, n4, n5, n6, id)
                numbers = [row[i] for i in range(2, 8) if row[i] is not None]
                for pair in combinations(sorted(numbers), 2):
                    pairs_count[pair] += 1
        
        return pairs_count.most_common(limit)
    
    def most_frequent_triplets(self, limit=10, draw_type=None):
        """Find most frequent triplets of numbers."""
        if self.schema_type == 'normalized':
            return self._most_frequent_triplets_normalized(limit, draw_type)
        else:
            return self._most_frequent_triplets_denormalized(limit, draw_type)
    
    def _most_frequent_triplets_normalized(self, limit, draw_type):
        """For normalized schema."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if draw_type:
            cursor.execute("""
            SELECT n1.number, n2.number, n3.number, COUNT(*) AS triplet_count
            FROM numbers n1
            JOIN numbers n2 
              ON n1.draw_id = n2.draw_id AND n1.number < n2.number
            JOIN numbers n3
              ON n1.draw_id = n3.draw_id AND n2.number < n3.number
            JOIN draws d ON n1.draw_id = d.id
            WHERE d.draw_type = ?
            GROUP BY n1.number, n2.number, n3.number
            ORDER BY triplet_count DESC, n1.number ASC, n2.number ASC, n3.number ASC
            LIMIT ?
            """, (draw_type, limit))
        else:
            cursor.execute("""
            SELECT n1.number, n2.number, n3.number, COUNT(*) AS triplet_count
            FROM numbers n1
            JOIN numbers n2 
              ON n1.draw_id = n2.draw_id AND n1.number < n2.number
            JOIN numbers n3
              ON n1.draw_id = n3.draw_id AND n2.number < n3.number
            GROUP BY n1.number, n2.number, n3.number
            ORDER BY triplet_count DESC, n1.number ASC, n2.number ASC, n3.number ASC
            LIMIT ?
            """, (limit,))

        results = cursor.fetchall()
        conn.close()
        return results
    
    def _most_frequent_triplets_denormalized(self, limit, draw_type):
        """For denormalized schema."""
        data = self.get_all_numbers_data(draw_type)
        triplets_count = Counter()
        
        for row in data:
            if self.schema_type == 'denormalized':
                numbers = [row[i] for i in range(2, 8) if row[i] is not None]
                for triplet in combinations(sorted(numbers), 3):
                    triplets_count[triplet] += 1
        
        return triplets_count.most_common(limit)
    
    def number_gap_analysis(self, draw_type=None):
        """Analyze gaps between consecutive draws for each number."""
        data = self.get_all_numbers_data(draw_type)
        number_appearances = defaultdict(list)
        
        draw_counter = 0
        if self.schema_type == 'denormalized':
            for row in data:
                numbers = [row[i] for i in range(2, 8) if row[i] is not None]
                for num in numbers:
                    number_appearances[num].append(draw_counter)
                draw_counter += 1
        else:
            # For normalized schema, group by draw_id
            current_draw_id = None
            for row in data:
                if row[3] != current_draw_id:  # draw_id changed
                    draw_counter += 1
                    current_draw_id = row[3]
                number_appearances[row[2]].append(draw_counter)
        
        # Calculate average gaps
        gap_stats = {}
        for num, appearances in number_appearances.items():
            if len(appearances) > 1:
                gaps = [appearances[i] - appearances[i-1] for i in range(1, len(appearances))]
                gap_stats[num] = {
                    'avg_gap': sum(gaps) / len(gaps),
                    'min_gap': min(gaps),
                    'max_gap': max(gaps),
                    'current_gap': draw_counter - appearances[-1]
                }
        
        return gap_stats
    
    def hot_cold_analysis(self, recent_draws=100, draw_type=None):
        """Analyze hot and cold numbers based on recent draws."""
        data = self.get_all_numbers_data(draw_type)
        recent_numbers = []
        
        if self.schema_type == 'denormalized':
            # Take last N draws
            recent_data = data[-recent_draws:] if len(data) > recent_draws else data
            for row in recent_data:
                numbers = [row[i] for i in range(2, 8) if row[i] is not None]
                recent_numbers.extend(numbers)
        else:
            # For normalized schema, need to count draws properly
            draw_ids = set()
            for row in reversed(data):
                if len(draw_ids) >= recent_draws:
                    break
                draw_ids.add(row[3])
                if row[3] in draw_ids:
                    recent_numbers.append(row[2])
        
        counter = Counter(recent_numbers)
        total_numbers = len(recent_numbers)
        
        hot_numbers = counter.most_common(10)
        cold_numbers = counter.most_common()[:-11:-1]  # Last 10
        
        return {
            'hot': hot_numbers,
            'cold': cold_numbers,
            'total_recent_numbers': total_numbers,
            'recent_draws_analyzed': min(recent_draws, len(data))
        }
    
    def export_analysis(self, filename=None, draw_type=None):
        """Export comprehensive analysis to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            draw_suffix = f"_{draw_type}" if draw_type else "_all"
            filename = f"uk49s_analysis{draw_suffix}_{timestamp}.json"
        
        analysis = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'draw_type': draw_type,
                'schema_type': self.schema_type
            },
            'most_frequent_numbers': self.most_frequent_numbers(20, draw_type),
            'most_frequent_pairs': self.most_frequent_pairs(15, draw_type),
            'most_frequent_triplets': self.most_frequent_triplets(10, draw_type),
            'gap_analysis': self.number_gap_analysis(draw_type),
            'hot_cold_analysis': self.hot_cold_analysis(100, draw_type)
        }
        
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"✅ Analysis exported to {filename}")
        return filename

def print_results(analyzer, draw_type=None):
    """Print formatted analysis results."""
    print(f"\n{'='*60}")
    print(f"🎰 UK49s Analysis Results")
    if draw_type:
        print(f"📊 Draw Type: {draw_type}")
    else:
        print(f"📊 Draw Type: All")
    print(f"🔧 Schema: {analyzer.schema_type}")
    print(f"{'='*60}")
    
    # Most frequent numbers
    numbers = analyzer.most_frequent_numbers(15, draw_type)
    print(f"\n🔢 Most Frequent Numbers:")
    for i, (num, freq) in enumerate(numbers, 1):
        print(f"   {i:2d}. Number {num:2d}: {freq:4d} times")
    
    # Most frequent pairs
    pairs = analyzer.most_frequent_pairs(10, draw_type)
    print(f"\n👥 Most Frequent Pairs:")
    for i, result in enumerate(pairs, 1):
        if len(result) == 2 and isinstance(result[0], tuple):
            # Denormalized result format: ((num1, num2), count)
            pair, freq = result
            print(f"   {i:2d}. ({pair[0]:2d}, {pair[1]:2d}): {freq:3d} times")
        else:
            # Normalized result format: (num1, num2, count)
            num1, num2, freq = result
            print(f"   {i:2d}. ({num1:2d}, {num2:2d}): {freq:3d} times")
    
    # Most frequent triplets
    triplets = analyzer.most_frequent_triplets(8, draw_type)
    print(f"\n🎲 Most Frequent Triplets:")
    for i, result in enumerate(triplets, 1):
        if len(result) == 2 and isinstance(result[0], tuple):
            # Denormalized result format: ((num1, num2, num3), count)
            triplet, freq = result
            print(f"   {i:2d}. ({triplet[0]:2d}, {triplet[1]:2d}, {triplet[2]:2d}): {freq:2d} times")
        else:
            # Normalized result format: (num1, num2, num3, count)
            num1, num2, num3, freq = result
            print(f"   {i:2d}. ({num1:2d}, {num2:2d}, {num3:2d}): {freq:2d} times")
    
    # Hot and cold analysis
    hot_cold = analyzer.hot_cold_analysis(50, draw_type)
    print(f"\n🔥 Hot Numbers (Last {hot_cold['recent_draws_analyzed']} draws):")
    for i, (num, freq) in enumerate(hot_cold['hot'][:8], 1):
        percentage = (freq / hot_cold['total_recent_numbers']) * 100
        print(f"   {i:2d}. Number {num:2d}: {freq:2d} times ({percentage:.1f}%)")
    
    print(f"\n🧊 Cold Numbers (Last {hot_cold['recent_draws_analyzed']} draws):")
    for i, (num, freq) in enumerate(hot_cold['cold'][:8], 1):
        percentage = (freq / hot_cold['total_recent_numbers']) * 100
        print(f"   {i:2d}. Number {num:2d}: {freq:2d} times ({percentage:.1f}%)")

def interactive_menu():
    """Interactive menu for analysis."""
    analyzer = UK49sAnalyzer()
    
    while True:
        print(f"\n{'='*50}")
        print("🎰 UK49s Advanced Analyzer")
        print(f"🔧 Detected Schema: {analyzer.schema_type}")
        print("="*50)
        print("1️⃣  Analyze All Draws")
        print("2️⃣  Analyze Lunchtime Only")
        print("3️⃣  Analyze Teatime Only")
        print("4️⃣  Export Analysis to JSON")
        print("5️⃣  Gap Analysis")
        print("6️⃣  Exit")
        print("-" * 50)
        
        choice = input("Choose an option: ").strip()
        
        if choice == "1":
            print_results(analyzer, None)
        elif choice == "2":
            print_results(analyzer, "Lunchtime")
        elif choice == "3":
            print_results(analyzer, "Teatime")
        elif choice == "4":
            draw_type = input("Export for which draw type? (Lunchtime/Teatime/All): ").strip()
            if draw_type.lower() == "all":
                draw_type = None
            elif draw_type not in ["Lunchtime", "Teatime"]:
                draw_type = None
            filename = analyzer.export_analysis(draw_type=draw_type)
            print(f"Analysis exported to: {filename}")
        elif choice == "5":
            draw_type = input("Gap analysis for which draw type? (Lunchtime/Teatime/All): ").strip()
            if draw_type.lower() == "all":
                draw_type = None
            elif draw_type not in ["Lunchtime", "Teatime"]:
                draw_type = None
            
            gaps = analyzer.number_gap_analysis(draw_type)
            print(f"\n📊 Gap Analysis ({draw_type or 'All'}):")
            print("Numbers with longest current gaps:")
            
            sorted_gaps = sorted(gaps.items(), key=lambda x: x[1]['current_gap'], reverse=True)
            for num, stats in sorted_gaps[:10]:
                print(f"   Number {num:2d}: Current gap {stats['current_gap']:3d} draws "
                      f"(Avg: {stats['avg_gap']:.1f})")
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    # Check if running interactively or with parameters
    import sys
    
    if len(sys.argv) > 1:
        # Command line usage
        draw_type = sys.argv[1] if sys.argv[1] != "All" else None
        analyzer = UK49sAnalyzer()
        print_results(analyzer, draw_type)
    else:
        # Interactive mode
        interactive_menu()
