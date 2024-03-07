from typing import cast

from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from ..register.workbook import obtain_last_data_column_from_worksheet

def test_last_column_in_workshhet():
    '''
    Test if returned value is 3, as function
    "obtain_last_data_column_from_worksheet" is counting from 1,
    and we want only the named columns.
    '''
    row: tuple[str, str, str, None] = ('Cell 1', 'Cell 2', 'Cell 3', None)
    wb: Workbook = Workbook()
    sheet: Worksheet = cast(Worksheet, wb.active)
    sheet.append(row)

    got: int = obtain_last_data_column_from_worksheet(cast(Worksheet, sheet))
    assert got == 3
