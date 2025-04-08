from warehouse import DATABASE, PRODUCT, SHEET, PAGE, RECORD
import gradio as gr
import json
import os

# Global database instance and persistence file
DB_FILE = "warehouse_db.json"
db = DATABASE()
db.init()

# Persistence functions
def save_db():
    data = {
        "products": [{
            "name": prod.name,
            "unit": prod.unit,
            "sheets": [{
                "year": sheet.year,
                "month": sheet.month,
                "pages": [{
                    "price": page.price,
                    "sold_final": page.sold_final,
                    "records": [{
                        "input": rec.input,
                        "output": rec.output,
                        "sold_final": rec.sold_final,
                        "doc_id": rec.doc_id,
                        "doc_type": rec.doc_type,
                        "dom": rec.dom
                    } for rec in page.records]
                } for page in sheet.pages]
            } for sheet in prod.sheets]
        } for prod in db.products]
    }
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)
    return display_db_state()

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            db.products.clear()
            db.maxproduct = 0
            for prod_data in data["products"]:
                db.create_product(prod_data["name"], prod_data["unit"])
                product = db.products[-1]
                for sheet_data in prod_data["sheets"]:
                    product.create_sheet(sheet_data["year"], sheet_data["month"])
                    sheet = product.sheets[-1]
                    for page_data in sheet_data["pages"]:
                        sheet.create_page(page_data["price"], 0)  # sold_init not stored, using 0
                        page = sheet.pages[-1]
                        page.sold_final = page_data["sold_final"]
                        for rec_data in page_data["records"]:
                            page.create_record(
                                rec_data["input"],
                                rec_data["output"],
                                rec_data["sold_final"],
                                rec_data["doc_id"],
                                rec_data["doc_type"],
                                rec_data["dom"]
                            )
    return display_db_state()

# Helper function to display current database state
def display_db_state():
    output = "Warehouse Database:\n"
    for i, product in enumerate(db.products):
        output += f"{product.name} ({product.unit})\n"
        for j, sheet in enumerate(product.sheets):
            output += f"  {sheet.year}-{sheet.month:02d}\n"
            for k, page in enumerate(sheet.pages):
                output += f"    Page {k}: Price=${page.price:.2f}, Sold=${page.sold_final:.2f}\n"
                for m, record in enumerate(page.records):
                    output += f"      Record {m}: In={record.input}, Out={record.output}, Sold=${record.sold_final}, Doc={record.doc_id}\n"
    return output if db.products else "Database is empty."

# Dropdown list generators
def get_product_list():
    return [p.name for p in db.products] if db.products else ["No products"]

def get_sheet_list(product_name):
    if not db.products or product_name == "No products":
        return ["No sheets"]
    product = next((p for p in db.products if p.name == product_name), None)
    return [f"{s.year}-{s.month:02d}" for s in product.sheets] if product and product.sheets else ["No sheets"]

def get_page_list(product_name, sheet_name):
    if not db.products or product_name == "No products" or sheet_name == "No sheets":
        return ["No pages"]
    product = next((p for p in db.products if p.name == product_name), None)
    if not product:
        return ["No pages"]
    sheet_idx = next((i for i, s in enumerate(product.sheets) if f"{s.year}-{s.month:02d}" == sheet_name), -1)
    if sheet_idx == -1:
        return ["No pages"]
    return [f"Page {i}" for i in range(len(product.sheets[sheet_idx].pages))] if product.sheets[sheet_idx].pages else ["No pages"]

def get_record_list(product_name, sheet_name, page_name):
    if not db.products or product_name == "No products" or sheet_name == "No sheets" or page_name == "No pages":
        return ["No records"]
    product = next((p for p in db.products if p.name == product_name), None)
    if not product:
        return ["No records"]
    sheet_idx = next((i for i, s in enumerate(product.sheets) if f"{s.year}-{s.month:02d}" == sheet_name), -1)
    if sheet_idx == -1:
        return ["No records"]
    page_idx = int(page_name.split()[-1]) if page_name != "No pages" else -1
    if page_idx < 0 or page_idx >= len(product.sheets[sheet_idx].pages):
        return ["No records"]
    return [f"Record {i}" for i in range(len(product.sheets[sheet_idx].pages[page_idx].records))] if product.sheets[sheet_idx].pages[page_idx].records else ["No records"]

