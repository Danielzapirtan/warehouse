import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from dataclasses import dataclass,field,asdict
from typing import List,Optional,Dict,Any
import re
from io import BytesIO
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter,A4
from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# Language support
LANGS = {
    'ro': {
        'app_title': 'Gestiune Depozit',
        'products': 'Produse',
        'sheets': 'Foi',
        'pages': 'Pagini',
        'records': 'Înregistrări',
        'add_product': 'Adaugă Produs',
        'product_name': 'Nume Produs',
        'measure_unit': 'Unitate Măsură',
        'search': 'Căutare',
        'delete': 'Șterge',
        'add_sheet': 'Adaugă Foaie',
        'year': 'An',
        'month': 'Lună',
        'add_page': 'Adaugă Pagină',
        'unit_price': 'Preț Unitar',
        'initial_stock': 'Stoc Inițial',
        'add_record': 'Adaugă Înregistrare',
        'day': 'Zi',
        'doc_id': 'ID Document',
        'doc_type': 'Tip Document',
        'input': 'Intrare',
        'output': 'Ieșire',
        'final_stock': 'Stoc Final',
        'comment': 'Comentariu',
        'download_pdf': 'Descarcă PDF',
        'no_data': 'Nu există date',
        'select_product': 'Selectează produs',
        'select_sheet': 'Selectează foaie',
        'select_page': 'Selectează pagină',
        'confirm_delete': 'Confirmă ștergerea',
        'cancel': 'Anulează',
        'language': 'Limbă',
        'months': ['','Ian','Feb','Mar','Apr','Mai','Iun','Iul','Aug','Sep','Oct','Nov','Dec']
    },
    'en': {
        'app_title': 'Warehouse Management',
        'products': 'Products',
        'sheets': 'Sheets',
        'pages': 'Pages',
        'records': 'Records',
        'add_product': 'Add Product',
        'product_name': 'Product Name',
        'measure_unit': 'Measure Unit',
        'search': 'Search',
        'delete': 'Delete',
        'add_sheet': 'Add Sheet',
        'year': 'Year',
        'month': 'Month',
        'add_page': 'Add Page',
        'unit_price': 'Unit Price',
        'initial_stock': 'Initial Stock',
        'add_record': 'Add Record',
        'day': 'Day',
        'doc_id': 'Document ID',
        'doc_type': 'Document Type',
        'input': 'Input',
        'output': 'Output',
        'final_stock': 'Final Stock',
        'comment': 'Comment',
        'download_pdf': 'Download PDF',
        'no_data': 'No data available',
        'select_product': 'Select product',
        'select_sheet': 'Select sheet',
        'select_page': 'Select page',
        'confirm_delete': 'Confirm delete',
        'cancel': 'Cancel',
        'language': 'Language',
        'months': ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    }
}

@dataclass
class Record:
    day:int
    doc_id:str
    doc_type:str
    input:float=0.0
    output:float=0.0
    comment:str=""
    initial_stock:float=0.0
    final_stock:float=0.0

@dataclass
class Page:
    unit_price:float
    initial_stock:float
    records:List[Record]=field(default_factory=list)

@dataclass
class Sheet:
    year:int
    month:int
    pages:List[Page]=field(default_factory=list)

@dataclass
class Product:
    name:str
    measure_unit:str
    sheets:List[Sheet]=field(default_factory=list)

@dataclass
class Database:
    products:List[Product]=field(default_factory=list)

class Observer:
    def __init__(self):
        self._observers=[]
    def attach(self,observer):
        self._observers.append(observer)
    def notify(self):
        for observer in self._observers:
            observer()

