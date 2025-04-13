from typing import Optional, List

class RECORD:
    def __init__(self) -> None:
        self.input: float = 0.0
        self.output: float = 0.0
        self.sold_final: float = 0.0
        self.sold_init: float = 0.0
        self.doc_id: str = ''
        self.doc_type: str = ''
        self.dom: int = 0
        self.page: Optional['PAGE'] = None

    def init(self, input_: float, output_: float, sold_final_: float, 
             sold_init_: float, doc_id_: str, doc_type_: str, dom_: int) -> 'RECORD':
        self.input = float(input_)
        self.output = float(output_)
        self.sold_init = float(sold_init_)
        self.doc_id = doc_id_
        self.doc_type = doc_type_
        self.dom = int(dom_)
        # Calculate the sold_final value based on input/output
        self.sold_final = self.sold_init + self.input - self.output
        return self

class PAGE:
    def __init__(self) -> None:
        self.price: float = 0.0
        self.sold_init: float = 0.0
        self.sold_final: float = 0.0
        self.crtrecord: int = 0
        self.maxrecord: int = 0
        self.records: List[RECORD] = []
        self.sheet: Optional['SHEET'] = None

    def init(self, price_: float, sold_init_: float) -> 'PAGE':
        self.price = float(price_)
        self.sold_init = float(sold_init_)
        self.sold_final = float(sold_init_)
        self.crtrecord = 0
        self.maxrecord = 0
        return self

    def add_record(self, record: RECORD) -> RECORD:
        record.page = self
        self.records.append(record)
        self.maxrecord += 1
        self.crtrecord = self.maxrecord - 1
        # Update page's sold_final based on record
        self.sold_final = record.sold_final
        return record

    def create_record(self, input_: float, output_: float, sold_init_: float,
                    doc_id_: str, doc_type_: str, dom_: int) -> RECORD:
        new_record = RECORD()
        # For the first record, use the page's sold_init, otherwise use the previous record's sold_final
        current_sold_init = self.sold_init if self.maxrecord == 0 else self.sold_final
        new_record.init(input_, output_, 0, current_sold_init, doc_id_, doc_type_, dom_)
        return self.add_record(new_record)

    def select_record(self, index: int) -> bool:
        if 0 <= index < self.maxrecord:
            self.crtrecord = index
            return True
        return False

class SHEET:
    def __init__(self) -> None:
        self.year: int = 2025
        self.month: int = 1
        self.crtpage: int = 0
        self.maxpage: int = 0
        self.pages: List[PAGE] = []
        self.product: Optional['PRODUCT'] = None

    def init(self, year_: int = 2025, month_: int = 1) -> 'SHEET':
        self.year = int(year_)
        self.month = int(month_)
        self.crtpage = 0
        self.maxpage = 0
        return self

    def create_page(self, price: float, sold_init: float) -> PAGE:
        new_page = PAGE()
        new_page.sheet = self
        new_page.init(price, sold_init)
        self.pages.append(new_page)
        self.maxpage += 1
        self.crtpage = self.maxpage - 1
        return new_page

    def select_page(self, index: int) -> bool:
        if 0 <= index < self.maxpage:
            self.crtpage = index
            return True
        return False

class PRODUCT:
    def __init__(self) -> None:
        self.name: str = ""
        self.unit: str = ""
        self.crtsheet: int = 0
        self.maxsheet: int = 0
        self.sheets: List[SHEET] = []
        self.database: Optional['DATABASE'] = None

    def init(self, name_: str, unit_: str) -> 'PRODUCT':
        self.name = str(name_)
        self.unit = str(unit_)
        self.crtsheet = 0
        self.maxsheet = 0
        return self

    def create_sheet(self, year: int = 2025, month: int = 4) -> SHEET:
        new_sheet = SHEET()
        new_sheet.product = self
        new_sheet.init(year, month)
        self.sheets.append(new_sheet)
        self.maxsheet += 1
        self.crtsheet = self.maxsheet - 1
        return new_sheet

    def select_sheet(self, index: int) -> bool:
        if 0 <= index < self.maxsheet:
            self.crtsheet = index
            return True
        return False

class DATABASE:
    def __init__(self) -> None:
        self.crtproduct: int = 0
        self.maxproduct: int = 0
        self.products: List[PRODUCT] = []

    def init(self) -> 'DATABASE':
        self.crtproduct = 0
        self.maxproduct = 0
        return self

    def create_product(self, name: str, unit: str) -> PRODUCT:
        new_product = PRODUCT()
        new_product.database = self
        new_product.init(name, unit)
        self.products.append(new_product)
        self.maxproduct += 1
        self.crtproduct = self.maxproduct - 1
        return new_product

    def select_product(self, index: int) -> bool:
        if 0 <= index < self.maxproduct:
            self.crtproduct = index
            return True
        return False

# Initialize database
db: DATABASE = DATABASE()
db.init()