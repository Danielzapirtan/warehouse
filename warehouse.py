from typing import Optional, List, Callable, Any

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
        
        # Trigger update propagation if attached to a page
        if self.page:
            self.page._update_totals()
        
        return self

    def update_values(self, input_: Optional[float] = None, output_: Optional[float] = None, 
                     doc_id_: Optional[str] = None, doc_type_: Optional[str] = None, 
                     dom_: Optional[int] = None) -> None:
        """Update record values and propagate changes"""
        if input_ is not None:
            self.input = float(input_)
        if output_ is not None:
            self.output = float(output_)
        if doc_id_ is not None:
            self.doc_id = doc_id_
        if doc_type_ is not None:
            self.doc_type = doc_type_
        if dom_ is not None:
            self.dom = int(dom_)
        
        # Recalculate sold_final
        self.sold_final = self.sold_init + self.input - self.output
        
        # Propagate changes up the hierarchy
        if self.page:
            self.page._update_totals()

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
        
        # Update page totals instead of just assigning
        self._update_totals()
        return record

    def _update_totals(self) -> None:
        """Update page totals based on all records and propagate changes"""
        if self.records:
            # The final sold amount should be the last record's sold_final
            self.sold_final = self.records[-1].sold_final
        else:
            self.sold_final = self.sold_init
        
        # Propagate changes to sheet level
        if self.sheet:
            self.sheet._update_totals()

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

    def remove_record(self, index: int) -> bool:
        """Remove a record and update totals"""
        if 0 <= index < self.maxrecord:
            self.records.pop(index)
            self.maxrecord -= 1
            if self.crtrecord >= self.maxrecord and self.maxrecord > 0:
                self.crtrecord = self.maxrecord - 1
            elif self.maxrecord == 0:
                self.crtrecord = 0
            
            # Recalculate all records' sold_init and sold_final values
            self._recalculate_records()
            self._update_totals()
            return True
        return False

    def _recalculate_records(self) -> None:
        """Recalculate all records after a change in sequence"""
        current_sold = self.sold_init
        for record in self.records:
            record.sold_init = current_sold
            record.sold_final = record.sold_init + record.input - record.output
            current_sold = record.sold_final

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
        
        # Propagate changes to product level
        self._update_totals()
        return new_page

    def _update_totals(self) -> None:
        """Update sheet totals and propagate to product level"""
        # Propagate changes to product level
        if self.product:
            self.product._update_totals()

    def select_page(self, index: int) -> bool:
        if 0 <= index < self.maxpage:
            self.crtpage = index
            return True
        return False

    def remove_page(self, index: int) -> bool:
        """Remove a page and update totals"""
        if 0 <= index < self.maxpage:
            self.pages.pop(index)
            self.maxpage -= 1
            if self.crtpage >= self.maxpage and self.maxpage > 0:
                self.crtpage = self.maxpage - 1
            elif self.maxpage == 0:
                self.crtpage = 0
            
            self._update_totals()
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
        
        # Propagate changes to database level
        self._update_totals()
        return new_sheet

    def _update_totals(self) -> None:
        """Update product totals and propagate to database level"""
        # Propagate changes to database level
        if self.database:
            self.database._notify_change('product_updated', self)

    def select_sheet(self, index: int) -> bool:
        if 0 <= index < self.maxsheet:
            self.crtsheet = index
            return True
        return False

    def remove_sheet(self, index: int) -> bool:
        """Remove a sheet and update totals"""
        if 0 <= index < self.maxsheet:
            self.sheets.pop(index)
            self.maxsheet -= 1
            if self.crtsheet >= self.maxsheet and self.maxsheet > 0:
                self.crtsheet = self.maxsheet - 1
            elif self.maxsheet == 0:
                self.crtsheet = 0
            
            self._update_totals()
            return True
        return False

    def update_info(self, name_: Optional[str] = None, unit_: Optional[str] = None) -> None:
        """Update product information and notify changes"""
        if name_ is not None:
            self.name = str(name_)
        if unit_ is not None:
            self.unit = str(unit_)
        
        if self.database:
            self.database._notify_change('product_updated', self)

class DATABASE:
    def __init__(self) -> None:
        self.crtproduct: int = 0
        self.maxproduct: int = 0
        self.products: List[PRODUCT] = []
        self._observers: List[Callable[[str, Any], None]] = []

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
        
        # Notify observers of new product
        self._notify_change('product_added', new_product)
        return new_product

    def select_product(self, index: int) -> bool:
        if 0 <= index < self.maxproduct:
            self.crtproduct = index
            self._notify_change('product_selected', self.products[index])
            return True
        return False

    def remove_product(self, index: int) -> bool:
        """Remove a product and notify observers"""
        if 0 <= index < self.maxproduct:
            removed_product = self.products.pop(index)
            self.maxproduct -= 1
            if self.crtproduct >= self.maxproduct and self.maxproduct > 0:
                self.crtproduct = self.maxproduct - 1
            elif self.maxproduct == 0:
                self.crtproduct = 0
            
            self._notify_change('product_removed', removed_product)
            return True
        return False

    def add_observer(self, callback: Callable[[str, Any], None]) -> None:
        """Add an observer for database changes"""
        self._observers.append(callback)

    def remove_observer(self, callback: Callable[[str, Any], None]) -> None:
        """Remove an observer"""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_change(self, event_type: str, data: Any) -> None:
        """Notify all observers of changes"""
        for observer in self._observers:
            try:
                observer(event_type, data)
            except Exception as e:
                print(f"Error notifying observer: {e}")

    def get_current_product(self) -> Optional[PRODUCT]:
        """Get the currently selected product"""
        if 0 <= self.crtproduct < self.maxproduct:
            return self.products[self.crtproduct]
        return None

    def get_current_sheet(self) -> Optional[SHEET]:
        """Get the currently selected sheet from current product"""
        product = self.get_current_product()
        if product and 0 <= product.crtsheet < product.maxsheet:
            return product.sheets[product.crtsheet]
        return None

    def get_current_page(self) -> Optional[PAGE]:
        """Get the currently selected page from current sheet"""
        sheet = self.get_current_sheet()
        if sheet and 0 <= sheet.crtpage < sheet.maxpage:
            return sheet.pages[sheet.crtpage]
        return None

    def get_current_record(self) -> Optional[RECORD]:
        """Get the currently selected record from current page"""
        page = self.get_current_page()
        if page and 0 <= page.crtrecord < page.maxrecord:
            return page.records[page.crtrecord]
        return None

# Initialize database
db: DATABASE = DATABASE()
db.init()

# Example usage of observer pattern:
def ui_update_handler(event_type: str, data: Any) -> None:
    """Example handler for UI updates"""
    print(f"UI Update: {event_type} - {data}")
    # Here you would update your UI components
    # For example:
    # - Refresh product list
    # - Update current selection
    # - Recalculate totals
    # - Update charts/graphs

# Register the UI handler
db.add_observer(ui_update_handler)