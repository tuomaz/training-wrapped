from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P

def get_cell_text(cell):
    text_elements = []
    for element in cell.childNodes:
        if element.qname[1] == 'p':
            for text in element.childNodes:
                if text.nodeType == 3: # Text node
                    text_elements.append(str(text))
    return "".join(text_elements)

doc = load("Cykel 2019 - 2025.ods")
for sheet in doc.getElementsByType(Table):
    print(f"Sheet: {sheet.getAttribute('name')}")
    rows = sheet.getElementsByType(TableRow)
    for row in rows:
        cells = row.getElementsByType(TableCell)
        row_data = [get_cell_text(cell) for cell in cells]
        if "2025" in " ".join(row_data):
            print(row_data)
