"""
Warehouse Management System UI built with Gradio.

This module provides a graphical interface for managing warehouse inventory data,
including products, sheets, pages, and records with full CRUD operations.
"""

import gradio as gr
import pandas as pd
from typing import List, Tuple, Optional
from datetime import datetime
import json

# Import your warehouse module
from warehouse import DATABASE, PRODUCT, SHEET, PAGE, RECORD, db
from colabfm import save_warehouse_db, load_warehouse_db


class WarehouseUI:
    """User interface for warehouse management system."""

    def __init__(self, database: DATABASE) -> None:
        """Initialize the UI with a database instance.
        
        Args:
            database: The warehouse database to manage
        """
        self.db = database
        # Set up observer to refresh UI when data changes
        self.db.add_observer(self._on_database_change)

    def _on_database_change(self, event_type: str, data) -> None:
        """Handle database changes - could be used for real-time UI updates.
        
        Args:
            event_type: Type of database change event
            data: Data associated with the change
        """
        # For now, we'll handle updates through return values
        save_warehouse_db(self.db, filename="db.json", format="json")

    def get_products_list(self) -> List[str]:
        """Get list of product names for dropdown.
        
        Returns:
            List of formatted product strings or ["No products available"] if empty
        """
        if not self.db.products:
            return ["No products available"]
        return [
            f"{i}: {product.name} ({product.unit})"
            for i, product in enumerate(self.db.products)
        ]

    def get_sheets_list(self, product_idx: int) -> List[str]:
        """Get list of sheets for selected product.
        
        Args:
            product_idx: Index of the selected product
            
        Returns:
            List of formatted sheet strings or ["No sheets available"] if invalid
        """
        if product_idx < 0 or product_idx >= len(self.db.products):
            return ["No sheets available"]
        product = self.db.products[product_idx]
        if not product.sheets:
            return ["No sheets available"]
        return [
            f"{i}: {sheet.year}-{sheet.month:02d}"
            for i, sheet in enumerate(product.sheets)
        ]

    def get_pages_list(self, product_idx: int, sheet_idx: int) -> List[str]:
        """Get list of pages for selected sheet.
        
        Args:
            product_idx: Index of the selected product
            sheet_idx: Index of the selected sheet
            
        Returns:
            List of formatted page strings or ["No pages available"] if invalid
        """
        if (product_idx < 0 or product_idx >= len(self.db.products) or
                sheet_idx < 0 or sheet_idx >= len(self.db.products[product_idx].sheets)):
            return ["No pages available"]
        sheet = self.db.products[product_idx].sheets[sheet_idx]
        if not sheet.pages:
            return ["No pages available"]
        return [
            f"{i}: Price ${page.price:.2f}, Init: {page.sold_init:.2f}, Final: {page.sold_final:.2f}"
            for i, page in enumerate(sheet.pages)
        ]

    def get_records_list(self, product_idx: int, sheet_idx: int, page_idx: int) -> List[str]:
        """Get list of records for selected page.
        
        Args:
            product_idx: Index of the selected product
            sheet_idx: Index of the selected sheet
            page_idx: Index of the selected page
            
        Returns:
            List of formatted record strings or ["No records available"] if invalid
        """
        try:
            page = self.db.products[product_idx].sheets[sheet_idx].pages[page_idx]
            if not page.records:
                return ["No records available"]
            return [
                f"{i}: {record.doc_id} ({record.doc_type}) - "
                f"In:{record.input}, Out:{record.output}, Final:{record.sold_final:.2f}"
                for i, record in enumerate(page.records)
            ]
        except (IndexError, AttributeError):
            return ["No records available"]

    # PRODUCT CRUD OPERATIONS
    def create_product(self, name: str, unit: str) -> Tuple[str, gr.Dropdown, str]:
        """Create a new product.
        
        Args:
            name: Name of the new product
            unit: Unit of measurement for the product
            
        Returns:
            Tuple containing:
                - Status message
                - Updated products dropdown
                - Database summary
        """
        if not name.strip():
            return (
                "Error: Product name cannot be empty",
                gr.Dropdown(choices=self.get_products_list()),
                self.get_database_summary()
            )

        product = self.db.create_product(name.strip(), unit.strip())
        return (
            f"✅ Created product: {product.name} ({product.unit})",
            gr.Dropdown(choices=self.get_products_list()),
            self.get_database_summary()
        )

    def update_product(self, product_idx: int, name: str, unit: str) -> Tuple[str, str]:
        """Update existing product.
        
        Args:
            product_idx: Index of product to update
            name: New product name
            unit: New product unit
            
        Returns:
            Tuple containing:
                - Status message
                - Database summary
        """
        if product_idx < 0 or product_idx >= len(self.db.products):
            return "Error: Invalid product selection", self.get_database_summary()

        if not name.strip():
            return "Error: Product name cannot be empty", self.get_database_summary()

        product = self.db.products[product_idx]
        product.update_info(name.strip(), unit.strip())
        return (
            f"✅ Updated product: {product.name} ({product.unit})",
            self.get_database_summary()
        )

    def delete_product(self, product_idx: int) -> Tuple[str, gr.Dropdown, str]:
        """Delete product.
        
        Args:
            product_idx: Index of product to delete
            
        Returns:
            Tuple containing:
                - Status message
                - Updated products dropdown
                - Database summary
        """
        if product_idx < 0 or product_idx >= len(self.db.products):
            return (
                "Error: Invalid product selection",
                gr.Dropdown(choices=self.get_products_list()),
                self.get_database_summary()
            )

        product_name = self.db.products[product_idx].name
        success = self.db.remove_product(product_idx)

        if success:
            return (
                f"🗑️ Deleted product: {product_name}",
                gr.Dropdown(choices=self.get_products_list()),
                self.get_database_summary()
            )
        return (
            "Error: Could not delete product",
            gr.Dropdown(choices=self.get_products_list()),
            self.get_database_summary()
        )

    # SHEET CRUD OPERATIONS
    def create_sheet(self, product_idx: int, year: int, month: int) -> Tuple[str, gr.Dropdown]:
        """Create a new sheet.
        
        Args:
            product_idx: Index of parent product
            year: Year for the new sheet
            month: Month for the new sheet (1-12)
            
        Returns:
            Tuple containing:
                - Status message
                - Updated sheets dropdown
        """
        if product_idx < 0 or product_idx >= len(self.db.products):
            return (
                "Error: Invalid product selection",
                gr.Dropdown(choices=["No sheets available"])
            )

        if not 1 <= month <= 12:
            return (
                "Error: Month must be between 1 and 12",
                gr.Dropdown(choices=["No sheets available"])
            )

        product = self.db.products[product_idx]
        sheet = product.create_sheet(year, month)
        return (
            f"✅ Created sheet: {sheet.year}-{sheet.month:02d} for {product.name}",
            gr.Dropdown(choices=self.get_sheets_list(product_idx))
        )

    def delete_sheet(self, product_idx: int, sheet_idx: int) -> Tuple[str, gr.Dropdown]:
        """Delete sheet.
        
        Args:
            product_idx: Index of parent product
            sheet_idx: Index of sheet to delete
            
        Returns:
            Tuple containing:
                - Status message
                - Updated sheets dropdown
        """
        try:
            product = self.db.products[product_idx]
            if sheet_idx < 0 or sheet_idx >= len(product.sheets):
                return (
                    "Error: Invalid sheet selection",
                    gr.Dropdown(choices=self.get_sheets_list(product_idx))
                )

            sheet_name = f"{product.sheets[sheet_idx].year}-{product.sheets[sheet_idx].month:02d}"
            success = product.remove_sheet(sheet_idx)

            if success:
                return (
                    f"🗑️ Deleted sheet: {sheet_name}",
                    gr.Dropdown(choices=self.get_sheets_list(product_idx))
                )
            return (
                "Error: Could not delete sheet",
                gr.Dropdown(choices=self.get_sheets_list(product_idx))
            )
        except (IndexError, AttributeError):
            return (
                "Error: Invalid selection",
                gr.Dropdown(choices=["No sheets available"])
            )

    # PAGE CRUD OPERATIONS
    def create_page(self, product_idx: int, sheet_idx: int,
                   price: float, sold_init: float) -> Tuple[str, gr.Dropdown]:
        """Create a new page.
        
        Args:
            product_idx: Index of parent product
            sheet_idx: Index of parent sheet
            price: Price for the new page
            sold_init: Initial stock amount
            
        Returns:
            Tuple containing:
                - Status message
                - Updated pages dropdown
        """
        try:
            sheet = self.db.products[product_idx].sheets[sheet_idx]
            page = sheet.create_page(price, sold_init)
            return (
                f"✅ Created page: Price ${page.price:.2f}, Initial stock: {page.sold_init:.2f}",
                gr.Dropdown(choices=self.get_pages_list(product_idx, sheet_idx))
            )
        except (IndexError, AttributeError):
            return (
                "Error: Invalid selection",
                gr.Dropdown(choices=["No pages available"])
            )

    def delete_page(self, product_idx: int, sheet_idx: int, page_idx: int) -> Tuple[str, gr.Dropdown]:
        """Delete page.
        
        Args:
            product_idx: Index of parent product
            sheet_idx: Index of parent sheet
            page_idx: Index of page to delete
            
        Returns:
            Tuple containing:
                - Status message
                - Updated pages dropdown
        """
        try:
            sheet = self.db.products[product_idx].sheets[sheet_idx]
            if page_idx < 0 or page_idx >= len(sheet.pages):
                return (
                    "Error: Invalid page selection",
                    gr.Dropdown(choices=self.get_pages_list(product_idx, sheet_idx))
                )

            page_info = f"Price ${sheet.pages[page_idx].price:.2f}"
            success = sheet.remove_page(page_idx)

            if success:
                return (
                    f"🗑️ Deleted page: {page_info}",
                    gr.Dropdown(choices=self.get_pages_list(product_idx, sheet_idx))
                )
            return (
                "Error: Could not delete page",
                gr.Dropdown(choices=self.get_pages_list(product_idx, sheet_idx))
            )
        except (IndexError, AttributeError):
            return (
                "Error: Invalid selection",
                gr.Dropdown(choices=["No pages available"])
            )

    # RECORD CRUD OPERATIONS
    def create_record(self, product_idx: int, sheet_idx: int, page_idx: int,
                     input_val: float, output_val: float,
                     doc_id: str, doc_type: str, dom: int) -> Tuple[str, gr.Dropdown]:
        """Create a new record.
        
        Args:
            product_idx: Index of parent product
            sheet_idx: Index of parent sheet
            page_idx: Index of parent page
            input_val: Input amount
            output_val: Output amount
            doc_id: Document ID
            doc_type: Document type
            dom: Day of month
            
        Returns:
            Tuple containing:
                - Status message
                - Updated records dropdown
        """
        try:
            page = self.db.products[product_idx].sheets[sheet_idx].pages[page_idx]
            if not doc_id.strip():
                return (
                    "Error: Document ID cannot be empty",
                    gr.Dropdown(choices=self.get_records_list(
                        product_idx, sheet_idx, page_idx))
                )

            record = page.create_record(input_val, output_val,
                                      doc_id.strip(), doc_type.strip(), dom)
            return (
                f"✅ Created record: {record.doc_id} - Final stock: {record.sold_final:.2f}",
                gr.Dropdown(choices=self.get_records_list(
                    product_idx, sheet_idx, page_idx))
            )
        except (IndexError, AttributeError):
            return (
                "Error: Invalid selection",
                gr.Dropdown(choices=["No records available"])
            )

    def update_record(self, product_idx: int, sheet_idx: int, page_idx: int, record_idx: int,
                     input_val: float, output_val: float,
                     doc_id: str, doc_type: str, dom: int) -> Tuple[str, gr.Dropdown]:
        """Update existing record.
        
        Args:
            product_idx: Index of parent product
            sheet_idx: Index of parent sheet
            page_idx: Index of parent page
            record_idx: Index of record to update
            input_val: New input amount
            output_val: New output amount
            doc_id: New document ID
            doc_type: New document type
            dom: New day of month
            
        Returns:
            Tuple containing:
                - Status message
                - Updated records dropdown
        """
        try:
            page = self.db.products[product_idx].sheets[sheet_idx].pages[page_idx]
            if record_idx < 0 or record_idx >= len(page.records):
                return (
                    "Error: Invalid record selection",
                    gr.Dropdown(choices=self.get_records_list(
                        product_idx, sheet_idx, page_idx))
                )

            record = page.records[record_idx]
            if not doc_id.strip():
                return (
                    "Error: Document ID cannot be empty",
                    gr.Dropdown(choices=self.get_records_list(
                        product_idx, sheet_idx, page_idx))
                )

            record.update_values(input_val, output_val,
                               doc_id.strip(), doc_type.strip(), dom)
            return (
                f"✅ Updated record: {record.doc_id} - Final stock: {record.sold_final:.2f}",
                gr.Dropdown(choices=self.get_records_list(
                    product_idx, sheet_idx, page_idx))
            )
        except (IndexError, AttributeError):
            return (
                "Error: Invalid selection",
                gr.Dropdown(choices=["No records available"])
            )

    def delete_record(self, product_idx: int, sheet_idx: int,
                     page_idx: int, record_idx: int) -> Tuple[str, gr.Dropdown]:
        """Delete record.
        
        Args:
            product_idx: Index of parent product
            sheet_idx: Index of parent sheet
            page_idx: Index of parent page
            record_idx: Index of record to delete
            
        Returns:
            Tuple containing:
                - Status message
                - Updated records dropdown
        """
        try:
            page = self.db.products[product_idx].sheets[sheet_idx].pages[page_idx]
            if record_idx < 0 or record_idx >= len(page.records):
                return (
                    "Error: Invalid record selection",
                    gr.Dropdown(choices=self.get_records_list(
                        product_idx, sheet_idx, page_idx))
                )

            record_id = page.records[record_idx].doc_id
            success = page.remove_record(record_idx)

            if success:
                return (
                    f"🗑️ Deleted record: {record_id}",
                    gr.Dropdown(choices=self.get_records_list(
                        product_idx, sheet_idx, page_idx))
                )
            return (
                "Error: Could not delete record",
                gr.Dropdown(choices=self.get_records_list(
                    product_idx, sheet_idx, page_idx))
            )
        except (IndexError, AttributeError):
            return (
                "Error: Invalid selection",
                gr.Dropdown(choices=["No records available"])
            )

    def get_database_summary(self) -> str:
        """Generate a summary of the database contents.
        
        Returns:
            Formatted string with database summary
        """
        summary = "📊 **Database Summary**\n\n"
        summary += f"**Total Products:** {len(self.db.products)}\n\n"

        for i, product in enumerate(self.db.products):
            summary += f"**{i+1}. {product.name}** ({product.unit})\n"
            summary += f"   - Sheets: {len(product.sheets)}\n"

            total_pages = sum(len(sheet.pages) for sheet in product.sheets)
            total_records = sum(len(page.records) for sheet in product.sheets
                              for page in sheet.pages)

            summary += f"   - Pages: {total_pages}\n"
            summary += f"   - Records: {total_records}\n"

            # Show current stock levels
            if product.sheets:
                for sheet in product.sheets:
                    if sheet.pages:
                        for page in sheet.pages:
                            summary += (
                                f"   - Current Stock (Price ${page.price:.2f}): "
                                f"{page.sold_final:.2f}\n"
                            )
            summary += "\n"

        return summary if self.db.products else "No products in database"

    def export_to_dataframe(self, product_idx: int) -> pd.DataFrame:
        """Export product data to pandas DataFrame.
        
        Args:
            product_idx: Index of product to export
            
        Returns:
            DataFrame containing all records for the product
        """
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
                        'Page_Final_Stock': page.sold_final,
                        'Doc_ID': record.doc_id,
                        'Doc_Type': record.doc_type,
                        'DOM': record.dom,
                        'Input': record.input,
                        'Output': record.output,
                        'Record_Init_Stock': record.sold_init,
                        'Record_Final_Stock': record.sold_final
                    })

        return pd.DataFrame(data)