class WarehouseManager:
    def __init__(self,db_path:str):
        self.db_path=Path(db_path)
        self.db_path.parent.mkdir(parents=True,exist_ok=True)
        self.observer=Observer()
        self.load_data()
    
    def load_data(self):
        if self.db_path.exists():
            with open(self.db_path,'r',encoding='utf-8') as f:
                data=json.load(f)
                self.db=self._dict_to_db(data)
        else:
            self.db=Database()
            self.save_data()
    
    def save_data(self):
        with open(self.db_path,'w',encoding='utf-8') as f:
            json.dump(self._db_to_dict(self.db),f,ensure_ascii=False,indent=2)
        self.observer.notify()
    
    def _db_to_dict(self,db:Database)->Dict:
        return asdict(db)
    
    def _dict_to_db(self,data:Dict)->Database:
        products=[]
        for p in data.get('products',[]):
            sheets=[]
            for s in p.get('sheets',[]):
                pages=[]
                for pg in s.get('pages',[]):
                    records=[]
                    for r in pg.get('records',[]):
                        records.append(Record(**r))
                    pages.append(Page(
                        unit_price=pg['unit_price'],
                        initial_stock=pg['initial_stock'],
                        records=records
                    ))
                sheets.append(Sheet(
                    year=s['year'],
                    month=s['month'],
                    pages=pages
                ))
            products.append(Product(
                name=p['name'],
                measure_unit=p['measure_unit'],
                sheets=sheets
            ))
        return Database(products=products)
    
    def add_product(self,name:str,measure_unit:str):
        self.db.products.append(Product(name,measure_unit))
        self.save_data()
    
    def delete_product(self,index:int):
        if 0 <= index < len(self.db.products):
            del self.db.products[index]
            self.save_data()
    
    def add_sheet(self,product_idx:int,year:int,month:int):
        if 0 <= product_idx < len(self.db.products):
            self.db.products[product_idx].sheets.append(Sheet(year,month))
            self.save_data()
    
    def delete_sheet(self,product_idx:int,sheet_idx:int):
        if (0 <= product_idx < len(self.db.products) and 
            0 <= sheet_idx < len(self.db.products[product_idx].sheets)):
            del self.db.products[product_idx].sheets[sheet_idx]
            self.save_data()
    
    def add_page(self,product_idx:int,sheet_idx:int,unit_price:float,initial_stock:float):
        if (0 <= product_idx < len(self.db.products) and 
            0 <= sheet_idx < len(self.db.products[product_idx].sheets)):
            self.db.products[product_idx].sheets[sheet_idx].pages.append(
                Page(unit_price,initial_stock)
            )
            self.save_data()
    
    def delete_page(self,product_idx:int,sheet_idx:int,page_idx:int):
        if (0 <= product_idx < len(self.db.products) and 
            0 <= sheet_idx < len(self.db.products[product_idx].sheets) and
            0 <= page_idx < len(self.db.products[product_idx].sheets[sheet_idx].pages)):
            del self.db.products[product_idx].sheets[sheet_idx].pages[page_idx]
            self.save_data()
    
    def add_record(self,product_idx:int,sheet_idx:int,page_idx:int,record:Record):
        if (0 <= product_idx < len(self.db.products) and 
            0 <= sheet_idx < len(self.db.products[product_idx].sheets) and
            0 <= page_idx < len(self.db.products[product_idx].sheets[sheet_idx].pages)):
            page=self.db.products[product_idx].sheets[sheet_idx].pages[page_idx]
            if page.records:
                record.initial_stock=page.records[-1].final_stock
            else:
                record.initial_stock=page.initial_stock
            record.final_stock=record.initial_stock+record.input-record.output
            page.records.append(record)
            self.save_data()
    
    def delete_record(self,product_idx:int,sheet_idx:int,page_idx:int,record_idx:int):
        if (0 <= product_idx < len(self.db.products) and 
            0 <= sheet_idx < len(self.db.products[product_idx].sheets) and
            0 <= page_idx < len(self.db.products[product_idx].sheets[sheet_idx].pages) and
            0 <= record_idx < len(self.db.products[product_idx].sheets[sheet_idx].pages[page_idx].records)):
            del self.db.products[product_idx].sheets[sheet_idx].pages[page_idx].records[record_idx]
            self.recalculate_stocks(product_idx,sheet_idx,page_idx)
            self.save_data()
    
    def recalculate_stocks(self,product_idx:int,sheet_idx:int,page_idx:int):
        if (0 <= product_idx < len(self.db.products) and 
            0 <= sheet_idx < len(self.db.products[product_idx].sheets) and
            0 <= page_idx < len(self.db.products[product_idx].sheets[sheet_idx].pages)):
            page=self.db.products[product_idx].sheets[sheet_idx].pages[page_idx]
            for i,record in enumerate(page.records):
                if i==0:
                    record.initial_stock=page.initial_stock
                else:
                    record.initial_stock=page.records[i-1].final_stock
                record.final_stock=record.initial_stock+record.input-record.output
    
    def search_products(self,pattern:str)->List[tuple]:
        results=[]
        try:
            regex=re.compile(pattern,re.IGNORECASE)
            for i,product in enumerate(self.db.products):
                if regex.search(product.name):
                    results.append((i,product))
        except:
            pass
        return results

