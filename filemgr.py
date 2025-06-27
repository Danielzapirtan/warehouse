import json
import pickle
from datetime import datetime
from typing import Dict, Any, Optional
import os
from google.colab import auth, drive
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError
import io

# Import your warehouse classes
from warehouse import DATABASE, PRODUCT, SHEET, PAGE, RECORD

class GoogleDriveWarehouseDB:
    """
    Google Drive integration for warehouse database with JSON and binary formats
    Designed for Google Colab environment
    """
    
    def __init__(self, folder_name: str = "WarehouseDB"):
        """
        Initialize Google Drive connection
        
        Args:
            folder_name: Name of the folder in Google Drive to store database files
        """
        self.folder_name = folder_name
        self.service = None
        self.folder_id = None
        self._authenticate()
        
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            # Authenticate and create the Drive API service
            auth.authenticate_user()
            self.service = build('drive', 'v3')
            print("✓ Successfully authenticated with Google Drive")
            
            # Create or find the database folder
            self._setup_folder()
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            raise
    
    def _setup_folder(self):
        """Create or find the database folder in Google Drive"""
        try:
            # Search for existing folder
            results = self.service.files().list(
                q=f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                self.folder_id = folders[0]['id']
                print(f"✓ Found existing folder '{self.folder_name}'")
            else:
                # Create new folder
                folder_metadata = {
                    'name': self.folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=folder_metadata).execute()
                self.folder_id = folder.get('id')
                print(f"✓ Created new folder '{self.folder_name}'")
                
        except HttpError as e:
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
        Save database to Google Drive as JSON file
        
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
            
            # Convert database to dictionary
            db_dict = self._database_to_dict(db)
            
            # Create JSON string
            json_content = json.dumps(db_dict, indent=2, ensure_ascii=False)
            
            # Create temporary file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_content)
            
            # Upload to Google Drive
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }
            
            media = MediaFileUpload(filename, mimetype='application/json')
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            # Clean up temporary file
            os.remove(filename)
            
            print(f"✓ Database saved to Google Drive as '{filename}'")
            print(f"  File ID: {file.get('id')}")
            print(f"  Products: {db.maxproduct}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving database: {e}")
            return False
    
    def save_database_binary(self, db: DATABASE, filename: str = None) -> bool:
        """
        Save database to Google Drive as binary pickle file
        
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
            
            # Save as pickle file
            with open(filename, 'wb') as f:
                pickle.dump(db, f)
            
            # Upload to Google Drive
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }
            
            media = MediaFileUpload(filename, mimetype='application/octet-stream')
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            # Clean up temporary file
            os.remove(filename)
            
            print(f"✓ Database saved to Google Drive as '{filename}' (binary)")
            print(f"  File ID: {file.get('id')}")
            print(f"  Products: {db.maxproduct}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving database (binary): {e}")
            return False
    
    def load_database_json(self, filename: str) -> Optional[DATABASE]:
        """
        Load database from Google Drive JSON file
        
        Args:
            filename: Name of the JSON file to load
            
        Returns:
            DATABASE object if successful, None otherwise
        """
        try:
            # Find file in Google Drive
            results = self.service.files().list(
                q=f"name='{filename}' and parents in '{self.folder_id}'",
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                print(f"❌ File '{filename}' not found in Google Drive")
                return None
            
            file_id = files[0]['id']
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Parse JSON content
            file_content.seek(0)
            json_content = file_content.read().decode('utf-8')
            db_dict = json.loads(json_content)
            
            # Convert to DATABASE object
            db = self._dict_to_database(db_dict)
            
            metadata = db_dict.get('metadata', {})
            print(f"✓ Database loaded from '{filename}'")
            print(f"  Created: {metadata.get('created_at', 'Unknown')}")
            print(f"  Version: {metadata.get('version', 'Unknown')}")
            print(f"  Products: {db.maxproduct}")
            
            return db
            
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            return None
    
    def load_database_binary(self, filename: str) -> Optional[DATABASE]:
        """
        Load database from Google Drive binary pickle file
        
        Args:
            filename: Name of the pickle file to load
            
        Returns:
            DATABASE object if successful, None otherwise
        """
        try:
            # Find file in Google Drive
            results = self.service.files().list(
                q=f"name='{filename}' and parents in '{self.folder_id}'",
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                print(f"❌ File '{filename}' not found in Google Drive")
                return None
            
            file_id = files[0]['id']
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Load pickle content
            file_content.seek(0)
            db = pickle.load(file_content)
            
            print(f"✓ Database loaded from '{filename}' (binary)")
            print(f"  Products: {db.maxproduct}")
            
            return db
            
        except Exception as e:
            print(f"❌ Error loading database (binary): {e}")
            return None
    
    def list_database_files(self) -> list:
        """
        List all database files in the Google Drive folder
        
        Returns:
            List of file information dictionaries
        """
        try:
            results = self.service.files().list(
                q=f"parents in '{self.folder_id}'",
                fields="files(id, name, createdTime, size)"
            ).execute()
            
            files = results.get('files', [])
            
            print(f"📁 Files in '{self.folder_name}' folder:")
            print("-" * 60)
            
            for file in files:
                size = int(file.get('size', 0))
                size_str = f"{size:,} bytes" if size > 0 else "Unknown size"
                created = file.get('createdTime', 'Unknown')[:19].replace('T', ' ')
                
                print(f"📄 {file['name']}")
                print(f"   Created: {created}")
                print(f"   Size: {size_str}")
                print(f"   ID: {file['id']}")
                print()
            
            return files
            
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []
    
    def delete_database_file(self, filename: str) -> bool:
        """
        Delete a database file from Google Drive
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find file in Google Drive
            results = self.service.files().list(
                q=f"name='{filename}' and parents in '{self.folder_id}'",
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                print(f"❌ File '{filename}' not found in Google Drive")
                return False
            
            file_id = files[0]['id']
            
            # Delete file
            self.service.files().delete(fileId=file_id).execute()
            
            print(f"✓ File '{filename}' deleted from Google Drive")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting file: {e}")
            return False

# Convenience functions for easy usage
def save_warehouse_db(db: DATABASE, filename: str = None, format: str = 'json', folder_name: str = "WarehouseDB") -> bool:
    """
    Quick save function for warehouse database
    
    Args:
        db: DATABASE object to save
        filename: Optional filename
        format: 'json' or 'binary' (default: 'json')
        folder_name: Google Drive folder name (default: 'WarehouseDB')
        
    Returns:
        bool: True if successful, False otherwise
    """
    gdrive_db = GoogleDriveWarehouseDB(folder_name)
    
    if format.lower() == 'binary':
        return gdrive_db.save_database_binary(db, filename)
    else:
        return gdrive_db.save_database_json(db, filename)

def load_warehouse_db(filename: str, format: str = 'json', folder_name: str = "WarehouseDB") -> Optional[DATABASE]:
    """
    Quick load function for warehouse database
    
    Args:
        filename: Name of the file to load
        format: 'json' or 'binary' (default: 'json')
        folder_name: Google Drive folder name (default: 'WarehouseDB')
        
    Returns:
        DATABASE object if successful, None otherwise
    """
    gdrive_db = GoogleDriveWarehouseDB(folder_name)
    
    if format.lower() == 'binary':
        return gdrive_db.load_database_binary(filename)
    else:
        return gdrive_db.load_database_json(filename)

def list_warehouse_files(folder_name: str = "WarehouseDB") -> list:
    """
    Quick function to list warehouse database files
    
    Args:
        folder_name: Google Drive folder name (default: 'WarehouseDB')
        
    Returns:
        List of file information dictionaries
    """
    gdrive_db = GoogleDriveWarehouseDB(folder_name)
    return gdrive_db.list_database_files()

# Example usage functions
def demo_save_load():
    """Demonstration of save/load functionality"""
    print("🚀 Warehouse Database Google Drive Demo")
    print("=" * 50)
    
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
    print("\n💾 Saving database...")
    success = save_warehouse_db(db, format='json')
    
    if success:
        print("\n📋 Listing files...")
        list_warehouse_files()
        
        print("\n📖 Loading database...")
        loaded_db = load_warehouse_db("warehouse_db_20250627_120000.json")  # Use actual filename
        
        if loaded_db:
            print(f"✓ Loaded database with {loaded_db.maxproduct} products")
        else:
            print("❌ Failed to load database")
    else:
        print("❌ Failed to save database")

if __name__ == "__main__":
    # Run demo if script is executed directly
    demo_save_load()