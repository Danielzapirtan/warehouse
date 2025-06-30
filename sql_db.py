import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

# Import your warehouse classes
from warehouse import DATABASE, PRODUCT, SHEET, PAGE, RECORD

class PostgreSQLWarehouseDB:
    """
    PostgreSQL integration for warehouse database with JSON format
    Compatible with Render's free PostgreSQL tier
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize PostgreSQL connection
        
        Args:
            database_url: PostgreSQL connection URL (default: from DATABASE_URL env var)
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Parse URL for connection
        self.db_config = self._parse_database_url(self.database_url)
        self._init_tables()
    
    def _parse_database_url(self, url: str) -> Dict[str, str]:
        """Parse DATABASE_URL into connection parameters"""
        parsed = urlparse(url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],  # Remove leading '/'
            'user': parsed.username,
            'password': parsed.password
        }
    
    def _get_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(**self.db_config)
    
    def _init_tables(self):
        """Initialize database tables if they don't exist"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create main warehouse_databases table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS warehouse_databases (
                        id SERIAL PRIMARY KEY,
                        filename VARCHAR(255) UNIQUE NOT NULL,
                        data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        size_bytes INTEGER DEFAULT 0
                    )
                """)
                
                # Create index for faster queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_warehouse_filename 
                    ON warehouse_databases(filename)
                """)
                
                # Create index for JSON queries (PostgreSQL specific)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_warehouse_metadata 
                    ON warehouse_databases USING GIN (data)
                """)
                
                conn.commit()
                print("✓ Database tables initialized")
                
        except Exception as e:
            print(f"❌ Error initializing tables: {e}")
            raise
    
    def _database_to_dict(self, db: DATABASE) -> Dict[str, Any]:
        """Convert DATABASE object to dictionary for JSON serialization"""
        db_dict = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'total_products': db.maxproduct
            },
            'database': {
                'crtproduct': db.crtproduct,
                'maxproduct': db.maxproduct,
                'products': []
            }
        }
        
        for product in db.products:
            product_dict = {
                'name': product.name,
                'unit': product.unit,
                'crtsheet': product.crtsheet,
                'maxsheet': product.maxsheet,
                'sheets': []
            }
            
            for sheet in product.sheets:
                sheet_dict = {
                    'year': sheet.year,
                    'month': sheet.month,
                    'crtpage': sheet.crtpage,
                    'maxpage': sheet.maxpage,
                    'pages': []
                }
                
                for page in sheet.pages:
                    page_dict = {
                        'price': page.price,
                        'sold_init': page.sold_init,
                        'sold_final': page.sold_final,
                        'crtrecord': page.crtrecord,
                        'maxrecord': page.maxrecord,
                        'records': []
                    }
                    
                    for record in page.records:
                        record_dict = {
                            'input': record.input,
                            'output': record.output,
                            'sold_final': record.sold_final,
                            'sold_init': record.sold_init,
                            'doc_id': record.doc_id,
                            'doc_type': record.doc_type,
                            'dom': record.dom
                        }
                        page_dict['records'].append(record_dict)
                    
                    sheet_dict['pages'].append(page_dict)
                
                product_dict['sheets'].append(sheet_dict)
            
            db_dict['database']['products'].append(product_dict)
        
        return db_dict
    
    def _dict_to_database(self, db_dict: Dict[str, Any]) -> DATABASE:
        """Convert dictionary back to DATABASE object"""
        db = DATABASE()
        db.init()
        
        db_data = db_dict['database']
        db.crtproduct = db_data['crtproduct']
        db.maxproduct = db_data['maxproduct']
        
        for product_data in db_data['products']:
            product = PRODUCT()
            product.database = db
            product.init(product_data['name'], product_data['unit'])
            product.crtsheet = product_data['crtsheet']
            product.maxsheet = product_data['maxsheet']
            
            for sheet_data in product_data['sheets']:
                sheet = SHEET()
                sheet.product = product
                sheet.init(sheet_data['year'], sheet_data['month'])
                sheet.crtpage = sheet_data['crtpage']
                sheet.maxpage = sheet_data['maxpage']
                
                for page_data in sheet_data['pages']:
                    page = PAGE()
                    page.sheet = sheet
                    page.init(page_data['price'], page_data['sold_init'])
                    page.sold_final = page_data['sold_final']
                    page.crtrecord = page_data['crtrecord']
                    page.maxrecord = page_data['maxrecord']
                    
                    for record_data in page_data['records']:
                        record = RECORD()
                        record.page = page
                        record.init(
                            record_data['input'],
                            record_data['output'],
                            record_data['sold_final'],
                            record_data['sold_init'],
                            record_data['doc_id'],
                            record_data['doc_type'],
                            record_data['dom']
                        )
                        page.records.append(record)
                    
                    sheet.pages.append(page)
                
                product.sheets.append(sheet)
            
            db.products.append(product)
        
        return db
    
    def save_database(self, db: DATABASE, filename: str = None) -> bool:
        """
        Save database to PostgreSQL as JSON
        
        Args:
            db: DATABASE object to save
            filename: Optional filename (default: warehouse_db_YYYYMMDD_HHMMSS)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"warehouse_db_{timestamp}"
            
            # Convert database to dictionary
            db_dict = self._database_to_dict(db)
            json_data = json.dumps(db_dict, ensure_ascii=False)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert or update database record
                cursor.execute("""
                    INSERT INTO warehouse_databases (filename, data, size_bytes, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (filename) 
                    DO UPDATE SET 
                        data = EXCLUDED.data,
                        size_bytes = EXCLUDED.size_bytes,
                        updated_at = CURRENT_TIMESTAMP
                """, (filename, json_data, len(json_data)))
                
                conn.commit()
            
            print(f"✓ Database saved as '{filename}' to PostgreSQL")
            print(f"  Size: {len(json_data):,} characters")
            print(f"  Products: {db.maxproduct}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving database to PostgreSQL: {e}")
            return False
    
    def load_database(self, filename: str) -> Optional[DATABASE]:
        """
        Load database from PostgreSQL
        
        Args:
            filename: Name of the database to load
            
        Returns:
            DATABASE object if successful, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                cursor.execute("""
                    SELECT data, created_at, size_bytes 
                    FROM warehouse_databases 
                    WHERE filename = %s
                """, (filename,))
                
                row = cursor.fetchone()
                
                if row is None:
                    print(f"❌ Database '{filename}' not found in PostgreSQL")
                    return None
                
                # Parse JSON and convert to DATABASE object
                db_dict = row['data']
                db = self._dict_to_database(db_dict)
                
                metadata = db_dict.get('metadata', {})
                
                print(f"✓ Database loaded from '{filename}'")
                print(f"  Created: {row['created_at']}")
                print(f"  Version: {metadata.get('version', 'Unknown')}")
                print(f"  Size: {row['size_bytes']:,} characters")
                print(f"  Products: {db.maxproduct}")
                
                return db
                
        except Exception as e:
            print(f"❌ Error loading database from PostgreSQL: {e}")
            return None
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """
        List all databases stored in PostgreSQL
        
        Returns:
            List of database information dictionaries
        """
        try:
            databases = []
            
            with self._get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                cursor.execute("""
                    SELECT filename, created_at, updated_at, size_bytes,
                           data->'metadata'->>'total_products' as total_products
                    FROM warehouse_databases 
                    ORDER BY updated_at DESC
                """)
                
                rows = cursor.fetchall()
                
                print(f"📁 Databases in PostgreSQL:")
                print("-" * 60)
                
                if not rows:
                    print("  No databases found")
                    return databases
                
                for row in rows:
                    print(f"📄 {row['filename']}")
                    print(f"   Created: {row['created_at']}")
                    print(f"   Updated: {row['updated_at']}")
                    print(f"   Size: {row['size_bytes']:,} characters")
                    print(f"   Products: {row['total_products'] or 'Unknown'}")
                    print()
                    
                    databases.append({
                        'name': row['filename'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'size': row['size_bytes'],
                        'total_products': row['total_products']
                    })
                
                return databases
                
        except Exception as e:
            print(f"❌ Error listing databases: {e}")
            return []
    
    def delete_database(self, filename: str) -> bool:
        """
        Delete a database from PostgreSQL
        
        Args:
            filename: Name of the database to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if exists and delete
                cursor.execute("""
                    DELETE FROM warehouse_databases 
                    WHERE filename = %s
                """, (filename,))
                
                if cursor.rowcount == 0:
                    print(f"❌ Database '{filename}' not found in PostgreSQL")
                    return False
                
                conn.commit()
                
                print(f"✓ Database '{filename}' deleted from PostgreSQL")
                return True
                
        except Exception as e:
            print(f"❌ Error deleting database: {e}")
            return False
    
    def clear_all_databases(self) -> bool:
        """
        Clear all warehouse databases from PostgreSQL
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM warehouse_databases")
                count = cursor.fetchone()[0]
                
                cursor.execute("DELETE FROM warehouse_databases")
                conn.commit()
                
                print(f"✓ Cleared {count} warehouse databases from PostgreSQL")
                return True
                
        except Exception as e:
            print(f"❌ Error clearing databases: {e}")
            return False
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """
        Get PostgreSQL storage usage information
        
        Returns:
            Dictionary with usage statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Get warehouse database statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as database_count,
                        SUM(size_bytes) as total_size,
                        AVG(size_bytes) as avg_size,
                        MAX(size_bytes) as max_size,
                        MIN(size_bytes) as min_size
                    FROM warehouse_databases
                """)
                
                stats = cursor.fetchone()
                
                # Get table size information
                cursor.execute("""
                    SELECT pg_total_relation_size('warehouse_databases') as table_size
                """)
                
                table_info = cursor.fetchone()
                
                usage_info = {
                    'database_count': stats['database_count'] or 0,
                    'total_content_size': stats['total_size'] or 0,
                    'average_size': stats['avg_size'] or 0,
                    'max_size': stats['max_size'] or 0,
                    'min_size': stats['min_size'] or 0,
                    'table_size_bytes': table_info['table_size'] or 0
                }
                
                print(f"📊 PostgreSQL Usage:")
                print(f"  Number of databases: {usage_info['database_count']}")
                print(f"  Total content size: {usage_info['total_content_size']:,} characters")
                print(f"  Average database size: {usage_info['average_size']:,.0f} characters")
                print(f"  Table size on disk: {usage_info['table_size_bytes']:,} bytes")
                
                return usage_info
                
        except Exception as e:
            print(f"❌ Error getting storage usage: {e}")
            return {}
    
    def search_databases(self, search_term: str = None, 
                        min_products: int = None,
                        created_after: datetime = None) -> List[Dict[str, Any]]:
        """
        Search databases with filters
        
        Args:
            search_term: Search in filename
            min_products: Minimum number of products
            created_after: Created after this date
            
        Returns:
            List of matching databases
        """
        try:
            conditions = []
            params = []
            
            if search_term:
                conditions.append("filename ILIKE %s")
                params.append(f"%{search_term}%")
            
            if min_products is not None:
                conditions.append("CAST(data->'metadata'->>'total_products' AS INTEGER) >= %s")
                params.append(min_products)
            
            if created_after:
                conditions.append("created_at >= %s")
                params.append(created_after)
            
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            with self._get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                query = f"""
                    SELECT filename, created_at, updated_at, size_bytes,
                           data->'metadata'->>'total_products' as total_products
                    FROM warehouse_databases 
                    WHERE {where_clause}
                    ORDER BY updated_at DESC
                """
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    results.append({
                        'name': row['filename'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'size': row['size_bytes'],
                        'total_products': row['total_products']
                    })
                
                print(f"🔍 Found {len(results)} databases matching criteria")
                return results
                
        except Exception as e:
            print(f"❌ Error searching databases: {e}")
            return []

# Convenience functions for easy usage
def save_warehouse_db(db: DATABASE, filename: str = None) -> bool:
    """
    Quick save function for warehouse database to PostgreSQL
    
    Args:
        db: DATABASE object to save
        filename: Optional filename
        
    Returns:
        bool: True if successful, False otherwise
    """
    postgres_db = PostgreSQLWarehouseDB()
    return postgres_db.save_database(db, filename)

def load_warehouse_db(filename: str) -> Optional[DATABASE]:
    """
    Quick load function for warehouse database from PostgreSQL
    
    Args:
        filename: Name of the database to load
        
    Returns:
        DATABASE object if successful, None otherwise
    """
    postgres_db = PostgreSQLWarehouseDB()
    return postgres_db.load_database(filename)

def list_warehouse_databases() -> List[Dict[str, Any]]:
    """
    Quick function to list warehouse databases in PostgreSQL
    
    Returns:
        List of database information dictionaries
    """
    postgres_db = PostgreSQLWarehouseDB()
    return postgres_db.list_databases()

def backup_database(db: DATABASE, backup_name: str = None) -> bool:
    """
    Create a backup of the database with a specific name
    
    Args:
        db: DATABASE object to backup
        backup_name: Optional backup name (default: backup_YYYYMMDD_HHMMSS)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if backup_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
    
    print(f"🔄 Creating backup '{backup_name}' in PostgreSQL...")
    
    success = save_warehouse_db(db, backup_name)
    
    if success:
        print(f"✓ Backup '{backup_name}' created successfully in PostgreSQL")
        return True
    else:
        print(f"❌ Failed to create backup '{backup_name}'")
        return False