# CRUD Operations for Product
def create_product(name, unit):
    db.create_product(name, unit)
    return save_db(), gr.update(choices=get_product_list())

def update_product(product_name, new_name, unit):
    product = next((p for p in db.products if p.name == product_name), None)
    if product:
        product.name = new_name
        product.unit = unit
    return save_db(), gr.update(choices=get_product_list())

def delete_product(product_name):
    product_idx = next((i for i, p in enumerate(db.products) if p.name == product_name), -1)
    if product_idx != -1:
        db.products.pop(product_idx)
        db.maxproduct -= 1
    return save_db(), gr.update(choices=get_product_list())

# CRUD Operations for Sheet
def create_sheet(product_name, year, month):
    product = first((p for p in db.products if p.name == product_name), None)
    if product:
        product.create_sheet(year, month)
    return save_db(), gr.update(choices=get_sheet_list(product_name))

def update_sheet(product_name, sheet_name, year, month):
    product = next((p for p in db.products if p.name == product_name), None)
    if product:
        sheet_idx = next((i for i, s in enumerate(product.sheets) if f"{s.year}-{s.month:02d}" == sheet_name), -1)
        if sheet_idx != -1:
            sheet = product.sheets[sheet_idx]
            sheet.year = year
            sheet.month = month
    return save_db(), gr.update(choices=get_sheet_list(product_name))

def delete_sheet(product_name, sheet_name):
    product = next((p for p in db.products if p.name == product_name), None)
    if product:
        sheet_idx = next((i for i, s in enumerate(product.sheets) if f"{s.year}-{s.month:02d}" == sheet_name), -1)
        if sheet_idx != -1:
            product.sheets.pop(sheet_idx)
            product.maxsheet -= 1
    return save_db(), gr.update(choices=get_sheet_list(product_name))

# CRUD Operations for Page
def create_page(product_name, sheet_name, price, sold_final):
    product = next((p for p in db.products if p.name == product_name), None)
    if product:
        sheet_idx = next((i for i, s in enumerate(product.sheets) if f"{s.year}-{s.month:02d}" == sheet_name), -1)
        if sheet_idx != -1:
            product.sheets[sheet_idx].create_page(price, sold_final)
    return save_db(), gr.update(choices=get_page_list(product_name, sheet_name))

def update_page(product_name, sheet_name, page_name, price, sold_final):
    product = next((p for p in db.products if p.name == product_name), None)
    if product:
        sheet_idx = next((i for i, s in enumerate(product.sheets) if f"{s.year}-{s.month:02d}" == sheet_name), -1)
        if sheet_idx != -1:
            page_idx = int(page_name.split()[-1]) if page_name != "No pages" else -1
            if 0 <= page_idx < len(product.sheets[sheet_idx].pages):
                page = product.sheets[sheet_idx].pages[page_idx]
                page.price = price
                page.sold_final = sold_final
    return save_db(), gr.update(choices=get_page_list(product_name, sheet_name))

def delete_page(product_name, sheet_name, page_name):
    product = next((p for p in db.products if p.name == product_name), None)
    if product:
        sheet_idx = next((i for i, s in enumerate(product.sheets) if f"{s.year}-{s.month:02d}" == sheet_name), -1)
        if sheet_idx != -1:
            page_idx = int(page_name.split()[-1]) if page_name != "No pages" else -1
            if 0 <= page_idx < len(product.sheets[sheet_idx].pages):
                product.sheets[sheet_idx].pages.pop(page_idx)
                product.sheets[sheet_idx].maxpage -= 1
    return save_db(), gr.update(choices=get_page_list(product_name, sheet_name))

