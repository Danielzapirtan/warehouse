# Database implementation with improvements
class RECORD:
    def __init__(self):
        self.input = 0.0
        self.output = 0.0
        self.sold_final = 0.0
        self.sold_init = 0.0
        self.doc_id = ''
        self.doc_type = ''
        self.dom = 0
        self.page = None

    def init(self, input_, output_, sold_final_, sold_init_, doc_id_, doc_type_, dom_):
        # Fixed tuple assignment bug by removing commas
        self.input = float(input_)
        self.output = float(output_)
        self.sold_final = float(sold_final_)
        self.sold_init = float(sold_init_)
        self.doc_id = doc_id_
        self.doc_type = doc_type_
        self.dom = int(dom_)
        # Calculate the sold_final value based on input/output
        self.sold_final = self.sold_init + self.input - self.output
        return self

class PAGE:
    def __init__(self):
        self.price = 0.0
        self.sold_init = 0.0
        self.sold_final = 0.0
        self.crtrecord = 0
        self.maxrecord = 0
        self.records = []  # Using dynamic list instead of fixed array
        self.sheet = None

    def init(self, price_, sold_init_):
        self.price = float(price_)
        self.sold_init = float(sold_init_)
        self.sold_final = float(sold_init_)
        self.crtrecord = 0
        self.maxrecord = 0
        return self

    def add_record(self, record):
        record.page = self
        self.records.append(record)
        self.maxrecord += 1
        self.crtrecord = self.maxrecord - 1
        # Update page's sold_final based on record
        self.sold_final = record.sold_final
        return record

    def create_record(self, input_, output_, sold_init_, doc_id_, doc_type_, dom_):
        new_record = RECORD()
        # Use current sold_final as the new record's sold_init if there are existing records
        current_sold_init = self.sold_final if self.maxrecord > 0 else sold_init_
        new_record.init(input_, output_, 0, current_sold_init, doc_id_, doc_type_, dom_)
        return self.add_record(new_record)

    def select_record(self, index):
        if 0 <= index < self.maxrecord:
            self.crtrecord = index
            return True
        return False

class SHEET:
    def __init__(self):
        self.year = 2025
        self.month = 1
        self.crtpage = 0
        self.maxpage = 0
        self.pages = []  # Using dynamic list instead of fixed array
        self.product = None

    def init(self, year_=2025, month_=1):
        self.year = int(year_)
        self.month = int(month_)
        self.crtpage = 0
        self.maxpage = 0
        return self

    def create_page(self, price, sold_init):
        new_page = PAGE()
        new_page.sheet = self
        new_page.init(price, sold_init)
        self.pages.append(new_page)
        self.maxpage += 1
        self.crtpage = self.maxpage - 1
        return new_page

    def select_page(self, index):
        if 0 <= index < self.maxpage:
            self.crtpage = index
            return True
        return False

class PRODUCT:
    def __init__(self):
        self.name = ""
        self.unit = ""
        self.crtsheet = 0
        self.maxsheet = 0
        self.sheets = []  # Using dynamic list instead of fixed array
        self.database = None

    def init(self, name_, unit_):
        self.name = str(name_)
        self.unit = str(unit_)
        self.crtsheet = 0
        self.maxsheet = 0
        return self

    def create_sheet(self, year=2025, month=4):
        new_sheet = SHEET()
        new_sheet.product = self
        new_sheet.init(year, month)
        self.sheets.append(new_sheet)
        self.maxsheet += 1
        self.crtsheet = self.maxsheet - 1
        return new_sheet

    def select_sheet(self, index):
        if 0 <= index < self.maxsheet:
            self.crtsheet = index
            return True
        return False

class DATABASE:
    def __init__(self):
        self.crtproduct = 0
        self.maxproduct = 0
        self.products = []  # Using dynamic list instead of fixed array

    def init(self):
        self.crtproduct = 0
        self.maxproduct = 0
        return self

    def create_product(self, name, unit):
        new_product = PRODUCT()
        new_product.database = self
        new_product.init(name, unit)
        self.products.append(new_product)
        self.maxproduct += 1
        self.crtproduct = self.maxproduct - 1
        return new_product

    def select_product(self, index):
        if 0 <= index < self.maxproduct:
            self.crtproduct = index
            return True
        return False

# Initialize database
db = DATABASE()
db.init()