def get_product_idx(selection: str) -> int:
    """Extract product index from dropdown selection.
    
    Args:
        selection: Dropdown selection string
        
    Returns:
        Extracted product index or -1 if invalid
    """
    if not selection or "No products" in selection:
        return -1
    return int(selection.split(":")[0])


def get_sheet_idx(selection: str) -> int:
    """Extract sheet index from dropdown selection.
    
    Args:
        selection: Dropdown selection string
        
    Returns:
        Extracted sheet index or -1 if invalid
    """
    if not selection or "No sheets" in selection:
        return -1
    return int(selection.split(":")[0])


def get_page_idx(selection: str) -> int:
    """Extract page index from dropdown selection.
    
    Args:
        selection: Dropdown selection string
        
    Returns:
        Extracted page index or -1 if invalid
    """
    if not selection or "No pages" in selection:
        return -1
    return int(selection.split(":")[0])


def get_record_idx(selection: str) -> int:
    """Extract record index from dropdown selection.
    
    Args:
        selection: Dropdown selection string
        
    Returns:
        Extracted record index or -1 if invalid
    """
    if not selection or "No records" in selection:
        return -1
    return int(selection.split(":")[0])


def create_interface(warehouse_ui: WarehouseUI) -> gr.Blocks:
    """Create the Gradio interface for warehouse management.
    
    Args:
        warehouse_ui: WarehouseUI instance
        
    Returns:
        Configured Gradio Blocks interface
    """
    with gr.Blocks(title="🏭 Warehouse Management System",
                  theme=gr.themes.Soft()) as app:
        gr.HTML("<h1 style='text-align: center; color: #2E8B57;'>"
               "🏭 Warehouse Management System</h1>")

        with gr.Tabs():
            # PRODUCTS TAB
            with gr.TabItem("📦 Products"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML("<h3>Create Product</h3>")
                        product_name = gr.Textbox(
                            label="Product Name",
                            placeholder="Enter product name")
                        product_unit = gr.Textbox(
                            label="Unit",
                            placeholder="kg, pieces, liters, etc.")
                        create_product_btn = gr.Button(
                            "➕ Create Product", variant="primary")

                        gr.HTML("<h3>Manage Products</h3>")
                        with gr.Row():
                            products_dropdown = gr.Dropdown(
                                label="Select Product",
                                choices=warehouse_ui.get_products_list(),
                                value=(0 if warehouse_ui.get_products_list()[0] != "No products available"
                                      else None)
                            )
                            sync_products_btn = gr.Button(
                                "🔄 Sync", variant="secondary", size="sm")

                        update_name = gr.Textbox(label="New Name")
                        update_unit = gr.Textbox(label="New Unit")

                        with gr.Row():
                            update_product_btn = gr.Button(
                                "✏️ Update", variant="secondary")
                            delete_product_btn = gr.Button(
                                "🗑️ Delete", variant="stop")

                    with gr.Column(scale=1):
                        product_status = gr.Textbox(
                            label="Status", interactive=False)
                        db_summary = gr.Markdown(
                            warehouse_ui.get_database_summary())

                # Event handlers for products
                create_product_btn.click(
                    warehouse_ui.create_product,
                    inputs=[product_name, product_unit],
                    outputs=[product_status, products_dropdown, db_summary]
                )

                update_product_btn.click(
                    lambda sel, name, unit: warehouse_ui.update_product(
                        get_product_idx(sel), name, unit),
                    inputs=[products_dropdown, update_name, update_unit],
                    outputs=[product_status, db_summary]
                )

                delete_product_btn.click(
                    lambda sel: warehouse_ui.delete_product(
                        get_product_idx(sel)),
                    inputs=[products_dropdown],
                    outputs=[product_status, products_dropdown, db_summary]
                )

                # Sync button handler for Products tab
                sync_products_btn.click(
                    lambda: [
                        gr.Dropdown(choices=warehouse_ui.get_products_list()),
                        warehouse_ui.get_database_summary()
                    ],
                    inputs=[],
                    outputs=[products_dropdown, db_summary]
                )

            # SHEETS TAB
            with gr.TabItem("📋 Sheets"):
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            products_for_sheets = gr.Dropdown(
                                label="Select Product",
                                choices=warehouse_ui.get_products_list()
                            )
                            sync_sheets_product_btn = gr.Button(
                                "🔄 Sync", variant="secondary", size="sm")

                        gr.HTML("<h3>Create Sheet</h3>")
                        sheet_year = gr.Number(
                            label="Year", value=2025, precision=0)
                        sheet_month = gr.Number(
                            label="Month", value=1, precision=0,
                            minimum=1, maximum=12)
                        create_sheet_btn = gr.Button(
                            "➕ Create Sheet", variant="primary")

                        gr.HTML("<h3>Manage Sheets</h3>")
                        with gr.Row():
                            sheets_dropdown = gr.Dropdown(
                                label="Select Sheet",
                                choices=["Select product first"])
                            sync_sheets_btn = gr.Button(
                                "🔄 Sync", variant="secondary", size="sm")
                        delete_sheet_btn = gr.Button(
                            "🗑️ Delete Sheet", variant="stop")

                    with gr.Column():
                        sheet_status = gr.Textbox(
                            label="Status", interactive=False)

                # Update sheets dropdown when product changes
                products_for_sheets.change(
                    lambda sel: gr.Dropdown(
                        choices=warehouse_ui.get_sheets_list(
                            get_product_idx(sel)) if sel else []),
                    inputs=[products_for_sheets],
                    outputs=[sheets_dropdown]
                )

                create_sheet_btn.click(
                    lambda sel, year, month: warehouse_ui.create_sheet(
                        get_product_idx(sel), int(year), int(month)),
                    inputs=[products_for_sheets, sheet_year, sheet_month],
                    outputs=[sheet_status, sheets_dropdown]
                )

                delete_sheet_btn.click(
                    lambda prod_sel, sheet_sel: warehouse_ui.delete_sheet(
                        get_product_idx(prod_sel), get_sheet_idx(sheet_sel)),
                    inputs=[products_for_sheets, sheets_dropdown],
                    outputs=[sheet_status, sheets_dropdown]
                )

                # Sync buttons handlers for Sheets tab
                sync_sheets_product_btn.click(
                    lambda: gr.Dropdown(
                        choices=warehouse_ui.get_products_list()),
                    inputs=[],
                    outputs=[products_for_sheets]
                )

                sync_sheets_btn.click(
                    lambda sel: gr.Dropdown(
                        choices=warehouse_ui.get_sheets_list(
                            get_product_idx(sel)) if sel else []),
                    inputs=[products_for_sheets],
                    outputs=[sheets_dropdown]
                )

            # PAGES TAB
            with gr.TabItem("📄 Pages"):
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            products_for_pages = gr.Dropdown(
                                label="Select Product",
                                choices=warehouse_ui.get_products_list())
                            sync_pages_product_btn = gr.Button(
                                "🔄 Sync", variant="secondary", size="sm")
                        with gr.Row():
                            sheets_for_pages = gr.Dropdown(
                                label="Select Sheet",
                                choices=["Select product first"])
                            sync_pages_sheet_btn = gr.Button(
                                "🔄 Sync", variant="secondary", size="sm")

                        gr.HTML("<h3>Create Page</h3>")
                        page_price = gr.Number(
                            label="Price", value=0.0, step=0.01)
                        page_sold_init = gr.Number(
                            label="Initial Stock", value=0.0, step=0.01)
                        create_page_btn = gr.Button(
                            "➕ Create Page", variant="primary")

                        gr.HTML("<h3>Manage Pages</h3>")
                        with gr.Row():
                            pages_dropdown = gr.Dropdown(
                                label="Select Page",
                                choices=["Select sheet first"])
                            sync_pages_btn = gr.Button(
                                "🔄 Sync", variant="secondary", size="sm")
                        delete_page_btn = gr.Button(
                            "🗑️ Delete Page", variant="stop")

                    with gr.Column():
                        page_status = gr.Textbox(
                            label="Status", interactive=False)

                # Update dropdowns
                products_for_pages.change(
                    lambda sel: gr.Dropdown(
                        choices=warehouse_ui.get_sheets_list(
                            get_product_idx(sel)) if sel else []),
                    inputs=[products_for_pages],
                    outputs=[sheets_for_pages]
                )

                sheets_for_pages.change(
                    lambda prod_sel, sheet_sel: gr.Dropdown(
                        choices=warehouse_ui.get_pages_list(
                            get_product_idx(prod_sel),
                            get_sheet_idx(sheet_sel)) if prod_sel and sheet_sel else []),
                    inputs=[products_for_pages, sheets_for_pages],
                    outputs=[pages_dropdown]
                )

                create_page_btn.click(
                    lambda prod_sel, sheet_sel, price, init: warehouse_ui.create_page(
                        get_product_idx(prod_sel),
                        get_sheet_idx(sheet_sel), price, init),
                    inputs=[products_for_pages, sheets_for_pages,
                           page_price, page_sold_init],
                    outputs=[page_status, pages_dropdown]
                )

                delete_page_btn.click(
                    lambda prod_sel, sheet_sel, page_sel: warehouse_ui.delete_page(
                        get_product_idx(prod_sel),
                        get_sheet_idx(sheet_sel),
                        get_page_idx(page_sel)),
                    inputs=[products_for_pages, sheets_for_pages, pages_dropdown],
                    outputs=[page_status, pages_dropdown]
                )

                # Sync buttons handlers for Pages tab
                sync_pages_product_btn.click(
                    lambda: gr.Dropdown(
                        choices=warehouse_ui.get_products_list()),
                    inputs=[],
                    outputs=[products_for_pages]
                )

                sync_pages_sheet_btn.click(
                    lambda sel: gr.Dropdown(
                        choices=warehouse_ui.get_sheets_list(
                            get_product_idx(sel)) if sel else []),
                    inputs=[products_for_pages],
                    outputs=[sheets_for_pages]
                )

                sync_pages_btn.click(
                    lambda prod_sel, sheet_sel: gr.Dropdown(
                        choices=warehouse_ui.get_pages_list(
                            get_product_idx(prod_sel),
                            get_sheet_idx(sheet_sel)) if prod_sel and sheet_sel else []),
                    inputs=[products_for_pages, sheets_for_pages],
                    outputs=[pages_dropdown]
                )

            # RECORDS TAB
            with gr.TabItem("📝 Records"):
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            products_for_records = gr.Dropdown(
                                label="Select Product",
                                choices=warehouse_ui.get_products_list())
                            sync_records_product_btn = gr.Button(
                                "🔄 Sync", variant="secondary", size="sm")
                        with gr.Row():
                            sheets_for_records = gr.Dropdown(
                                label="Select Sheet",
                                choices=["Select product first"])
                            sync_records_sheet_btn = gr.Button(
                                "🔄 Sync", variant="secondary", size="sm")
                        with gr.Row():
                            pages_for_records = gr.Dropdown(
                                label="Select Page",
                                choices=["Select sheet first"])
                            sync_records_page_btn = gr.Button(
                                "🔄 Sync", variant="secondary", size="sm")

                        gr.HTML("<h3>Create/Update Record</h3>")
                        record_input = gr.Number(
                            label="Input", value=0.0, step=0.01)
                        record_output = gr.Number(
                            label="Output", value=0.0, step=0.01)
                        record_doc_id = gr.Textbox(
                            label="Document ID",
                            placeholder="Enter document ID")
                        record_doc_type = gr.Textbox(
                            label="Document Type",
                            placeholder="e.g., Invoice, Receipt")
                        record_dom = gr.Number(
                            label="DOM (Day of Month)",
                            value=1, precision=0, minimum=1, maximum=31)

                        with gr.Row():
                            create_record_btn = gr.Button(
                                "➕ Create Record", variant="primary")
                            update_record_btn = gr.Button(
                                "✏️ Update Record", variant="secondary")

                        gr.HTML("<h3>Manage Records</h3>")
                        with gr.Row():
                            records_dropdown = gr.Dropdown(
                                label="Select Record",
                                choices=["Select page first"])
                            sync_records_btn = gr.Button(
                                "🔄 Sync", variant="secondary", size="sm")
                        delete_record_btn = gr.Button(
                            "🗑️ Delete Record", variant="stop")

                    with gr.Column():
                        record_status = gr.Textbox(
                            label="Status", interactive=False)

                # Update dropdowns for records
                products_for_records.change(
                    lambda sel: gr.Dropdown(
                        choices=warehouse_ui.get_sheets_list(
                            get_product_idx(sel)) if sel else []),
                    inputs=[products_for_records],
                    outputs=[sheets_for_records]
                )

                sheets_for_records.change(
                    lambda prod_sel, sheet_sel: gr.Dropdown(
                        choices=warehouse_ui.get_pages_list(
                            get_product_idx(prod_sel),
                            get_sheet_idx(sheet_sel)) if prod_sel and sheet_sel else []),
                    inputs=[products_for_records, sheets_for_records],
                    outputs=[pages_for_records]
                )

                pages_for_records.change(
                    lambda prod_sel, sheet_sel, page_sel: gr.Dropdown(
                        choices=warehouse_ui.get_records_list(
                            get_product_idx(prod_sel),
                            get_sheet_idx(sheet_sel),
                            get_page_idx(page_sel)) if prod_sel and sheet_sel and page_sel else []),
                    inputs=[products_for_records, sheets_for_records, pages_for_records],
                    outputs=[records_dropdown]
                )

                create_record_btn.click(
                    lambda prod_sel, sheet_sel, page_sel, inp, out, doc_id, doc_type, dom: warehouse_ui.create_record(
                        get_product_idx(prod_sel),
                        get_sheet_idx(sheet_sel),
                        get_page_idx(page_sel),
                        inp, out, doc_id, doc_type, dom),
                    inputs=[products_for_records, sheets_for_records, pages_for_records,
                           record_input, record_output, record_doc_id, record_doc_type, record_dom],
                    outputs=[record_status, records_dropdown]
                )

                update_record_btn.click(
                    lambda prod_sel, sheet_sel, page_sel, rec_sel, inp, out, doc_id, doc_type, dom: warehouse_ui.update_record(
                        get_product_idx(prod_sel),
                        get_sheet_idx(sheet_sel),
                        get_page_idx(page_sel),
                        get_record_idx(rec_sel),
                        inp, out, doc_id, doc_type, dom),
                    inputs=[products_for_records, sheets_for_records, pages_for_records, records_dropdown,
                           record_input, record_output, record_doc_id, record_doc_type, record_dom],
                    outputs=[record_status, records_dropdown]
                )

                delete_record_btn.click(
                    lambda prod_sel, sheet_sel, page_sel, rec_sel: warehouse_ui.delete_record(
                        get_product_idx(prod_sel),
                        get_sheet_idx(sheet_sel),
                        get_page_idx(page_sel),
                        get_record_idx(rec_sel)),
                    inputs=[products_for_records, sheets_for_records, pages_for_records, records_dropdown],
                    outputs=[record_status, records_dropdown]
                )

                # Sync buttons handlers for Records tab
                sync_records_product_btn.click(
                    lambda: gr.Dropdown(
                        choices=warehouse_ui.get_products_list()),
                    inputs=[],
                    outputs=[products_for_records]
                )

                sync_records_sheet_btn.click(
                    lambda sel: gr.Dropdown(
                        choices=warehouse_ui.get_sheets_list(
                            get_product_idx(sel)) if sel else []),
                    inputs=[products_for_records],
                    outputs=[sheets_for_records]
                )

                sync_records_page_btn.click(
                    lambda prod_sel, sheet_sel: gr.Dropdown(
                        choices=warehouse_ui.get_pages_list(
                            get_product_idx(prod_sel),
                            get_sheet_idx(sheet_sel)) if prod_sel and sheet_sel else []),
                    inputs=[products_for_records, sheets_for_records],
                    outputs=[pages_for_records]
                )

                sync_records_btn.click(
                    lambda prod_sel, sheet_sel, page_sel: gr.Dropdown(
                        choices=warehouse_ui.get_records_list(
                            get_product_idx(prod_sel),
                            get_sheet_idx(sheet_sel),
                            get_page_idx(page_sel)) if prod_sel and sheet_sel and page_sel else []),
                    inputs=[products_for_records, sheets_for_records, pages_for_records],
                    outputs=[records_dropdown]
                )

            # DATA EXPORT TAB
            with gr.TabItem("📊 Data Export"):
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            products_for_export = gr.Dropdown(
                                label="Select Product to Export",
                                choices=warehouse_ui.get_products_list())
                            sync_export_btn = gr.Button(
                                "🔄 Sync", variant="secondary", size="sm")
                        export_btn = gr.Button(
                            "📥 Export to DataFrame", variant="primary")

                    with gr.Column():
                        export_data = gr.Dataframe(
                            label="Exported Data", interactive=False)

                export_btn.click(
                    lambda sel: warehouse_ui.export_to_dataframe(
                        get_product_idx(sel)),
                    inputs=[products_for_export],
                    outputs=[export_data]
                )

                # Sync button handler for Export tab
                sync_export_btn.click(
                    lambda: gr.Dropdown(
                        choices=warehouse_ui.get_products_list()),
                    inputs=[],
                    outputs=[products_for_export]
                )

        gr.HTML("""
        <div style='text-align: center; margin-top: 20px; color: #666;'>
            <p>🏭 Warehouse Management System | Built with Gradio</p>
            <p>Features: Full CRUD operations, Real-time updates, Data export capabilities</p>
        </div>
        """)

    return app


def launch_app(share: bool = False, debug: bool = False) -> gr.Blocks:
    """Launch the Warehouse Management UI.
    
    Args:
        share: Whether to create a public share link
        debug: Whether to run in debug mode
        
    Returns:
        The Gradio Blocks interface
    """
    # Initialize UI
    try:
        db = load_warehouse_db(filename="db.json", format="json")
    except FileNotFoundError:
        try:
            db = load_warehouse_db(
                filename="db.json", format="json", folder_path='/content/warehouse')
        except FileNotFoundError:
            db = DATABASE()  # Create empty database if file not found

    warehouse_ui = WarehouseUI(db)
    app = create_interface(warehouse_ui)
    app.launch(share=share, debug=debug, height=800)
    return app


if __name__ == "__main__":
    print("🏭 Warehouse Management System")
    print("================================")
    launch_app()