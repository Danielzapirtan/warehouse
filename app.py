import gradio as gr
import pandas as pd
from typing import List, Tuple, Optional
from datetime import datetime
import json

# Import your warehouse module
from warehouse import DATABASE, PRODUCT, SHEET, PAGE, RECORD, db

class WarehouseUI:
    def __init__(self, database: DATABASE):
        self.db = database
        
    def get_products_list(self) -> List[str]:
        """Get list of product names for dropdown"""
        if not self.db.products:
            return ["No products available"]
        return [f"{i}: {product.name} ({product.unit})" for i, product in enumerate(self.db.products)]
    
    def get_sheets_list(self, product_idx: int) -> List[str]:
        """Get list of sheets for selected product"""
        if product_idx < 0 or product_idx >= len(self.db.products):
            return ["No sheets available"]
        product = self.db.products[product_idx]
        if not product.sheets:
            return ["No sheets available"]
        return [f"{i}: {sheet.year}-{sheet.month:02d}" for i, sheet in enumerate(product.sheets)]
    
    def get_pages_list(self, product_idx: int, sheet_idx: int) -> List[str]:
        """Get list of pages for selected sheet"""
        if (product_idx < 0 or product_idx >= len(self.db.products) or 
            sheet_idx < 0 or sheet_idx >= len(self.db.products[product_idx].sheets)):
            return ["No pages available"]
        sheet = self.db.products[product_idx].sheets[sheet_idx]
        if not sheet.pages:
            return ["No pages available"]
        return [f"{i}: Price ${page.price:.2f}, Init: {page.sold_init:.2f}" 
                for i, page in enumerate(sheet.pages)]
    
    def get_records_list(self, product_idx: int, sheet_idx: int, page_idx: int) -> List[str]:
        """Get list of records for selected page"""
        try:
            page = self.db.products[product_idx].sheets[sheet_idx].pages[page_idx]
            if not page.records:
                return ["No records available"]
            return [f"{i}: {record.doc_id} ({record.doc_type}) - Final: {record.sold_final:.2f}" 
                    for i, record in enumerate(page.records)]
        except (IndexError, AttributeError):
            return ["No records available"]

    # PRODUCT CRUD OPERATIONS
    def create_product(self, name: str, unit: str) -> Tuple[str, str]:
        """Create a new product"""
        if not name.strip():
            return "Error: Product name cannot be empty", self.get_products_dropdown()
        
        product = self.db.create_product(name.strip(), unit.strip())
        return f"✅ Created product: {product.name} ({product.unit})", gr.Dropdown(choices=self.get_products_list())
    
    def update_product(self, product_idx: int, name: str, unit: str) -> str:
        """Update existing product"""
        if product_idx < 0 or product_idx >= len(self.db.products):
            return "Error: Invalid product selection"
        
        if not name.strip():
            return "Error: Product name cannot be empty"
        
        product = self.db.products[product_idx]
        product.name = name.strip()
        product.unit = unit.strip()
        return f"✅ Updated product: {product.name} ({product.unit})"
    
    def delete_product(self, product_idx: int) -> Tuple[str, str]:
        """Delete product"""
        if product_idx < 0 or product_idx >= len(self.db.products):
            return "Error: Invalid product selection", self.get_products_dropdown()
        
        product = self.db.products.pop(product_idx)
        self.db.maxproduct -= 1
        if self.db.crtproduct >= self.db.maxproduct:
            self.db.crtproduct = max(0, self.db.maxproduct - 1)
        
        return f"🗑️ Deleted product: {product.name}", gr.Dropdown(choices=self.get_products_list())

    # SHEET CRUD OPERATIONS
    def create_sheet(self, product_idx: int, year: int, month: int) -> str:
        """Create a new sheet"""
        if product_idx < 0 or product_idx >= len(self.db.products):
            return "Error: Invalid product selection"
        
        if not (1 <= month <= 12):
            return "Error: Month must be between 1 and 12"
        
        product = self.db.products[product_idx]
        sheet = product.create_sheet(year, month)
        return f"✅ Created sheet: {sheet.year}-{sheet.month:02d} for {product.name}"
    
    def delete_sheet(self, product_idx: int, sheet_idx: int) -> str:
        """Delete sheet"""
        try:
            product = self.db.products[product_idx]
            sheet = product.sheets.pop(sheet_idx)
            product.maxsheet -= 1
            if product.crtsheet >= product.maxsheet:
                product.crtsheet = max(0, product.maxsheet - 1)
            return f"🗑️ Deleted sheet: {sheet.year}-{sheet.month:02d}"
        except (IndexError, AttributeError):
            return "Error: Invalid selection"

    # PAGE CRUD OPERATIONS
    def create_page(self, product_idx: int, sheet_idx: int, price: float, sold_init: float) -> str:
        """Create a new page"""
        try:
            sheet = self.db.products[product_idx].sheets[sheet_idx]
            page = sheet.create_page(price, sold_init)
            return f"✅ Created page: Price ${page.price:.2f}, Initial stock: {page.sold_init:.2f}"
        except (IndexError, AttributeError):
            return "Error: Invalid selection"
    
    def delete_page(self, product_idx: int, sheet_idx: int, page_idx: int) -> str:
        """Delete page"""
        try:
            sheet = self.db.products[product_idx].sheets[sheet_idx]
            page = sheet.pages.pop(page_idx)
            sheet.maxpage -= 1
            if sheet.crtpage >= sheet.maxpage:
                sheet.crtpage = max(0, sheet.maxpage - 1)
            return f"🗑️ Deleted page: Price ${page.price:.2f}"
        except (IndexError, AttributeError):
            return "Error: Invalid selection"

    # RECORD CRUD OPERATIONS
    def create_record(self, product_idx: int, sheet_idx: int, page_idx: int, 
                     input_val: float, output_val: float, doc_id: str, doc_type: str, dom: int) -> str:
        """Create a new record"""
        try:
            page = self.db.products[product_idx].sheets[sheet_idx].pages[page_idx]
            if not doc_id.strip():
                return "Error: Document ID cannot be empty"
            
            # Removed sold_init parameter (3rd argument) from create_record call
            record = page.create_record(input_val, output_val, doc_id.strip(), doc_type.strip(), dom)
            return f"✅ Created record: {record.doc_id} - Final stock: {record.sold_final:.2f}"
        except (IndexError, AttributeError):
            return "Error: Invalid selection"

    def update_record(self, product_idx: int, sheet_idx: int, page_idx: int, record_idx: int,
                     input_val: float, output_val: float, doc_id: str, doc_type: str, dom: int) -> str:
        """Update existing record"""
        try:
            record = self.db.products[product_idx].sheets[sheet_idx].pages[page_idx].records[record_idx]
            if not doc_id.strip():
                return "Error: Document ID cannot be empty"
            
            record.input = float(input_val)
            record.output = float(output_val)
            record.doc_id = doc_id.strip()
            record.doc_type = doc_type.strip()
            record.dom = int(dom)
            # Recalculate sold_final
            record.sold_final = record.sold_init + record.input - record.output
            
            return f"✅ Updated record: {record.doc_id} - Final stock: {record.sold_final:.2f}"
        except (IndexError, AttributeError):
            return "Error: Invalid selection"
    
    def delete_record(self, product_idx: int, sheet_idx: int, page_idx: int, record_idx: int) -> str:
        """Delete record"""
        try:
            page = self.db.products[product_idx].sheets[sheet_idx].pages[page_idx]
            record = page.records.pop(record_idx)
            page.maxrecord -= 1
            if page.crtrecord >= page.maxrecord:
                page.crtrecord = max(0, page.maxrecord - 1)
            return f"🗑️ Deleted record: {record.doc_id}"
        except (IndexError, AttributeError):
            return "Error: Invalid selection"

    def get_database_summary(self) -> str:
        """Get database summary"""
        summary = f"📊 **Database Summary**\n\n"
        summary += f"**Total Products:** {len(self.db.products)}\n\n"
        
        for i, product in enumerate(self.db.products):
            summary += f"**{i+1}. {product.name}** ({product.unit})\n"
            summary += f"   - Sheets: {len(product.sheets)}\n"
            
            total_pages = sum(len(sheet.pages) for sheet in product.sheets)
            total_records = sum(len(page.records) for sheet in product.sheets for page in sheet.pages)
            
            summary += f"   - Pages: {total_pages}\n"
            summary += f"   - Records: {total_records}\n\n"
        
        return summary if self.db.products else "No products in database"

    def export_to_dataframe(self, product_idx: int) -> pd.DataFrame:
        """Export product data to pandas DataFrame"""
        if product_idx < 0 or product_idx >= len(self.db.products):
            return pd.DataFrame()
        
        product = self.db.products[product_idx]
        data = []
        
        for sheet in product.sheets:
            for page in sheet.pages:
                for record in page.records:
                    data.append({
                        'Product': product.name,
                        'Unit': product.unit,
                        'Year': sheet.year,
                        'Month': sheet.month,
                        'Price': page.price,
                        'Page_Init_Stock': page.sold_init,
                        'Doc_ID': record.doc_id,
                        'Doc_Type': record.doc_type,
                        'DOM': record.dom,
                        'Input': record.input,
                        'Output': record.output,
                        'Initial_Stock': record.sold_init,
                        'Final_Stock': record.sold_final
                    })
        
        return pd.DataFrame(data)

