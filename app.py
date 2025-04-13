from typing import Optional, Union
from warehouse import DATABASE, PRODUCT, SHEET, PAGE, RECORD
import gradio as gr

# Global database instance
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

# CRUD Operations for Product
def create_product(name:str, unit:str)->str:
    db.create_product(name, unit)
    return display_db_state()

def update_product(index, name, unit):
    if 0 <= index < db.maxproduct:
        db.products[index].name = name
        db.products[index].unit = unit
    return display_db_state()

def delete_product(index):
    if 0 <= index < db.maxproduct:
        db.products.pop(index)
        db.maxproduct -= 1
    return display_db_state()

# CRUD Operations for Sheet
def create_sheet(product_index, year, month):
    if 0 <= product_index < db.maxproduct:
        db.products[product_index].create_sheet(year, month)
    return display_db_state()

def update_sheet(product_index, sheet_index, year, month):
    if 0 <= product_index < db.maxproduct and 0 <= sheet_index < db.products[product_index].maxsheet:
        sheet = db.products[product_index].sheets[sheet_index]
        sheet.year = year
        sheet.month = month
    return display_db_state()

def delete_sheet(product_index, sheet_index):
    if 0 <= product_index < db.maxproduct and 0 <= sheet_index < db.products[product_index].maxsheet:
        db.products[product_index].sheets.pop(sheet_index)
        db.products[product_index].maxsheet -= 1
    return display_db_state()

# CRUD Operations for Page
def create_page(product_index, sheet_index, price, sold_init):
    if 0 <= product_index < db.maxproduct and 0 <= sheet_index < db.products[product_index].maxsheet:
        db.products[product_index].sheets[sheet_index].create_page(price, sold_init)
    return display_db_state()

def update_page(product_index, sheet_index, page_index, price, sold_final):
    if (0 <= product_index < db.maxproduct and 
        0 <= sheet_index < db.products[product_index].maxsheet and 
        0 <= page_index < db.products[product_index].sheets[sheet_index].maxpage):
        page = db.products[product_index].sheets[sheet_index].pages[page_index]
        page.price = price
        page.sold_final = sold_final
    return display_db_state()

def delete_page(product_index, sheet_index, page_index):
    if (0 <= product_index < db.maxproduct and 
        0 <= sheet_index < db.products[product_index].maxsheet and 
        0 <= page_index < db.products[product_index].sheets[sheet_index].maxpage):
        db.products[product_index].sheets[sheet_index].pages.pop(page_index)
        db.products[product_index].sheets[sheet_index].maxpage -= 1
    return display_db_state()

# CRUD Operations for Record
def create_record(product_index, sheet_index, page_index, input_, output_, sold_init_, doc_id, doc_type, dom):
    if (0 <= product_index < db.maxproduct and
        0 <= sheet_index < db.products[product_index].maxsheet and
        0 <= page_index < db.products[product_index].sheets[sheet_index].maxpage):
        db.products[product_index].sheets[sheet_index].pages[page_index].create_record(
            input_, output_, sold_init_, doc_id, doc_type, dom)
    return display_db_state()

def update_record(product_index, sheet_index, page_index, record_index, input_, output_, sold_final, doc_id, doc_type, dom):
    if (0 <= product_index < db.maxproduct and
        0 <= sheet_index < db.products[product_index].maxsheet and
        0 <= page_index < db.products[product_index].sheets[sheet_index].maxpage and
        0 <= record_index < len(db.products[product_index].sheets[sheet_index].pages[page_index].records)):
        record = db.products[product_index].sheets[sheet_index].pages[page_index].records[record_index]
        record.input = input_
        record.output = output_
        record.sold_final = sold_final
        record.doc_id = doc_id
        record.doc_type = doc_type
        record.dom = dom
    return display_db_state()

def delete_record(product_index, sheet_index, page_index, record_index):
    if (0 <= product_index < db.maxproduct and
        0 <= sheet_index < db.products[product_index].maxsheet and
        0 <= page_index < db.products[product_index].sheets[sheet_index].maxpage and
        0 <= record_index < len(db.products[product_index].sheets[sheet_index].pages[page_index].records)):
        db.products[product_index].sheets[sheet_index].pages[page_index].records.pop(record_index)
    return display_db_state()

