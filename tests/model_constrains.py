model_constrains = {
    "date": " 19/12/2023, 21-12-2023",
    "nameOfItem": "Dell Latitude 5440 laptop, 8GB RAM, 512GB SSD   \t\n",
    "invoice": "F/174/06/2023",
    "issuer": "\"STATIM LLC\" Peter Pan, 123456789 ",
    "value": "1537.99",
    "materialDutyPerson": "GDPR         \n\n     ",
    "psp": "0801-D111-00003-01 ",
    "costCenter": "    1110300   ",
    "inventoryNumber": "           487-T-1110300-111100140070",
    "invoiceDate": None,
}

expected_data = {
    'date': '19-12-2023',
    'name_of_item': 'Dell Latitude 5440 laptop, 8GB RAM, 512GB SSD',
    'invoice': 'F/174/06/2023',
    'issuer': '"STATIM LLC" Peter Pan, 123456789',
    'value': '1537.99',
    'material_duty_person': 'GDPR',
    'psp': '0801-D111-00003-01',
    'cost_center': '1110300',
    'inventory_number': '487-T-1110300-111100140070',
    'invoice_date': None,
}

document_constraints = {
    'document_name_unit': '',
    'document_name_serial': '123456',
    'fixed_asset': model_constrains,
}
