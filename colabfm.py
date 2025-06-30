import json
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import your warehouse classes
from warehouse import DATABASE, PRODUCT, SHEET, PAGE, RECORD

class BrowserWarehouseDB:
    """
    Browser localStorage integration for warehouse database with JSON format
    NOTE: This code is designed for browser environments where localStorage is available
    It will NOT work in Claude.ai artifacts - use only in external browser environments
    """
    
    def __init__(self, storage_prefix: str = 'warehouse_db'):
        """
        Initialize browser localStorage storage
        
        Args:
            storage_prefix: Prefix for localStorage keys to avoid conflicts
        """
        self.storage_prefix = storage_prefix
        self.metadata_key = f"{storage_prefix}_metadata"
        
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
    
    def _check_localStorage_available(self) -> bool:
        """Check if localStorage is available in the current environment"""
        try:
            # This would work in a browser environment with JavaScript
            # In Python, we'd need to use a browser automation library like Selenium
            # or run this code in a web context with PyScript/Pyodide
            import js  # This would be available in PyScript/Pyodide
            return hasattr(js, 'localStorage')
        except ImportError:
            print("❌ localStorage not available - this code requires a browser environment")
            return False
    
    def save_database(self, db: DATABASE, filename: str = None) -> bool:
        """
        Save database to browser localStorage as JSON
        
        Args:
            db: DATABASE object to save
            filename: Optional filename (default: warehouse_db_YYYYMMDD_HHMMSS)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self._check_localStorage_available():
                return False
                
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"warehouse_db_{timestamp}"
            
            # Convert database to dictionary
            db_dict = self._database_to_dict(db)
            
            # Save to localStorage
            storage_key = f"{self.storage_prefix}_{filename}"
            json_data = json.dumps(db_dict, ensure_ascii=False)
            
            # In a browser environment with PyScript/Pyodide:
            import js
            js.localStorage.setItem(storage_key, json_data)
            
            # Update metadata with list of saved databases
            self._update_metadata(filename, len(json_data))
            
            print(f"✓ Database saved as '{filename}' to localStorage")
            print(f"  Key: {storage_key}")
            print(f"  Size: {len(json_data):,} characters")
            print(f"  Products: {db.maxproduct}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving database to localStorage: {e}")
            return False
    
    def load_database(self, filename: str) -> Optional[DATABASE]:
        """
        Load database from browser localStorage
        
        Args:
            filename: Name of the database to load
            
        Returns:
            DATABASE object if successful, None otherwise
        """
        try:
            if not self._check_localStorage_available():
                return None
                
            storage_key = f"{self.storage_prefix}_{filename}"
            
            # Load from localStorage
            import js
            json_data = js.localStorage.getItem(storage_key)
            
            if json_data is None:
                print(f"❌ Database '{filename}' not found in localStorage")
                return None
            
            # Parse JSON and convert to DATABASE object
            db_dict = json.loads(json_data)
            db = self._dict_to_database(db_dict)
            
            metadata = db_dict.get('metadata', {})
            
            print(f"✓ Database loaded from '{filename}'")
            print(f"  Created: {metadata.get('created_at', 'Unknown')}")
            print(f"  Version: {metadata.get('version', 'Unknown')}")
            print(f"  Size: {len(json_data):,} characters")
            print(f"  Products: {db.maxproduct}")
            
            return db
            
        except Exception as e:
            print(f"❌ Error loading database from localStorage: {e}")
            return None
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """
        List all databases stored in localStorage
        
        Returns:
            List of database information dictionaries
        """
        try:
            if not self._check_localStorage_available():
                return []
                
            databases = []
            
            # Get metadata
            metadata = self._get_metadata()
            
            print(f"📁 Databases in localStorage (prefix: {self.storage_prefix}):")
            print("-" * 60)
            
            if not metadata.get('databases'):
                print("  No databases found")
                return databases
            
            for db_name, db_info in metadata['databases'].items():
                print(f"📄 {db_name}")
                print(f"   Created: {db_info.get('created_at', 'Unknown')}")
                print(f"   Size: {db_info.get('size', 0):,} characters")
                print()
                
                databases.append({
                    'name': db_name,
                    'created_at': db_info.get('created_at'),
                    'size': db_info.get('size', 0)
                })
            
            return databases
            
        except Exception as e:
            print(f"❌ Error listing databases: {e}")
            return []
    
    def delete_database(self, filename: str) -> bool:
        """
        Delete a database from localStorage
        
        Args:
            filename: Name of the database to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self._check_localStorage_available():
                return False
                
            storage_key = f"{self.storage_prefix}_{filename}"
            
            import js
            
            # Check if exists
            if js.localStorage.getItem(storage_key) is None:
                print(f"❌ Database '{filename}' not found in localStorage")
                return False
            
            # Remove from localStorage
            js.localStorage.removeItem(storage_key)
            
            # Update metadata
            self._remove_from_metadata(filename)
            
            print(f"✓ Database '{filename}' deleted from localStorage")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting database: {e}")
            return False
    
    def clear_all_databases(self) -> bool:
        """
        Clear all warehouse databases from localStorage
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self._check_localStorage_available():
                return False
                
            import js
            
            # Get all keys that match our prefix
            keys_to_remove = []
            for i in range(js.localStorage.length):
                key = js.localStorage.key(i)
                if key and key.startswith(self.storage_prefix):
                    keys_to_remove.append(key)
            
            # Remove all matching keys
            for key in keys_to_remove:
                js.localStorage.removeItem(key)
            
            print(f"✓ Cleared {len(keys_to_remove)} warehouse databases from localStorage")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing databases: {e}")
            return False
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Get metadata about stored databases"""
        try:
            import js
            metadata_json = js.localStorage.getItem(self.metadata_key)
            if metadata_json:
                return json.loads(metadata_json)
            return {'databases': {}}
        except:
            return {'databases': {}}
    
    def _update_metadata(self, filename: str, size: int):
        """Update metadata with new database info"""
        try:
            metadata = self._get_metadata()
            metadata['databases'][filename] = {
                'created_at': datetime.now().isoformat(),
                'size': size
            }
            
            import js
            js.localStorage.setItem(self.metadata_key, json.dumps(metadata))
        except Exception as e:
            print(f"⚠️  Warning: Could not update metadata: {e}")
    
    def _remove_from_metadata(self, filename: str):
        """Remove database from metadata"""
        try:
            metadata = self._get_metadata()
            if filename in metadata['databases']:
                del metadata['databases'][filename]
                
                import js
                js.localStorage.setItem(self.metadata_key, json.dumps(metadata))
        except Exception as e:
            print(f"⚠️  Warning: Could not update metadata: {e}")
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """
        Get localStorage usage information
        
        Returns:
            Dictionary with usage statistics
        """
        try:
            if not self._check_localStorage_available():
                return {}
                
            import js
            
            total_size = 0
            warehouse_size = 0
            warehouse_count = 0
            
            # Calculate total localStorage usage
            for i in range(js.localStorage.length):
                key = js.localStorage.key(i)
                if key:
                    value = js.localStorage.getItem(key)
                    item_size = len(key) + len(value or '')
                    total_size += item_size
                    
                    if key.startswith(self.storage_prefix):
                        warehouse_size += item_size
                        warehouse_count += 1
            
            usage_info = {
                'total_localStorage_size': total_size,
                'warehouse_size': warehouse_size,
                'warehouse_count': warehouse_count,
                'warehouse_percentage': (warehouse_size / total_size * 100) if total_size > 0 else 0
            }
            
            print(f"📊 localStorage Usage:")
            print(f"  Total localStorage: {total_size:,} characters")
            print(f"  Warehouse databases: {warehouse_size:,} characters ({usage_info['warehouse_percentage']:.1f}%)")
            print(f"  Number of warehouse DBs: {warehouse_count}")
            
            return usage_info
            
        except Exception as e:
            print(f"❌ Error getting storage usage: {e}")
            return {}