# CRUD Operations for Record
def create_record(product_name, sheet_name, page_name, input_, output_, sold_final, doc_id, doc_type, dom):
    product = next((p for p in db.products if p.name == product_name), None)
    if product:
        sheet_idx = next((i for i, s in enumerate(product.sheets) if f"{s.year}-{s.month:02d}" == sheet_name), -1)
        if sheet_idx != -1:
            page_idx = int(page_name.split()[-1]) if page_name != "No pages" else -1
            if 0 <= page_idx < len(product.sheets[sheet_idx].pages):
                product.sheets[sheet_idx].pages[page_idx].create_record(input_, output_, sold_final, doc_id, doc_type, dom)
    return save_db(), gr.update(choices=get_record_list(product_name, sheet_name, page_name))

def update_record(product_name, sheet_name, page_name, record_name, input_, output_, sold_final, doc_id, doc_type, dom):
    product = next((p for p in db.products if p.name == product_name), None)
    if product:
        sheet_idx = next((i for i, s in enumerate(product.sheets) if f"{s.year}-{s.month:02d}" == sheet_name), -1)
        if sheet_idx != -1:
            page_idx = int(page_name.split()[-1]) if page_name != "No pages" else -1
            if 0 <= page_idx < len(product.sheets[sheet_idx].pages):
                record_idx = int(record_name.split()[-1]) if record_name != "No records" else -1
                if 0 <= record_idx < len(product.sheets[sheet_idx].pages[page_idx].records):
                    record = product.sheets[sheet_idx].pages[page_idx].records[record_idx]
                    record.input = input_
                    record.output = output_
                    record.sold_final = sold_final
                    record.doc_id = doc_id
                    record.doc_type = doc_type
                    record.dom = dom
    return save_db(), gr.update(choices=get_record_list(product_name, sheet_name, page_name))

def delete_record(product_name, sheet_name, page_name, record_name):
    product = next((p for p in db.products if p.name == product_name), None)
    if product:
        sheet_idx = next((i for i, s in enumerate(product.sheets) if f"{s.year}-{s.month:02d}" == sheet_name), -1)
        if sheet_idx != -1:
            page_idx = int(page_name.split()[-1]) if page_name != "No pages" else -1
            if 0 <= page_idx < len(product.sheets[sheet_idx].pages):
                record_idx = int(record_name.split()[-1]) if record_name != "No records" else -1
                if 0 <= record_idx < len(product.sheets[sheet_idx].pages[page_idx].records):
                    product.sheets[sheet_idx].pages[page_idx].records.pop(record_idx)
    return save_db(), gr.update(choices=get_record_list(product_name, sheet_name, page_name))

# Update dependent dropdowns function
def update_all_dropdowns(product_name):
    sheet_list = get_sheet_list(product_name)
    sheet_name = sheet_list[0] if sheet_list else "No sheets"
    page_list = get_page_list(product_name, sheet_name)
    page_name = page_list[0] if page_list else "No pages"
    record_list = get_record_list(product_name, sheet_name, page_name)
    return gr.update(choices=sheet_list, value=sheet_name), gr.update(choices=page_list, value=page_name), gr.update(choices=record_list, value=record_list[0] if record_list else "No records")

