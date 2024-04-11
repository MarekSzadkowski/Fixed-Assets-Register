from ..register.models import FixedAsset
from .model_constrains import model_constrains

def test_date_parsed_as_string():
    """
    Testing our date parser enclosed in FixedAsset model.
    Date can be passed as a datetime object or as a string.
    If it is a string it is passed as double date literal in a form
    of 'date, date' or 'date (date)'. Also may by given in dotted
    or slashed format, like '19.12.2023' or '19/12/2023'.
    What we want is '19-12-2023'.
    """
    fixed_asset = FixedAsset.model_validate(model_constrains)
    assert fixed_asset.date == '19-12-2023'

def test_english_date_as_string():
    model_constrains['date'] = '07.31.2023,11.19.2023'
    model_constrains['invoiceDate'] = '12/15/2007 (13.06.2017)'
    fixed_asset = FixedAsset.model_validate(model_constrains)
    assert fixed_asset.date == '07-31-2023'
    assert fixed_asset.invoice_date == '12-15-2007'
