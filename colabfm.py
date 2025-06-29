import json
import pickle
import os
import glob
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import your warehouse classes
from warehouse import DATABASE, PRODUCT, SHEET, PAGE, RECORD

folder_path = '/content/drive/MyDrive/WarehouseDB'
class ColabWarehouseDB:
    """
    Colab temporary file system integration for warehouse database with JSON and binary formats
    Designed for Google Colab environment using local temporary storage
    """
    
    def __init__(self, folder_path: str = folder_path):
        """
        Initialize local file system storage
        
        Args:
            folder_path: Path to store database files in Colab's temporary file system
        """
        self.folder_path = folder_path
        self._setup_folder()
        
    def _setup_folder(self):
        """Create the database folder if it doesn't exist"""
        try:
            if not os.path.exists(self.folder_path):
                os.makedirs(self.folder_path)
                print(f"✓ Created folder '{self.folder_path}'")
            else:
                print(f"✓ Using existing folder '{self.folder_path}'")
                
        except Exception as e:
            print(f"❌ Error setting up folder: {e}")
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
    
    def save_database_json(self, db: DATABASE, filename: str = None) -> bool:
        """
        Save database to local file system as JSON file
        
        Args:
            db: DATABASE object to save
            filename: Optional filename (default: warehouse_db_YYYYMMDD_HHMMSS.json)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"warehouse_db_{timestamp}.json"
            
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            file_path = os.path.join(self.folder_path, filename)
            
            # Convert database to dictionary
            db_dict = self._database_to_dict(db)
            
            # Save as JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(db_dict, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(file_path)
            
            print(f"✓ Database saved as '{filename}'")
            print(f"  Path: {file_path}")
            print(f"  Size: {file_size:,} bytes")
            print(f"  Products: {db.maxproduct}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving database: {e}")
            return False
    
    def save_database_binary(self, db: DATABASE, filename: str = None) -> bool:
        """
        Save database to local file system as binary pickle file
        
        Args:
            db: DATABASE object to save
            filename: Optional filename (default: warehouse_db_YYYYMMDD_HHMMSS.pkl)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"warehouse_db_{timestamp}.pkl"
            
            # Ensure filename has .pkl extension
            if not filename.endswith('.pkl'):
                filename += '.pkl'
            
            file_path = os.path.join(self.folder_path, filename)
            
            # Save as pickle file
            with open(file_path, 'wb') as f:
                pickle.dump(db, f)
            
            file_size = os.path.getsize(file_path)
            
            print(f"✓ Database saved as '{filename}' (binary)")
            print(f"  Path: {file_path}")
            print(f"  Size: {file_size:,} bytes")
            print(f"  Products: {db.maxproduct}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving database (binary): {e}")
            return False
    
    def load_database_json(self, filename: str) -> Optional[DATABASE]:
        """
        Load database from local JSON file
        
        Args:
            filename: Name of the JSON file to load
            
        Returns:
            DATABASE object if successful, None otherwise
        """
        try:
            # Add .json extension if not present
            if not filename.endswith('.json'):
                filename += '.json'
            
            file_path = os.path.join(self.folder_path, filename)
            
            if not os.path.exists(file_path):
                print(f"❌ File '{filename}' not found in {self.folder_path}")
                return None
            
            # Load and parse JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                db_dict = json.load(f)
            
            # Convert to DATABASE object
            db = self._dict_to_database(db_dict)
            
            metadata = db_dict.get('metadata', {})
            file_size = os.path.getsize(file_path)
            
            print(f"✓ Database loaded from '{filename}'")
            print(f"  Created: {metadata.get('created_at', 'Unknown')}")
            print(f"  Version: {metadata.get('version', 'Unknown')}")
            print(f"  Size: {file_size:,} bytes")
            print(f"  Products: {db.maxproduct}")
            
            return db
            
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            return None
    
    def load_database_binary(self, filename: str) -> Optional[DATABASE]:
        """
        Load database from local binary pickle file
        
        Args:
            filename: Name of the pickle file to load
            
        Returns:
            DATABASE object if successful, None otherwise
        """
        try:
            # Add .pkl extension if not present
            if not filename.endswith('.pkl'):
                filename += '.pkl'
            
            file_path = os.path.join(self.folder_path, filename)
            
            if not os.path.exists(file_path):
                print(f"❌ File '{filename}' not found in {self.folder_path}")
                return None
            
            # Load pickle file
            with open(file_path, 'rb') as f:
                db = pickle.load(f)
            
            file_size = os.path.getsize(file_path)
            
            print(f"✓ Database loaded from '{filename}' (binary)")
            print(f"  Size: {file_size:,} bytes")
            print(f"  Products: {db.maxproduct}")
            
            return db
            
        except Exception as e:
            print(f"❌ Error loading database (binary): {e}")
            return None
    
    def list_database_files(self) -> List[Dict[str, Any]]:
        """
        List all database files in the local folder
        
        Returns:
            List of file information dictionaries
        """
        try:
            files_info = []
            
            # Get all files in the folder
            pattern = os.path.join(self.folder_path, "*")
            files = glob.glob(pattern)
            
            print(f"📁 Files in '{self.folder_path}':")
            print("-" * 60)
            
            if not files:
                print("  No files found")
                return files_info
            
            for file_path in sorted(files):
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    file_info = {
                        'name': filename,
                        'path': file_path,
                        'size': file_size,
                        'modified': modified_time.isoformat()
                    }
                    files_info.append(file_info)
                    
                    # Determine file type
                    if filename.endswith('.json'):
                        file_type = "📄 JSON"
                    elif filename.endswith('.pkl'):
                        file_type = "📦 Binary"
                    else:
                        file_type = "📋 Other"
                    
                    print(f"{file_type} {filename}")
                    print(f"   Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   Size: {file_size:,} bytes")
                    print()
            
            return files_info
            
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []
    
    def delete_database_file(self, filename: str) -> bool:
        """
        Delete a database file from local storage
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = os.path.join(self.folder_path, filename)
            
            if not os.path.exists(file_path):
                print(f"❌ File '{filename}' not found in {self.folder_path}")
                return False
            
            os.remove(file_path)
            print(f"✓ File '{filename}' deleted")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting file: {e}")
            return False
    
    def copy_file(self, filename: str, new_filename: str) -> bool:
        """
        Copy a database file
        
        Args:
            filename: Source filename
            new_filename: Destination filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import shutil
            
            src_path = os.path.join(self.folder_path, filename)
            dst_path = os.path.join(self.folder_path, new_filename)
            
            if not os.path.exists(src_path):
                print(f"❌ Source file '{filename}' not found")
                return False
            
            shutil.copy2(src_path, dst_path)
            print(f"✓ File copied from '{filename}' to '{new_filename}'")
            return True
            
        except Exception as e:
            print(f"❌ Error copying file: {e}")
            return False
    
    def get_folder_size(self) -> int:
        """
        Get total size of all files in the database folder
        
        Returns:
            Total size in bytes
        """
        try:
            total_size = 0
            for filename in os.listdir(self.folder_path):
                file_path = os.path.join(self.folder_path, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
            
            print(f"📊 Total folder size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
            return total_size
            
        except Exception as e:
            print(f"❌ Error calculating folder size: {e}")
            return 0

# Convenience functions for easy usage
def save_warehouse_db(db: DATABASE, filename: str = None, format: str = 'json', folder_path: str = folder_path) -> bool:
    """
    Quick save function for warehouse database
    
    Args:
        db: DATABASE object to save
        filename: Optional filename
        format: 'json' or 'binary' (default: 'json')
        folder_path: Local folder path (default: folder_path)
        
    Returns:
        bool: True if successful, False otherwise
    """
    colab_db = ColabWarehouseDB(folder_path)
    
    if format.lower() == 'binary':
        return colab_db.save_database_binary(db, filename)
    else:
        return colab_db.save_database_json(db, filename)

def load_warehouse_db(filename: str, format: str = 'json', folder_path: str = "/content/drive/WarehouseDB") -> Optional[DATABASE]:
    """
    Quick load function for warehouse database
    
    Args:
        filename: Name of the file to load
        format: 'json' or 'binary' (default: 'json')
        folder_path: Local folder path (default: '/content/drive/WarehouseDB')
        
    Returns:
        DATABASE object if successful, None otherwise
    """
    colab_db = ColabWarehouseDB(folder_path)
    
    if format.lower() == 'binary':
        return colab_db.load_database_binary(filename)
    else:
        return colab_db.load_database_json(filename)

def list_warehouse_files(folder_path: str = "/content/WarehouseDB") -> List[Dict[str, Any]]:
    """
    Quick function to list warehouse database files
    
    Args:
        folder_path: Local folder path (default: '/content/WarehouseDB')
        
    Returns:
        List of file information dictionaries
    """
    colab_db = ColabWarehouseDB(folder_path)
    return colab_db.list_database_files()

def cleanup_old_files(folder_path: str = folder_path, keep_latest: int = 5) -> bool:
    """
    Clean up old database files, keeping only the most recent ones
    
    Args:
        folder_path: Local folder path (default: folder_path)
        keep_latest: Number of most recent files to keep (default: 5)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        colab_db = ColabWarehouseDB(folder_path)
        files_info = colab_db.list_database_files()
        
        if len(files_info) <= keep_latest:
            print(f"✓ Only {len(files_info)} files found, no cleanup needed")
            return True
        
        # Sort by modification time (newest first)
        files_info.sort(key=lambda x: x['modified'], reverse=True)
        
        # Delete old files
        deleted_count = 0
        for file_info in files_info[keep_latest:]:
            if colab_db.delete_database_file(file_info['name']):
                deleted_count += 1
        
        print(f"✓ Cleaned up {deleted_count} old files, kept {keep_latest} most recent")
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

# Example usage functions
def demo_save_load():
    """Demonstration of save/load functionality"""
    print("🚀 Warehouse Database Colab Local Storage Demo")
    print("=" * 60)
    
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
    
    # Save database in both formats
    print("\n💾 Saving database...")
    json_success = save_warehouse_db(db, format='json')
    binary_success = save_warehouse_db(db, format='binary')
    
    if json_success or binary_success:
        print("\n📋 Listing files...")
        files = list_warehouse_files()
        
        if files:
            # Try loading the most recent JSON file
            json_files = [f for f in files if f['name'].endswith('.json')]
            if json_files:
                latest_json = sorted(json_files, key=lambda x: x['modified'])[-1]
                print(f"\n📖 Loading database from {latest_json['name']}...")
                loaded_db = load_warehouse_db(latest_json['name'])
                
                if loaded_db:
                    print(f"✓ Loaded database with {loaded_db.maxproduct} products")
                else:
                    print("❌ Failed to load database")
        
        # Show folder size
        print("\n📊 Storage information:")
        colab_db = ColabWarehouseDB()
        colab_db.get_folder_size()
        
    else:
        print("❌ Failed to save database")

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
    
    print(f"🔄 Creating backup '{backup_name}'...")
    
    # Save in both formats
    json_success = save_warehouse_db(db, f"{backup_name}.json", format='json')
    binary_success = save_warehouse_db(db, f"{backup_name}.pkl", format='binary')
    
    if json_success and binary_success:
        print(f"✓ Backup '{backup_name}' created successfully")
        return True
    else:
        print(f"⚠️  Backup '{backup_name}' partially created")
        return False

if __name__ == "__main__":
    # Run demo if script is executed directly
    demo_save_load()