# Gradio Interface
with gr.Blocks(title="Warehouse Management") as demo:
    gr.Markdown("# Warehouse Management System")
    output_text = gr.Textbox(label="Database State", lines=10, interactive=False)

    with gr.Tab("Product"):
        with gr.Row():
            product_idx = gr.Number(label="Product Index", value=0)
            name_input = gr.Textbox(label="Product Name")
            unit_input = gr.Textbox(label="Unit")
        with gr.Row():
            create_product_btn = gr.Button("Create")
            update_product_btn = gr.Button("Update")
            delete_product_btn = gr.Button("Delete")
        create_product_btn.click(fn=create_product, inputs=[name_input, unit_input], outputs=output_text)
        update_product_btn.click(fn=update_product, inputs=[product_idx, name_input, unit_input], outputs=output_text)
        delete_product_btn.click(fn=delete_product, inputs=[product_idx], outputs=output_text)

    with gr.Tab("Sheet"):
        with gr.Row():
            product_idx_sheet = gr.Number(label="Product Index", value=0)
            sheet_idx = gr.Number(label="Sheet Index", value=0)
            year_input = gr.Number(label="Year", value=2025)
            month_input = gr.Number(label="Month", value=4)
        with gr.Row():
            create_sheet_btn = gr.Button("Create")
            update_sheet_btn = gr.Button("Update")
            delete_sheet_btn = gr.Button("Delete")
        create_sheet_btn.click(fn=create_sheet, inputs=[product_idx_sheet, year_input, month_input], outputs=output_text)
        update_sheet_btn.click(fn=update_sheet, inputs=[product_idx_sheet, sheet_idx, year_input, month_input], outputs=output_text)
        delete_sheet_btn.click(fn=delete_sheet, inputs=[product_idx_sheet, sheet_idx], outputs=output_text)

    with gr.Tab("Page"):
        with gr.Row():
            product_idx_page = gr.Number(label="Product Index", value=0)
            sheet_idx_page = gr.Number(label="Sheet Index", value=0)
            page_idx = gr.Number(label="Page Index", value=0)
            price_input = gr.Number(label="Price", value=0.0)
            sold_init_input = gr.Number(label="Sold Final", value=0.0)
        with gr.Row():
            create_page_btn = gr.Button("Create")
            update_page_btn = gr.Button("Update")
            delete_page_btn = gr.Button("Delete")
        create_page_btn.click(fn=create_page, inputs=[product_idx_page, sheet_idx_page, price_input, sold_init_input], outputs=output_text)
        update_page_btn.click(fn=update_page, inputs=[product_idx_page, sheet_idx_page, page_idx, price_input, sold_init_input], outputs=output_text)
        delete_page_btn.click(fn=delete_page, inputs=[product_idx_page, sheet_idx_page, page_idx], outputs=output_text)

    with gr.Tab("Record"):
        with gr.Row():
            product_idx_rec = gr.Number(label="Product Index", value=0)
            sheet_idx_rec = gr.Number(label="Sheet Index", value=0)
            page_idx_rec = gr.Number(label="Page Index", value=0)
            record_idx = gr.Number(label="Record Index", value=0)
        with gr.Row():
            input_rec = gr.Number(label="Input", value=0.0)
            output_rec = gr.Number(label="Output", value=0.0)
            sold_final_rec = gr.Number(label="Sold Final", value=0.0)
            doc_id_rec = gr.Textbox(label="Document ID")
            doc_type_rec = gr.Textbox(label="Document Type")
            dom_rec = gr.Number(label="DOM", value=0)
        with gr.Row():
            create_record_btn = gr.Button("Create")
            update_record_btn = gr.Button("Update")
            delete_record_btn = gr.Button("Delete")
        create_record_btn.click(fn=create_record, inputs=[product_idx_rec, sheet_idx_rec, page_idx_rec, input_rec, output_rec, sold_final_rec, doc_id_rec, doc_type_rec, dom_rec], outputs=output_text)
        update_record_btn.click(fn=update_record, inputs=[product_idx_rec, sheet_idx_rec, page_idx_rec, record_idx, input_rec, output_rec, sold_final_rec, doc_id_rec, doc_type_rec, dom_rec], outputs=output_text)
        delete_record_btn.click(fn=delete_record, inputs=[product_idx_rec, sheet_idx_rec, page_idx_rec, record_idx], outputs=output_text)

    # Initial state
    demo.load(fn=display_db_state, inputs=None, outputs=output_text)

demo.launch(debug=True)
