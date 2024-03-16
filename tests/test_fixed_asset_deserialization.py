from json import dumps

from pydantic import ValidationError

from ..register.models import FixedAsset


model_constrains = {
    "date": " 19/12/2023, 21-12-2023",
    "nameOfItem": "Dell Latitude 5440 laptop, 8GB RAM, 512GB SSD   \t\n",
    "invoice": "F/174/06/2023",
    "invoiceDate": "30.06.2023 (13.07.2023)",
    "issuer": "\"STATIM LLC\" Peter Pan, 123456789 ",
    "value": "1537.99",
    "materialDutyPerson": "GDPR         \n\n     ",
    "psp": "0801-D111-00003-01 ",
    "costCenter": "    1110300   ",
    "inventoryNumber": "           487-T-1110300-111100140070"
}

expected_data = {
    'date': '19-12-2023',
    'name_of_item': 'Dell Latitude 5440 laptop, 8GB RAM, 512GB SSD',
    'invoice': 'F/174/06/2023',
    'invoice_date': '30-06-2023',
    'issuer': '"STATIM LLC" Peter Pan, 123456789',
    'value': '1537.99',
    'material_duty_person': 'GDPR',
    'psp': '0801-D111-00003-01',
    'cost_center': '1110300',
    'inventory_number': '487-T-1110300-111100140070'
}

def test_model_deserialization():
    """
    Tests if model is deserialized correctly
    """
    fixed_asset = FixedAsset.model_validate(model_constrains)
    assert fixed_asset.model_dump() == expected_data

def test_model_deserialization_json():
    """
    Tests if json is deserialized correctly
    """
    model_constrains_json = dumps(model_constrains)
    fixed_asset = FixedAsset.model_validate_json(model_constrains_json)
    assert fixed_asset.model_dump() == expected_data

def test_model_deserialization_with_extra_field_added():
    """
    Here we only check if the deserialization fails with an extra field
    added to the model. Earlier, in the FixedAsset's ConficDict we
    supressed any extra data.
    """
    model_constrains_with_extra_field_added = expected_data.copy()
    model_constrains_with_extra_field_added.update({
        'extra': 'extra field added',
    })
    try:
        FixedAsset.model_validate(model_constrains_with_extra_field_added)
    except ValidationError:
        assert True
