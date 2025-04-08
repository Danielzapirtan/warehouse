
# Install Gradio in Colab
!pip install gradio

# Paste the warehouse.py code here (assuming it's available in the environment)
# For this example, I'll assume the code you provided is already in the notebook

%cd /content
!rm -rf warehouse
!apt install git
!git clone https://github.com/Danielzapirtan/warehouse.git
%cd warehouse
from warehouse import DATABASE, PRODUCT, SHEET, PAGE, RECORD

import gradio as gr

# Global database instance (assuming db is initialized as in your code)
db = DATABASE()
db.init()

# Helper function to display current database state
def display_db_state():
    output = "Current Database State:\n"
    for i, product in enumerate(db.products):
        output += f"Product {i}: {product.name} ({product.unit})\n"
        for j, sheet in enumerate(product.sheets):
            output += f"  Sheet {j}: {sheet.year}-{sheet.month}\n"
            for k, page in enumerate(sheet.pages):
                output += f"    Page {k}: Price={page.price}, Sold Final={page.sold_final}\n"
                for m, record in enumerate(page.records):
                    output += f"      Record {m}: Input={record.input}, Output={record.output}, Sold Final={record.sold_final}, Doc ID={record.doc_id}\n"
    return output if db.products else "Database is empty."

# Function to create a product
def create_product(name, unit):
    db.create_product(name, unit)
    return display_db_state()

# Function to create a sheet
def create_sheet(product_index, year, month):
    if 0 <= product_index < db.maxproduct:
        db.products[product_index].create_sheet(year, month)
    return display_db_state()

# Function to create a page
def create_page(product_index, sheet_index, price, sold_init):
    if 0 <= product_index < db.maxproduct and 0 <= sheet_index < db.products[product_index].maxsheet:
        db.products[product_index].sheets[sheet_index].create_page(price, sold_init)
    return display_db_state()

# Function to create a record
def create_record(product_index, sheet_index, page_index, input_, output_, sold_init_, doc_id, doc_type, dom):
    if (0 <= product_index < db.maxproduct and
        0 <= sheet_index < db.products[product_index].maxsheet and
        0 <= page_index < db.products[product_index].sheets[sheet_index].maxpage):
        db.products[product_index].sheets[sheet_index].pages[page_index].create_record(
            input_, output_, sold_init_, doc_id, doc_type, dom)
    return display_db_state()

# Function to select a product
def select_product(index):
    success = db.select_product(index)
    return f"Selected product: {index if success else 'Invalid index'}\n" + display_db_state()

# Function to select a sheet
def select_sheet(product_index, sheet_index):
    if 0 <= product_index < db.maxproduct:
        success = db.products[product_index].select_sheet(sheet_index)
        return f"Selected sheet: {sheet_index if success else 'Invalid index'}\n" + display_db_state()
    return "Invalid product index\n" + display_db_state()

# Function to select a page
def select_page(product_index, sheet_index, page_index):
    if (0 <= product_index < db.maxproduct and
        0 <= sheet_index < db.products[product_index].maxsheet):
        success = db.products[product_index].sheets[sheet_index].select_page(page_index)
        return f"Selected page: {page_index if success else 'Invalid index'}\n" + display_db_state()
    return "Invalid product or sheet index\n" + display_db_state()

# Gradio Interface
with gr.Blocks(title="Warehouse Management") as demo:
    gr.Markdown("# Warehouse Management System")
    output_text = gr.Textbox(label="Database State", lines=10, interactive=False)

    with gr.Tab("Product"):
        with gr.Row():
            name_input = gr.Textbox(label="Product Name")
            unit_input = gr.Textbox(label="Unit")
            create_product_btn = gr.Button("Create Product")
        create_product_btn.click(
            fn=create_product,
            inputs=[name_input, unit_input],
            outputs=output_text
        )
        product_index = gr.Number(label="Product Index", value=0)
        select_product_btn = gr.Button("Select Product")
        select_product_btn.click(
            fn=select_product,
            inputs=product_index,
            outputs=output_text
        )

    with gr.Tab("Sheet"):
        with gr.Row():
            product_idx_sheet = gr.Number(label="Product Index", value=0)
            year_input = gr.Number(label="Year", value=2025)
            month_input = gr.Number(label="Month", value=4)
            create_sheet_btn = gr.Button("Create Sheet")
        create_sheet_btn.click(
            fn=create_sheet,
            inputs=[product_idx_sheet, year_input, month_input],
            outputs=output_text
        )
        sheet_index = gr.Number(label="Sheet Index", value=0)
        select_sheet_btn = gr.Button("Select Sheet")
        select_sheet_btn.click(
            fn=select_sheet,
            inputs=[product_idx_sheet, sheet_index],
            outputs=output_text
        )

    with gr.Tab("Page"):
        with gr.Row():
            product_idx_page = gr.Number(label="Product Index", value=0)
            sheet_idx_page = gr.Number(label="Sheet Index", value=0)
            price_input = gr.Number(label="Price", value=0.0)
            sold_init_input = gr.Number(label="Initial Sold", value=0.0)
            create_page_btn = gr.Button("Create Page")
        create_page_btn.click(
            fn=create_page,
            inputs=[product_idx_page, sheet_idx_page, price_input, sold_init_input],
            outputs=output_text
        )
        page_index = gr.Number(label="Page Index", value=0)
        select_page_btn = gr.Button("Select Page")
        select_page_btn.click(
            fn=select_page,
            inputs=[product_idx_page, sheet_idx_page, page_index],
            outputs=output_text
        )

    with gr.Tab("Record"):
        with gr.Row():
            product_idx_rec = gr.Number(label="Product Index", value=0)
            sheet_idx_rec = gr.Number(label="Sheet Index", value=0)
            page_idx_rec = gr.Number(label="Page Index", value=0)
            input_rec = gr.Number(label="Input", value=0.0)
            output_rec = gr.Number(label="Output", value=0.0)
            sold_init_rec = gr.Number(label="Initial Sold", value=0.0)
            doc_id_rec = gr.Textbox(label="Document ID")
            doc_type_rec = gr.Textbox(label="Document Type")
            dom_rec = gr.Number(label="DOM", value=0)
            create_record_btn = gr.Button("Create Record")
        create_record_btn.click(
            fn=create_record,
            inputs=[product_idx_rec, sheet_idx_rec, page_idx_rec, input_rec, output_rec,
                    sold_init_rec, doc_id_rec, doc_type_rec, dom_rec],
            outputs=output_text
        )

    # Initial state
    demo.load(fn=display_db_state, inputs=None, outputs=output_text)

demo.launch(debug=True)