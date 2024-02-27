from typing import cast

from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from ..FixedAssetsRegister.functions import obtain_last_column_from_worksheet

def test_last_column_in_workshhet():
    '''
    Test if returned value is 4, as function
    "obtain_last_column_from_worksheet" is counting from 1.
    '''
    row: tuple[str, str, str, None] = ('Cell 1', 'Cell 2', 'Cell 3', None)
    wb: Workbook = Workbook()
    sheet: Worksheet = cast(Worksheet, wb.active)
    sheet.append(row)

    got: int = obtain_last_column_from_worksheet(cast(Worksheet, sheet))
    assert got == 4