# Initialize UI
warehouse_ui = WarehouseUI(db)

def create_interface():
    """Create the Gradio interface"""
    
    with gr.Blocks(title="🏭 Warehouse Management System", theme=gr.themes.Soft()) as app:
        gr.HTML("<h1 style='text-align: center; color: #2E8B57;'>🏭 Warehouse Management System</h1>")
        
        with gr.Tabs():
            # PRODUCTS TAB
            with gr.TabItem("📦 Products"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML("<h3>Create Product</h3>")
                        product_name = gr.Textbox(label="Product Name", placeholder="Enter product name")
                        product_unit = gr.Textbox(label="Unit", placeholder="kg, pieces, liters, etc.")
                        create_product_btn = gr.Button("➕ Create Product", variant="primary")
                        
                        gr.HTML("<h3>Manage Products</h3>")
                        products_dropdown = gr.Dropdown(
                            label="Select Product",
                            choices=warehouse_ui.get_products_list(),
                            value=0 if warehouse_ui.get_products_list()[0] != "No products available" else None
                        )
                        
                        update_name = gr.Textbox(label="New Name")
                        update_unit = gr.Textbox(label="New Unit")
                        
                        with gr.Row():
                            update_product_btn = gr.Button("✏️ Update", variant="secondary")
                            delete_product_btn = gr.Button("🗑️ Delete", variant="stop")
                    
                    with gr.Column(scale=1):
                        product_status = gr.Textbox(label="Status", interactive=False)
                        db_summary = gr.Markdown(warehouse_ui.get_database_summary())
                
                # Event handlers for products
                create_product_btn.click(
                    warehouse_ui.create_product,
                    inputs=[product_name, product_unit],
                    outputs=[product_status, products_dropdown]
                ).then(
                    lambda: warehouse_ui.get_database_summary(),
                    outputs=[db_summary]
                )
                
                def get_product_idx(selection):
                    if not selection or "No products" in selection:
                        return -1
                    return int(selection.split(":")[0])
                
                update_product_btn.click(
                    lambda sel, name, unit: warehouse_ui.update_product(get_product_idx(sel), name, unit),
                    inputs=[products_dropdown, update_name, update_unit],
                    outputs=[product_status]
                )
                
                delete_product_btn.click(
                    lambda sel: warehouse_ui.delete_product(get_product_idx(sel)),
                    inputs=[products_dropdown],
                    outputs=[product_status, products_dropdown]
                ).then(
                    lambda: warehouse_ui.get_database_summary(),
                    outputs=[db_summary]
                )

            # SHEETS TAB
            with gr.TabItem("📋 Sheets"):
                with gr.Row():
                    with gr.Column():
                        products_for_sheets = gr.Dropdown(
                            label="Select Product",
                            choices=warehouse_ui.get_products_list()
                        )
                        
                        gr.HTML("<h3>Create Sheet</h3>")
                        sheet_year = gr.Number(label="Year", value=2025, precision=0)
                        sheet_month = gr.Number(label="Month", value=1, precision=0, minimum=1, maximum=12)
                        create_sheet_btn = gr.Button("➕ Create Sheet", variant="primary")
                        
                        gr.HTML("<h3>Manage Sheets</h3>")
                        sheets_dropdown = gr.Dropdown(label="Select Sheet", choices=["Select product first"])
                        delete_sheet_btn = gr.Button("🗑️ Delete Sheet", variant="stop")
                    
                    with gr.Column():
                        sheet_status = gr.Textbox(label="Status", interactive=False)
                
                # Update sheets dropdown when product changes
                products_for_sheets.change(
                    lambda sel: gr.Dropdown(choices=warehouse_ui.get_sheets_list(get_product_idx(sel))),
                    inputs=[products_for_sheets],
                    outputs=[sheets_dropdown]
                )
                
                create_sheet_btn.click(
                    lambda sel, year, month: warehouse_ui.create_sheet(get_product_idx(sel), int(year), int(month)),
                    inputs=[products_for_sheets, sheet_year, sheet_month],
                    outputs=[sheet_status]
                ).then(
                    lambda sel: gr.Dropdown(choices=warehouse_ui.get_sheets_list(get_product_idx(sel))),
                    inputs=[products_for_sheets],
                    outputs=[sheets_dropdown]
                )
                
                def get_sheet_idx(selection):
                    if not selection or "No sheets" in selection:
                        return -1
                    return int(selection.split(":")[0])
                
                delete_sheet_btn.click(
                    lambda prod_sel, sheet_sel: warehouse_ui.delete_sheet(get_product_idx(prod_sel), get_sheet_idx(sheet_sel)),
                    inputs=[products_for_sheets, sheets_dropdown],
                    outputs=[sheet_status]
                )

            # PAGES TAB
            with gr.TabItem("📄 Pages"):
                with gr.Row():
                    with gr.Column():
                        products_for_pages = gr.Dropdown(label="Select Product", choices=warehouse_ui.get_products_list())
                        sheets_for_pages = gr.Dropdown(label="Select Sheet", choices=["Select product first"])
                        
                        gr.HTML("<h3>Create Page</h3>")
                        page_price = gr.Number(label="Price", value=0.0, step=0.01)
                        page_sold_init = gr.Number(label="Initial Stock", value=0.0, step=0.01)
                        create_page_btn = gr.Button("➕ Create Page", variant="primary")
                        
                        gr.HTML("<h3>Manage Pages</h3>")
                        pages_dropdown = gr.Dropdown(label="Select Page", choices=["Select sheet first"])
                        delete_page_btn = gr.Button("🗑️ Delete Page", variant="stop")
                    
                    with gr.Column():
                        page_status = gr.Textbox(label="Status", interactive=False)
                
                # Update dropdowns
                products_for_pages.change(
                    lambda sel: gr.Dropdown(choices=warehouse_ui.get_sheets_list(get_product_idx(sel))),
                    inputs=[products_for_pages],
                    outputs=[sheets_for_pages]
                )
                
                sheets_for_pages.change(
                    lambda prod_sel, sheet_sel: gr.Dropdown(choices=warehouse_ui.get_pages_list(get_product_idx(prod_sel), get_sheet_idx(sheet_sel))),
                    inputs=[products_for_pages, sheets_for_pages],
                    outputs=[pages_dropdown]
                )
                
                def get_page_idx(selection):
                    if not selection or "No pages" in selection:
                        return -1
                    return int(selection.split(":")[0])
                
                create_page_btn.click(
                    lambda prod_sel, sheet_sel, price, init: warehouse_ui.create_page(
                        get_product_idx(prod_sel), get_sheet_idx(sheet_sel), price, init
                    ),
                    inputs=[products_for_pages, sheets_for_pages, page_price, page_sold_init],
                    outputs=[page_status]
                )
                
                delete_page_btn.click(
                    lambda prod_sel, sheet_sel, page_sel: warehouse_ui.delete_page(
                        get_product_idx(prod_sel), get_sheet_idx(sheet_sel), get_page_idx(page_sel)
                    ),
                    inputs=[products_for_pages, sheets_for_pages, pages_dropdown],
                    outputs=[page_status]
                )

            # RECORDS TAB
            with gr.TabItem("📝 Records"):
                with gr.Row():
                    with gr.Column():
                        products_for_records = gr.Dropdown(label="Select Product", choices=warehouse_ui.get_products_list())
                        sheets_for_records = gr.Dropdown(label="Select Sheet", choices=["Select product first"])
                        pages_for_records = gr.Dropdown(label="Select Page", choices=["Select sheet first"])
                        
                        gr.HTML("<h3>Create/Update Record</h3>")
                        record_input = gr.Number(label="Input", value=0.0, step=0.01)
                        record_output = gr.Number(label="Output", value=0.0, step=0.01)
                        record_doc_id = gr.Textbox(label="Document ID", placeholder="Enter document ID")
                        record_doc_type = gr.Textbox(label="Document Type", placeholder="e.g., Invoice, Receipt")
                        record_dom = gr.Number(label="DOM (Day of Month)", value=1, precision=0, minimum=1, maximum=31)
                        
                        with gr.Row():
                            create_record_btn = gr.Button("➕ Create Record", variant="primary")
                            update_record_btn = gr.Button("✏️ Update Record", variant="secondary")
                        
                        gr.HTML("<h3>Manage Records</h3>")
                        records_dropdown = gr.Dropdown(label="Select Record", choices=["Select page first"])
                        delete_record_btn = gr.Button("🗑️ Delete Record", variant="stop")
                    
                    with gr.Column():
                        record_status = gr.Textbox(label="Status", interactive=False)
                
                # Update dropdowns for records
                products_for_records.change(
                    lambda sel: gr.Dropdown(choices=warehouse_ui.get_sheets_list(get_product_idx(sel))),
                    inputs=[products_for_records],
                    outputs=[sheets_for_records]
                )
                
                sheets_for_records.change(
                    lambda prod_sel, sheet_sel: gr.Dropdown(choices=warehouse_ui.get_pages_list(get_product_idx(prod_sel), get_sheet_idx(sheet_sel))),
                    inputs=[products_for_records, sheets_for_records],
                    outputs=[pages_for_records]
                )
                
                pages_for_records.change(
                    lambda prod_sel, sheet_sel, page_sel: gr.Dropdown(choices=warehouse_ui.get_records_list(
                        get_product_idx(prod_sel), get_sheet_idx(sheet_sel), get_page_idx(page_sel)
                    )),
                    inputs=[products_for_records, sheets_for_records, pages_for_records],
                    outputs=[records_dropdown]
                )
                
                def get_record_idx(selection):
                    if not selection or "No records" in selection:
                        return -1
                    return int(selection.split(":")[0])
                
                create_record_btn.click(
                    lambda prod_sel, sheet_sel, page_sel, inp, out, doc_id, doc_type, dom: warehouse_ui.create_record(
                        get_product_idx(prod_sel), get_sheet_idx(sheet_sel), get_page_idx(page_sel),
                        inp, out, doc_id, doc_type, dom
                    ),
                    inputs=[products_for_records, sheets_for_records, pages_for_records, 
                           record_input, record_output, record_doc_id, record_doc_type, record_dom],
                    outputs=[record_status]
                )
                
                update_record_btn.click(
                    lambda prod_sel, sheet_sel, page_sel, rec_sel, inp, out, doc_id, doc_type, dom: warehouse_ui.update_record(
                        get_product_idx(prod_sel), get_sheet_idx(sheet_sel), get_page_idx(page_sel), get_record_idx(rec_sel),
                        inp, out, doc_id, doc_type, dom
                    ),
                    inputs=[products_for_records, sheets_for_records, pages_for_records, records_dropdown,
                           record_input, record_output, record_doc_id, record_doc_type, record_dom],
                    outputs=[record_status]
                )
                
                delete_record_btn.click(
                    lambda prod_sel, sheet_sel, page_sel, rec_sel: warehouse_ui.delete_record(
                        get_product_idx(prod_sel), get_sheet_idx(sheet_sel), get_page_idx(page_sel), get_record_idx(rec_sel)
                    ),
                    inputs=[products_for_records, sheets_for_records, pages_for_records, records_dropdown],
                    outputs=[record_status]
                )

            # DATA EXPORT TAB
            with gr.TabItem("📊 Data Export"):
                with gr.Row():
                    with gr.Column():
                        products_for_export = gr.Dropdown(label="Select Product to Export", choices=warehouse_ui.get_products_list())
                        export_btn = gr.Button("📥 Export to DataFrame", variant="primary")
                    
                    with gr.Column():
                        export_data = gr.Dataframe(label="Exported Data", interactive=False)
                
                export_btn.click(
                    lambda sel: warehouse_ui.export_to_dataframe(get_product_idx(sel)),
                    inputs=[products_for_export],
                    outputs=[export_data]
                )

        gr.HTML("""
        <div style='text-align: center; margin-top: 20px; color: #666;'>
            <p>🏭 Warehouse Management System | Built with Gradio</p>
            <p>Features: Full CRUD operations, Real-time updates, Data export capabilities</p>
        </div>
        """)
    
    return app

# Function to launch the app
def launch_app(share=False, debug=False):
    """Launch the Warehouse Management UI"""
    app = create_interface()
    app.launch(share=share, debug=debug, height=800)
    return app

# For Colab usage
if __name__ == "__main__":
    # Create some sample data for demonstration
    product1 = db.create_product("Apples", "kg")
    sheet1 = product1.create_sheet(2025, 6)
    page1 = sheet1.create_page(2.50, 100.0)
    page1.create_record(50.0, 20.0, 100.0, "INV001", "Purchase Invoice", 15)
    page1.create_record(30.0, 40.0, 130.0, "INV002", "Sale Invoice", 20)
    
    product2 = db.create_product("Oranges", "kg")
    sheet2 = product2.create_sheet(2025, 6)
    page2 = sheet2.create_page(3.00, 80.0)
    page2.create_record(25.0, 15.0, 80.0, "INV003", "Purchase Invoice", 10)
    
    print("🏭 Warehouse Management System")
    print("================================")
    print("Sample data created!")
    print(f"Products: {len(db.products)}")
    print("Ready to launch UI...")
    print("\nTo launch the interface, call: launch_app(share=True)")