def get_pdf_font():
    try:
        pdfmetrics.registerFont(TTFont('DejaVu','DejaVuSans.ttf'))
        return 'DejaVu'
    except:
        return 'Helvetica'

def generate_pdf(data:pd.DataFrame,title:str,lang:str)->bytes:
    buffer=BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=A4,topMargin=0.5*inch,bottomMargin=0.5*inch)
    elements=[]
    
    font_name=get_pdf_font()
    styles=getSampleStyleSheet()
    title_style=ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        spaceAfter=0.3*inch,
        fontName=font_name
    )
    
    elements.append(Paragraph(title,title_style))
    elements.append(Spacer(1,0.2*inch))
    
    if not data.empty:
        table_data=[list(data.columns)]+data.values.tolist()
        col_widths=[doc.width/len(data.columns)]*len(data.columns)
        
        table=Table(table_data,colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.grey),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('FONTNAME',(0,0),(-1,0),font_name),
            ('FONTSIZE',(0,0),(-1,0),10),
            ('BOTTOMPADDING',(0,0),(-1,0),12),
            ('BACKGROUND',(0,1),(-1,-1),colors.beige),
            ('GRID',(0,0),(-1,-1),1,colors.black),
            ('FONTNAME',(0,1),(-1,-1),font_name),
            ('FONTSIZE',(0,1),(-1,-1),8),
        ]))
        elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()

def handle_delete_confirmation(item_type: str, item_id: str, item_name: str, delete_function, L):
    """Handle delete confirmation with proper state management"""
    
    # Initialize session state for pending deletes
    if 'pending_deletes' not in st.session_state:
        st.session_state.pending_deletes = {}
    
    delete_key = f"{item_type}_{item_id}"
    
    # Check if this item is pending deletion
    if delete_key in st.session_state.pending_deletes:
        st.warning(f"🗑️ {L['confirm_delete']}: {item_name}")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(f"✅ {L['confirm_delete']}", key=f"confirm_{delete_key}"):
                delete_function()
                # Remove from pending deletes
                del st.session_state.pending_deletes[delete_key]
                st.rerun()
        
        with col2:
            if st.button(f"❌ {L['cancel']}", key=f"cancel_{delete_key}"):
                # Remove from pending deletes
                del st.session_state.pending_deletes[delete_key]
                st.rerun()
    else:
        # Show delete button
        if st.button(f"🗑️ {item_name}", key=f"delete_{delete_key}"):
            # Add to pending deletes
            st.session_state.pending_deletes[delete_key] = True
            st.rerun()

