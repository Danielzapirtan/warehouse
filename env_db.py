import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import your warehouse classes
from warehouse import DATABASE, PRODUCT, SHEET, PAGE, RECORD

class EnvWarehouseDB:
    """
    Environment variable integration for warehouse database with JSON format
    Stores the entire database as a JSON string in the WAREHOUSEDB environment variable
    """
    
    def __init__(self, env_var_name: str = 'WAREHOUSEDB'):
        """
        Initialize environment variable storage
        
        Args:
            env_var_name: Name of the environment variable to use
        """
        self.env_var_name = env_var_name
        
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
    
    def save_database(self, db: DATABASE) -> bool:
        """
        Save database to environment variable as JSON string
        
        Args:
            db: DATABASE object to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert database to dictionary
            db_dict = self._database_to_dict(db)
            
            # Convert to JSON string
            json_data = json.dumps(db_dict, ensure_ascii=False)
            
            # Store in environment variable
            os.environ[self.env_var_name] = json_data
            
            print(f"✓ Database saved to environment variable '{self.env_var_name}'")
            print(f"  Size: {len(json_data):,} characters")
            print(f"  Products: {db.maxproduct}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving database to environment variable: {e}")
            return False
    
    def load_database(self) -> Optional[DATABASE]:
        """
        Load database from environment variable
        
        Returns:
            DATABASE object if successful, None otherwise
        """
        try:
            # Get JSON string from environment variable
            json_data = os.environ.get(self.env_var_name)
            
            if json_data is None:
                print(f"❌ Environment variable '{self.env_var_name}' not found or empty")
                return None
            
            # Parse JSON and convert to DATABASE object
            db_dict = json.loads(json_data)
            db = self._dict_to_database(db_dict)
            
            metadata = db_dict.get('metadata', {})
            
            print(f"✓ Database loaded from environment variable '{self.env_var_name}'")
            print(f"  Created: {metadata.get('created_at', 'Unknown')}")
            print(f"  Version: {metadata.get('version', 'Unknown')}")
            print(f"  Size: {len(json_data):,} characters")
            print(f"  Products: {db.maxproduct}")
            
            return db
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON from environment variable: {e}")
            return None
        except Exception as e:
            print(f"❌ Error loading database from environment variable: {e}")
            return None
    
    def database_exists(self) -> bool:
        """
        Check if database exists in environment variable
        
        Returns:
            bool: True if database exists, False otherwise
        """
        return self.env_var_name in os.environ and bool(os.environ[self.env_var_name])
    
    def delete_database(self) -> bool:
        """
        Delete database from environment variable
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.env_var_name in os.environ:
                del os.environ[self.env_var_name]
                print(f"✓ Database deleted from environment variable '{self.env_var_name}'")
                return True
            else:
                print(f"❌ Environment variable '{self.env_var_name}' not found")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting database: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database stored in environment variable
        
        Returns:
            Dictionary with database information
        """
        try:
            json_data = os.environ.get(self.env_var_name)
            
            if json_data is None:
                return {'exists': False}
            
            # Parse JSON to get metadata
            db_dict = json.loads(json_data)
            metadata = db_dict.get('metadata', {})
            
            info = {
                'exists': True,
                'created_at': metadata.get('created_at', 'Unknown'),
                'version': metadata.get('version', 'Unknown'),
                'size': len(json_data),
                'total_products': metadata.get('total_products', 0)
            }
            
            print(f"📊 Database Information:")
            print(f"  Environment Variable: {self.env_var_name}")
            print(f"  Exists: {info['exists']}")
            print(f"  Created: {info['created_at']}")
            print(f"  Version: {info['version']}")
            print(f"  Size: {info['size']:,} characters")
            print(f"  Products: {info['total_products']}")
            
            return info
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON from environment variable: {e}")
            return {'exists': True, 'error': 'Invalid JSON format'}
        except Exception as e:
            print(f"❌ Error getting database info: {e}")
            return {'exists': False, 'error': str(e)}
    
    def export_to_file(self, filename: str) -> bool:
        """
        Export database from environment variable to a JSON file
        
        Args:
            filename: Name of the file to export to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            json_data = os.environ.get(self.env_var_name)
            
            if json_data is None:
                print(f"❌ Environment variable '{self.env_var_name}' not found or empty")
                return False
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                # Pretty print the JSON for better readability
                db_dict = json.loads(json_data)
                json.dump(db_dict, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Database exported to file '{filename}'")
            print(f"  Size: {len(json_data):,} characters")
            
            return True
            
        except Exception as e:
            print(f"❌ Error exporting database to file: {e}")
            return False
    
    def import_from_file(self, filename: str) -> bool:
        """
        Import database from a JSON file to environment variable
        
        Args:
            filename: Name of the file to import from
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read from file
            with open(filename, 'r', encoding='utf-8') as f:
                db_dict = json.load(f)
            
            # Convert to JSON string and store in environment variable
            json_data = json.dumps(db_dict, ensure_ascii=False)
            os.environ[self.env_var_name] = json_data
            
            print(f"✓ Database imported from file '{filename}' to environment variable '{self.env_var_name}'")
            print(f"  Size: {len(json_data):,} characters")
            
            return True
            
        except FileNotFoundError:
            print(f"❌ File '{filename}' not found")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON from file: {e}")
            return False
        except Exception as e:
            print(f"❌ Error importing database from file: {e}")
            return False

# Convenience functions for easy usage
def save_warehouse_db(db: DATABASE, env_var_name: str = 'WAREHOUSEDB') -> bool:
    """
    Quick save function for warehouse database to environment variable
    
    Args:
        db: DATABASE object to save
        env_var_name: Name of environment variable to use
        
    Returns:
        bool: True if successful, False otherwise
    """
    env_db = EnvWarehouseDB(env_var_name)
    return env_db.save_database(db)

def load_warehouse_db(env_var_name: str = 'WAREHOUSEDB') -> Optional[DATABASE]:
    """
    Quick load function for warehouse database from environment variable
    
    Args:
        env_var_name: Name of environment variable to use
        
    Returns:
        DATABASE object if successful, None otherwise
    """
    env_db = EnvWarehouseDB(env_var_name)
    return env_db.load_database()

def database_exists(env_var_name: str = 'WAREHOUSEDB') -> bool:
    """
    Quick function to check if database exists in environment variable
    
    Args:
        env_var_name: Name of environment variable to check
        
    Returns:
        bool: True if database exists, False otherwise
    """
    env_db = EnvWarehouseDB(env_var_name)
    return env_db.database_exists()

def get_database_info(env_var_name: str = 'WAREHOUSEDB') -> Dict[str, Any]:
    """
    Quick function to get database information from environment variable
    
    Args:
        env_var_name: Name of environment variable to check
        
    Returns:
        Dictionary with database information
    """
    env_db = EnvWarehouseDB(env_var_name)
    return env_db.get_database_info()

def backup_database(db: DATABASE, backup_env_var: str = None) -> bool:
    """
    Create a backup of the database in a different environment variable
    
    Args:
        db: DATABASE object to backup
        backup_env_var: Environment variable name for backup (default: WAREHOUSEDB_BACKUP_YYYYMMDD_HHMMSS)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if backup_env_var is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_env_var = f"WAREHOUSEDB_BACKUP_{timestamp}"
    
    print(f"🔄 Creating backup in environment variable '{backup_env_var}'...")
    
    success = save_warehouse_db(db, backup_env_var)
    
    if success:
        print(f"✓ Backup created successfully in environment variable '{backup_env_var}'")
        return True
    else:
        print(f"❌ Failed to create backup in '{backup_env_var}'")
        return False

def demo_env_storage():
    """Demonstration of environment variable functionality"""
    print("🚀 Warehouse Database Environment Variable Demo")
    print("=" * 60)
    print(f"📝 Using environment variable: WAREHOUSEDB")
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
        print("\n💾 Saving database to environment variable...")
        success = save_warehouse_db(db)
        
        if success:
            print("\n📋 Database information:")
            get_database_info()
            
            print(f"\n📖 Loading database from environment variable...")
            loaded_db = load_warehouse_db()
            
            if loaded_db:
                print(f"✓ Loaded database with {loaded_db.maxproduct} products")
                
                # Create a backup
                print(f"\n🔄 Creating backup...")
                backup_success = backup_database(loaded_db)
                
                if backup_success:
                    print("✓ Backup created successfully")
                
                # Export to file
                print(f"\n📤 Exporting to file...")
                env_db = EnvWarehouseDB()
                export_success = env_db.export_to_file("warehouse_export.json")
                
                if export_success:
                    print("✓ Database exported to 'warehouse_export.json'")
                
            else:
                print("❌ Failed to load database")
            
        else:
            print("❌ Failed to save database to environment variable")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    # Run demo if script is executed directly
    demo_env_storage()