# Gradio Interface
with gr.Blocks(title="Warehouse Management") as demo:
    gr.Markdown("# Warehouse Management System")
    output_text = gr.Textbox(label="Database State", lines=10, interactive=False)

    with gr.Tab("Product"):
        product_dropdown = gr.Dropdown(label="Select Product", choices=get_product_list())
        with gr.Row():
            name_input = gr.Textbox(label="Product Name")
            unit_input = gr.Textbox(label="Unit")
        with gr.Row():
            create_btn = gr.Button("Create")
            update_btn = gr.Button("Update")
            delete_btn = gr.Button("Delete")
        create_btn.click(fn=create_product, inputs=[name_input, unit_input], outputs=[output_text, product_dropdown])
        update_btn.click(fn=update_product, inputs=[product_dropdown, name_input, unit_input], outputs=[output_text, product_dropdown])
        delete_btn.click(fn=delete_product, inputs=[product_dropdown], outputs=[output_text, product_dropdown])
        # Auto-fill fields when product is selected
        product_dropdown.change(
            fn=lambda p: [next((prod.name for prod in db.products if prod.name == p), ""), 
                          next((prod.unit for prod in db.products if prod.name == p), "")],
            inputs=product_dropdown,
            outputs=[name_input, unit_input]
        )

    with gr.Tab("Sheet"):
        product_dropdown_sheet = gr.Dropdown(label="Select Product", choices=get_product_list())
        sheet_dropdown = gr.Dropdown(label="Select Sheet", choices=["No sheets"])
        with gr.Row():
            year_input = gr.Number(label="Year", value=2025)
            month_input = gr.Number(label="Month", value=4)
        with gr.Row():
            create_sheet_btn = gr.Button("Create")
            update_sheet_btn = gr.Button("Update")
            delete_sheet_btn = gr.Button("Delete")
        product_dropdown_sheet.change(fn=get_sheet_list, inputs=product_dropdown_sheet, outputs=sheet_dropdown)
        # Auto-fill fields when sheet is selected
        sheet_dropdown.change(
            fn=lambda p, s: [int(s.split('-')[0]) if s != "No sheets" else 2025, 
                            int(s.split('-')[1]) if s != "No sheets" else 4],
            inputs=[product_dropdown_sheet, sheet_dropdown],
            outputs=[year_input, month_input]
        )
        create_sheet_btn.click(fn=create_sheet, inputs=[product_dropdown_sheet, year_input, month_input], outputs=[output_text, sheet_dropdown])
        update_sheet_btn.click(fn=update_sheet, inputs=[product_dropdown_sheet, sheet_dropdown, year_input, month_input], outputs=[output_text, sheet_dropdown])
        delete_sheet_btn.click(fn=delete_sheet, inputs=[product_dropdown_sheet, sheet_dropdown], outputs=[output_text, sheet_dropdown])

    with gr.Tab("Page"):
        product_dropdown_page = gr.Dropdown(label="Select Product", choices=get_product_list())
        sheet_dropdown_page = gr.Dropdown(label="Select Sheet", choices=["No sheets"])
        page_dropdown = gr.Dropdown(label="Select Page", choices=["No pages"])
        with gr.Row():
            price_input = gr.Number(label="Price", value=0.0)
            sold_final_input = gr.Number(label="Sold Final", value=0.0)
        with gr.Row():
            create_page_btn = gr.Button("Create")
            update_page_btn = gr.Button("Update")
            delete_page_btn = gr.Button("Delete")
        product_dropdown_page.change(fn=get_sheet_list, inputs=product_dropdown_page, outputs=sheet_dropdown_page)
        sheet_dropdown_page.change(fn=lambda p, s: get_page_list(p, s), inputs=[product_dropdown_page, sheet_dropdown_page], outputs=page_dropdown)
        # Auto-fill fields when page is selected
        page_dropdown.change(
            fn=lambda p, s, pg: (
                [next((page.price for page in next((sheet for sheet in next((prod for prod in db.products if prod.name == p), None).sheets 
                                                  if f"{sheet.year}-{sheet.month:02d}" == s), None).pages 
                         if f"Page {i}" == pg), 0.0),
                 next((page.sold_final for page in next((sheet for sheet in next((prod for prod in db.products if prod.name == p), None).sheets 
                                                       if f"{sheet.year}-{sheet.month:02d}" == s), None).pages 
                         if f"Page {i}" == pg), 0.0)]
                if p != "No products" and s != "No sheets" and pg != "No pages" else [0.0, 0.0]
            ),
            inputs=[product_dropdown_page, sheet_dropdown_page, page_dropdown],
            outputs=[price_input, sold_final_input]
        )
        create_page_btn.click(fn=create_page, inputs=[product_dropdown_page, sheet_dropdown_page, price_input, sold_final_input], outputs=[output_text, page_dropdown])
        update_page_btn.click(fn=update_page, inputs=[product_dropdown_page, sheet_dropdown_page, page_dropdown, price_input, sold_final_input], outputs=[output_text, page_dropdown])
        delete_page_btn.click(fn=delete_page, inputs=[product_dropdown_page, sheet_dropdown_page, page_dropdown], outputs=[output_text, page_dropdown])

    with gr.Tab("Record"):
        product_dropdown_rec = gr.Dropdown(label="Select Product", choices=get_product_list())
        sheet_dropdown_rec = gr.Dropdown(label="Select Sheet", choices=["No sheets"])
        page_dropdown_rec = gr.Dropdown(label="Select Page", choices=["No pages"])
        record_dropdown = gr.Dropdown(label="Select Record", choices=["No records"])
        with gr.Row():
            input_rec = gr.Number(label="Input", value=0.0)
            output_rec = gr.Number(label="Output", value=0.0)
            sold_final_rec = gr.Number(label="Sold Final", value=0.0)
        with gr.Row():
            doc_id_rec = gr.Textbox(label="Document ID")
            doc_type_rec = gr.Textbox(label="Document Type")
            dom_rec = gr.Number(label="DOM", value=0)
        with gr.Row():
            create_record_btn = gr.Button("Create")
            update_record_btn = gr.Button("Update")
            delete_record_btn = gr.Button("Delete")
        product_dropdown_rec.change(fn=get_sheet_list, inputs=product_dropdown_rec, outputs=sheet_dropdown_rec)
        sheet_dropdown_rec.change(fn=lambda p, s: get_page_list(p, s), inputs=[product_dropdown_rec, sheet_dropdown_rec], outputs=page_dropdown_rec)
        page_dropdown_rec.change(fn=lambda p, s, pg: get_record_list(p, s, pg), inputs=[product_dropdown_rec, sheet_dropdown_rec, page_dropdown_rec], outputs=record_dropdown)
        
        # Auto-fill fields when record is selected
        def get_record_fields(p, s, pg, r):
            if p == "No products" or s == "No sheets" or pg == "No pages" or r == "No records":
                return 0.0, 0.0, 0.0, "", "", 0
            
            try:
                product = next((prod for prod in db.products if prod.name == p), None)
                if not product:
                    return 0.0, 0.0, 0.0, "", "", 0
                    
                sheet_idx = next((i for i, sheet in enumerate(product.sheets) if f"{sheet.year}-{sheet.month:02d}" == s), -1)
                if sheet_idx == -1:
                    return 0.0, 0.0, 0.0, "", "", 0
                    
                page_idx = int(pg.split()[-1]) if pg != "No pages" else -1
                if page_idx < 0 or page_idx >= len(product.sheets[sheet_idx].pages):
                    return 0.0, 0.0, 0.0, "", "", 0
                    
                record_idx = int(r.split()[-1]) if r != "No records" else -1
                if record_idx < 0 or record_idx >= len(product.sheets[sheet_idx].pages[page_idx].records):
                    return 0.0, 0.0, 0.0, "", "", 0
                    
                record = product.sheets[sheet_idx].pages[page_idx].records[record_idx]
                return record.input, record.output, record.sold_final, record.doc_id, record.doc_type, record.dom
            except Exception:
                return 0.0, 0.0, 0.0, "", "", 0
        
        record_dropdown.change(
            fn=get_record_fields,
            inputs=[product_dropdown_rec, sheet_dropdown_rec, page_dropdown_rec, record_dropdown],
            outputs=[input_rec, output_rec, sold_final_rec, doc_id_rec, doc_type_rec, dom_rec]
        )
        
        create_record_btn.click(fn=create_record, inputs=[product_dropdown_rec, sheet_dropdown_rec, page_dropdown_rec, input_rec, output_rec, sold_final_rec, doc_id_rec, doc_type_rec, dom_rec], outputs=[output_text, record_dropdown])
        update_record_btn.click(fn=update_record, inputs=[product_dropdown_rec, sheet_dropdown_rec, page_dropdown_rec, record_dropdown, input_rec, output_rec, sold_final_rec, doc_id_rec, doc_type_rec, dom_rec], outputs=[output_text, record_dropdown])
        delete_record_btn.click(fn=delete_record, inputs=[product_dropdown_rec, sheet_dropdown_rec, page_dropdown_rec, record_dropdown], outputs=[output_text, record_dropdown])

    # Initial state
    demo.load(fn=load_db, inputs=None, outputs=output_text)

demo.launch(debug=True)