def demo_postgres_storage():
    """Demonstration of PostgreSQL functionality"""
    print("🚀 Warehouse Database PostgreSQL Demo")
    print("=" * 60)
    print("📋 Using PostgreSQL database for persistent storage")
    print()
    
    try:
        # Import your database
        from warehouse import db
        
        # Add some sample data if database is empty
        if db.maxproduct == 0:
            print("📝 Creating sample data...")
            
            # Create a product
            product = db.create_product("Sample Product", "kg")
            
            # Create a sheet for current month
            sheet = product.create_sheet(2025, 6)
            
            # Create a page with initial inventory
            page = sheet.create_page(10.50, 100.0)  # price: 10.50, initial stock: 100
            
            # Add some records
            page.create_record(50.0, 0.0, "DOC001", "INPUT", 1)    # Receive 50 units
            page.create_record(0.0, 20.0, "DOC002", "OUTPUT", 2)   # Sell 20 units
            page.create_record(30.0, 0.0, "DOC003", "INPUT", 3)    # Receive 30 more
            
            print("✓ Sample data created")
        
        # Save database
        print("\n💾 Saving database to PostgreSQL...")
        success = save_warehouse_db(db)
        
        if success:
            print("\n📋 Listing databases in PostgreSQL...")
            databases = list_warehouse_databases()
            
            if databases:
                # Try loading the most recent database
                latest_db_name = databases[0]['name']  # Already sorted by updated_at DESC
                print(f"\n📖 Loading database '{latest_db_name}' from PostgreSQL...")
                loaded_db = load_warehouse_db(latest_db_name)
                
                if loaded_db:
                    print(f"✓ Loaded database with {loaded_db.maxproduct} products")
                else:
                    print("❌ Failed to load database")
            
            # Show storage usage
            print("\n📊 Storage information:")
            postgres_db = PostgreSQLWarehouseDB()
            postgres_db.get_storage_usage()
            
        else:
            print("❌ Failed to save database to PostgreSQL")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("Make sure DATABASE_URL environment variable is set with PostgreSQL connection string")

# Environment setup helper
def setup_environment_example():
    """Show example of how to set up environment variables"""
    print("🔧 Environment Setup for Render:")
    print("=" * 50)
    print("Set these environment variables in your Render dashboard:")
    print()
    print("DATABASE_URL=postgresql://username:password@host:port/database")
    print()
    print("Example for Render's free PostgreSQL:")
    print("DATABASE_URL=postgresql://user:pass@dpg-xxxxx-a.oregon-postgres.render.com/dbname")
    print()
    print("The DATABASE_URL is automatically provided by Render when you create a PostgreSQL service.")

if __name__ == "__main__":
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable not set")
        setup_environment_example()
    else:
        # Run demo if script is executed directly
        demo_postgres_storage()