# Convenience functions for easy usage
def save_warehouse_db(db: DATABASE, filename: str = None) -> bool:
    """
    Quick save function for warehouse database to localStorage
    
    Args:
        db: DATABASE object to save
        filename: Optional filename
        
    Returns:
        bool: True if successful, False otherwise
    """
    browser_db = BrowserWarehouseDB()
    return browser_db.save_database(db, filename)

def load_warehouse_db(filename: str) -> Optional[DATABASE]:
    """
    Quick load function for warehouse database from localStorage
    
    Args:
        filename: Name of the database to load
        
    Returns:
        DATABASE object if successful, None otherwise
    """
    browser_db = BrowserWarehouseDB()
    return browser_db.load_database(filename)

def list_warehouse_databases() -> List[Dict[str, Any]]:
    """
    Quick function to list warehouse databases in localStorage
    
    Returns:
        List of database information dictionaries
    """
    browser_db = BrowserWarehouseDB()
    return browser_db.list_databases()

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
    
    print(f"🔄 Creating backup '{backup_name}' in localStorage...")
    
    success = save_warehouse_db(db, backup_name)
    
    if success:
        print(f"✓ Backup '{backup_name}' created successfully in localStorage")
        return True
    else:
        print(f"❌ Failed to create backup '{backup_name}'")
        return False

def demo_browser_storage():
    """Demonstration of localStorage functionality"""
    print("🚀 Warehouse Database Browser localStorage Demo")
    print("=" * 60)
    print("⚠️  NOTE: This requires a browser environment with localStorage support")
    print("   This will NOT work in Claude.ai artifacts!")
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
        print("\n💾 Saving database to localStorage...")
        success = save_warehouse_db(db)
        
        if success:
            print("\n📋 Listing databases in localStorage...")
            databases = list_warehouse_databases()
            
            if databases:
                # Try loading the most recent database
                latest_db_name = databases[-1]['name']
                print(f"\n📖 Loading database '{latest_db_name}' from localStorage...")
                loaded_db = load_warehouse_db(latest_db_name)
                
                if loaded_db:
                    print(f"✓ Loaded database with {loaded_db.maxproduct} products")
                else:
                    print("❌ Failed to load database")
            
            # Show storage usage
            print("\n📊 Storage information:")
            browser_db = BrowserWarehouseDB()
            browser_db.get_storage_usage()
            
        else:
            print("❌ Failed to save database to localStorage")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("This code requires a browser environment with localStorage support")

if __name__ == "__main__":
    # Run demo if script is executed directly
    demo_browser_storage()