def main():
    st.set_page_config(
        page_title="Warehouse Management",
        page_icon="📦",
        layout="wide"
    )
    
    if 'lang' not in st.session_state:
        st.session_state.lang='ro'
    if 'manager' not in st.session_state:
        db_path=os.path.expanduser("~/WarehouseDB/db.json")
        st.session_state.manager=WarehouseManager(db_path)
        st.session_state.manager.observer.attach(lambda:st.rerun())
    
    L=LANGS[st.session_state.lang]
    manager=st.session_state.manager
    
    with st.sidebar:
        st.selectbox(
            L['language'],
            options=['ro','en'],
            index=0 if st.session_state.lang=='ro' else 1,
            key='lang_selector',
            on_change=lambda:setattr(st.session_state,'lang',st.session_state.lang_selector)
        )
    
    st.title(f"📦 {L['app_title']}")
    
    tab1,tab2,tab3,tab4=st.tabs([L['products'],L['sheets'],L['pages'],L['records']])
    
    with tab1:
        col1,col2=st.columns([3,1])
        with col1:
            search_pattern=st.text_input(L['search'],key='product_search')
        
        with st.form('add_product_form'):
            cols=st.columns([2,2,1])
            name=cols[0].text_input(L['product_name'])
            unit=cols[1].text_input(L['measure_unit'])
            if cols[2].form_submit_button(L['add_product']):
                if name and unit:
                    manager.add_product(name,unit)
                    st.rerun()
        
        if search_pattern:
            products=manager.search_products(search_pattern)
        else:
            products=[(i,p) for i,p in enumerate(manager.db.products)]
        
        if products:
            df=pd.DataFrame([
                {
                    L['product_name']:p.name,
                    L['measure_unit']:p.measure_unit,
                    L['sheets']:len(p.sheets)
                } for _,p in products
            ])
            
            st.dataframe(df,use_container_width=True)
            
            pdf_data=generate_pdf(df,L['products'],st.session_state.lang)
            st.download_button(
                label=L['download_pdf'],
                data=pdf_data,
                file_name=f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime='application/pdf'
            )
            
            st.subheader(L['delete'])
            for idx,(i,p) in enumerate(products):
                handle_delete_confirmation(
                    "product", 
                    str(i), 
                    p.name,
                    lambda prod_idx=i: manager.delete_product(prod_idx),
                    L
                )
        else:
            st.info(L['no_data'])
    
    with tab2:
        if manager.db.products:
            product_names=[p.name for p in manager.db.products]
            selected_product=st.selectbox(L['select_product'],product_names)
            product_idx=product_names.index(selected_product)
            
            with st.form('add_sheet_form'):
                cols=st.columns([2,2,1])
                year=cols[0].number_input(L['year'],min_value=2000,max_value=2100,value=datetime.now().year)
                month=cols[1].selectbox(L['month'],range(1,13),format_func=lambda x:L['months'][x])
                if cols[2].form_submit_button(L['add_sheet']):
                    manager.add_sheet(product_idx,int(year),month)
                    st.rerun()
            
            sheets=manager.db.products[product_idx].sheets
            if sheets:
                df=pd.DataFrame([
                    {
                        L['year']:s.year,
                        L['month']:L['months'][s.month],
                        L['pages']:len(s.pages)
                    } for s in sheets
                ])
                
                st.dataframe(df,use_container_width=True)
                
                pdf_data=generate_pdf(df,f"{L['sheets']} - {selected_product}",st.session_state.lang)
                st.download_button(
                    label=L['download_pdf'],
                    data=pdf_data,
                    file_name=f"sheets_{selected_product}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime='application/pdf'
                )
                
                st.subheader(L['delete'])
                for i,s in enumerate(sheets):
                    handle_delete_confirmation(
                        "sheet", 
                        f"{product_idx}_{i}", 
                        f"{s.year}-{L['months'][s.month]}",
                        lambda sheet_idx=i: manager.delete_sheet(product_idx, sheet_idx),
                        L
                    )
            else:
                st.info(L['no_data'])
        else:
            st.info(L['select_product'])
    
    with tab3:
        if manager.db.products:
            product_names=[p.name for p in manager.db.products]
            selected_product=st.selectbox(L['select_product'],product_names,key='page_product')
            product_idx=product_names.index(selected_product)
            
            sheets=manager.db.products[product_idx].sheets
            if sheets:
                sheet_names=[f"{s.year}-{L['months'][s.month]}" for s in sheets]
                selected_sheet=st.selectbox(L['select_sheet'],sheet_names)
                sheet_idx=sheet_names.index(selected_sheet)
                
                with st.form('add_page_form'):
                    cols=st.columns([2,2,1])
                    price=cols[0].number_input(L['unit_price'],min_value=0.0,step=0.01)
                    stock=cols[1].number_input(L['initial_stock'],min_value=0.0,step=0.01)
                    if cols[2].form_submit_button(L['add_page']):
                        manager.add_page(product_idx,sheet_idx,price,stock)
                        st.rerun()
                
                pages=sheets[sheet_idx].pages
                if pages:
                    df=pd.DataFrame([
                        {
                            'ID':i+1,
                            L['unit_price']:p.unit_price,
                            L['initial_stock']:p.initial_stock,
                            L['records']:len(p.records)
                        } for i,p in enumerate(pages)
                    ])
                    
                    st.dataframe(df,use_container_width=True)
                    
                    pdf_data=generate_pdf(df,f"{L['pages']} - {selected_product} - {selected_sheet}",st.session_state.lang)
                    st.download_button(
                        label=L['download_pdf'],
                        data=pdf_data,
                        file_name=f"pages_{selected_product}_{selected_sheet}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime='application/pdf'
                    )
                    
                    st.subheader(L['delete'])
                    for i,p in enumerate(pages):
                        handle_delete_confirmation(
                            "page", 
                            f"{product_idx}_{sheet_idx}_{i}", 
                            f"Page {i+1}",
                            lambda page_idx=i: manager.delete_page(product_idx, sheet_idx, page_idx),
                            L
                        )
                else:
                    st.info(L['no_data'])
            else:
                st.info(L['select_sheet'])
        else:
            st.info(L['select_product'])
    
    with tab4:
        if manager.db.products:
            product_names=[p.name for p in manager.db.products]
            selected_product=st.selectbox(L['select_product'],product_names,key='rec_product')
            product_idx=product_names.index(selected_product)
            
            sheets=manager.db.products[product_idx].sheets
            if sheets:
                sheet_names=[f"{s.year}-{L['months'][s.month]}" for s in sheets]
                selected_sheet=st.selectbox(L['select_sheet'],sheet_names,key='rec_sheet')
                sheet_idx=sheet_names.index(selected_sheet)
                
                pages=sheets[sheet_idx].pages
                if pages:
                    page_names=[f"Page {i+1} (Price: {p.unit_price})" for i,p in enumerate(pages)]
                    selected_page=st.selectbox(L['select_page'],page_names)
                    page_idx=page_names.index(selected_page)
                    
                    with st.form('add_record_form'):
                        cols=st.columns([1,2,2,1,1,2,1])
                        day=cols[0].number_input(L['day'],min_value=1,max_value=31,value=datetime.now().day)
                        doc_id=cols[1].text_input(L['doc_id'])
                        doc_type=cols[2].text_input(L['doc_type'])
                        input_val=cols[3].number_input(L['input'],min_value=0.0,step=0.01)
                        output_val=cols[4].number_input(L['output'],min_value=0.0,step=0.01)
                        comment=cols[5].text_input(L['comment'])
                        
                        if cols[6].form_submit_button(L['add_record']):
                            if doc_id and doc_type:
                                record=Record(
                                    day=int(day),
                                    doc_id=doc_id,
                                    doc_type=doc_type,
                                    input=input_val,
                                    output=output_val,
                                    comment=comment
                                )
                                manager.add_record(product_idx,sheet_idx,page_idx,record)
                                st.rerun()
                    
                    records=pages[page_idx].records
                    if records:
                        df=pd.DataFrame([
                            {
                                L['day']:r.day,
                                L['doc_id']:r.doc_id,
                                L['doc_type']:r.doc_type,
                                L['initial_stock']:r.initial_stock,
                                L['input']:r.input,
                                L['output']:r.output,
                                L['final_stock']:r.final_stock,
                                L['comment']:r.comment
                            } for r in records
                        ])
                        
                        st.dataframe(df,use_container_width=True)
                        
                        pdf_data=generate_pdf(df,f"{L['records']} - {selected_product} - {selected_sheet} - Page {page_idx+1}",st.session_state.lang)
                        st.download_button(
                            label=L['download_pdf'],
                            data=pdf_data,
                            file_name=f"records_{selected_product}_{selected_sheet}_p{page_idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime='application/pdf'
                        )
                        
                        st.subheader(L['delete'])
                        for i,r in enumerate(records):
                            handle_delete_confirmation(
                                "record", 
                                f"{product_idx}_{sheet_idx}_{page_idx}_{i}", 
                                f"{r.doc_id} ({r.day})",
                                lambda record_idx=i: manager.delete_record(product_idx, sheet_idx, page_idx, record_idx),
                                L
                            )
                    else:
                        st.info(L['no_data'])
                else:
                    st.info(L['select_page'])
            else:
                st.info(L['select_sheet'])
        else:
            st.info(L['select_product'])

if __name__=="__main__":
    main()