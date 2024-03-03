from datetime import datetime  # pylint: disable=unused-import
from itertools import islice
from pickle import dump, load
from re import match
from typing import Any

from pydantic import ValidationError

from .financial_sources import FINANCIAL_SOURCES
from .helpers import exit_with_info, user_input
from .models import AppSettings, BadDateFormat, FixedAsset, FixedAssetDocument
from .workbook import setup_workbook


FILE_DB = 'fixed_assets.db'
DATE_PATTERN = r'^\d{2}-\d{2}-\d{4}$'


def get_app_settings() -> AppSettings:
    """
    Returns the complete AppSettings object depending on users input.
    """
    try:
        app_settings = AppSettings()
    except ValidationError as e:
        exit_with_info(f'Error: {e}')

    files = app_settings.list_excel_files()
    if not files:
        exit_with_info('Cannot find any Excel file.')

    if app_settings.wb_filename is None:
        setup_workbook(app_settings, files)

    if app_settings.fa_filename is None:
        index = user_input(
            files,
            'Choose a file which is your fixed asset template you want to use',
        )
        app_settings.fa_filename = files[index]

    fa_path = user_input(
        app_settings.fa_path,
        'Enter the path where your fixed asset documents will be stored,\n'
        + 'currently set to: '
    )
    if fa_path not in {'', app_settings.fa_path}:
        app_settings.fa_path = fa_path

    app_settings.configured = True
    return app_settings

def skip_on_pattern(value: str) -> bool:
    """
    True if data belongs to a group that makes an asset - marked as 'do '

    Parameters:
    value (str): The current cell value.

    Returns:
    bool: True if data belongs to a group that makes an asset, False otherwise.
    """
    return value[:3] == 'do '

def get_serial(inventory_number: str) -> str | None:
    """
    Parameter:
    inventory_number from which the serial is derived,
    i.e. the last six digits from it.

    Returns None if serial contains something else than digits, as it means
    uncomplete stuff - something is currently being built and its costs are
    unknown yet.
    """
    serial = inventory_number[-6:]
    for char in serial:
        if not char.isdigit():
            return None
    return serial

def financial_cost_values(financial_source: str) -> list[str, str] | None:
    """
    Returns a list of psp and cost_center elements if financial_source is found
    in the FINANCIAL_SOURCES dictionary. None oterwise.
    """
    if financial_source in FINANCIAL_SOURCES:
        return [
            FINANCIAL_SOURCES[financial_source]['psp'],
            FINANCIAL_SOURCES[financial_source]['cost_center'],
        ]
    return None

def format_date(date: str) -> str:
    """
    Corrects the date format by removing any comma or space,
    replaces dots with dashes and returns the corrected date.

    Parameters:
    date (str): The input date string to be corrected.

    Returns:
    str: The corrected date string.
    """
    if ',' in date or ' ' in date:
        if ',' in date:
            date, _ = date.split(',')
        else:
            date, _ = date.split(' ')
    if '.' in date:
        date = date.replace('.', '-')
    return date

def fix_date(date: Any) -> str:
    """
    Usually date is a datetime object, but sometimes may be given
    as a string not complying with the actual standards, e.g. as
    'date, date' literals in this case the former literal is taken.

    Parameters:
    date (str | None): The input date string to be corrected.

    Returns:
    str: The corrected date string.
    """
    if date is None:
        date = ''
    else:
        try:
            date = date.strftime('%d-%m-%Y')
        except AttributeError as e:
            date_string = format_date(date.strip())
            date = match(DATE_PATTERN, date_string)
            if date is None:
                raise BadDateFormat(date) from e

            date = date.group()
    return date

def check_date(row: dict[str, int]) -> None:
    """
    Checks if the date is set correctly
    """
    try:
        row['date'] = fix_date(row['date'])
        row['invoice_date'] = fix_date(row['invoice_date'])
    except BadDateFormat as e:
        print(e)
        exit_with_info(
            'Please check your data for ordinal number: ' \
            + f'{row['ordinal_number']}')

def set_financial_source(row: dict[str, int]) -> bool:
    """
    If financial_source (row['financial_source']) is given (which is mostly true),
    it is translated to psp and cost_center repectivly.
    Sometimes financial_source may be given as a string however, if this is the
    case we chceck if the strng starts P. If it does, we return True.

    Parameters:
    row (dictionary): The current row of the Excel data.
    """
    financial_source = row['financial_source']
    if isinstance(financial_source, str) and financial_source[0] == 'P':
        return True

    if financial_source is None:
        row['psp'] = row['cost_center'] = ''
    else:
        source = financial_cost_values(financial_source)
        if source is None:
            row['psp'] = row['cost_center'] = str(financial_source)
        else:
            row['psp'], row['cost_center'] = source

    return False

def create_fixed_asset(row: dict[str, int]) -> FixedAsset:
    """
    Parameters:
    row (dictionary): The current row of the Excel data.

    Returns:
    FixedAsset: The created FixedAsset object.
    """
    # Sometimes financial_source is a very complex string, in such cases values
    # of 'invoice' and 'issuer' are usually not given, therefore None, which
    # needs fixing so the class' constructor didn't complain about it.
    if row['invoice'] is None:
        row['invoice'] = 'appendix'
    if row['issuer'] is None:
        row['issuer'] = 'appendix'

    construct_data = dict(islice(row.items(), 4, None))
    return FixedAsset.model_validate(construct_data)

def select_fixed_asset_documents(
        rows: list[dict[Any]]
    ) -> list[FixedAssetDocument]:
    """
    This is the most important function of this module. It takes
    all the previously remapped data from the workbook and creates
    a list of FixedAssetDocument objects.
    It also validates the data and skips rows which are currently
    not needed in the register.

    Parameters:
    rows (list of dictionaries).

    Returns:
    list: A list of FixedAssetDocument objects.
    """
    selected_elements = []
    for i, row in enumerate(rows, 1):
        ordinal_number = row['ordinal_number']
        inventory_number = row['inventory_number']

        if (ordinal_number is None or inventory_number is None
            or skip_on_pattern(inventory_number)
            and i > 1 and ordinal_number == rows[i - 1]['ordinal_number']):
            continue

        # Or maybe this below would be better:?
        # I asked the tinker about this, and it answered:
        #
        # if any((
        #     ordinal_number is None,
        #     inventory_number is None,
        #     skip_on_pattern(inventory_number),
        #     i > 1 and ordinal_number == rows[i - 1]['ordinal_number']
        # )):
        #     continue
        #
        # Personally I'd rather not.

        serial = get_serial(row['serial'])
        if serial is not None:
            row['serial'] = serial
            if set_financial_source(row):
                continue
            check_date(row)
            try:
                fixed_asset = create_fixed_asset(row)
            except ValidationError as e:
                print(f'Error in row {row['ordinal_number']}\n{row}:\n{e}')
                continue
            fa_document = FixedAssetDocument(
                document_name_unit=row['unit'],
                document_name_serial=serial,
                fixed_asset=fixed_asset
            )
            selected_elements.append(fa_document)
    return selected_elements

def check_serials(
        elemets: list[tuple, FixedAsset]
    ) -> list[FixedAsset] | None:
    """
    Returns None if all double_elements are unique, otherwise a list
    of doubled elements.
    """
    serials = {}
    for t, _ in elemets:
        _, serial = t
        serials[serial] = serials.get(serial, 0) + 1
    doubles = [[k, v] for k, v in serials.items() if v > 1]
    if len(doubles) > 0:
        return doubles
    return None

def print_double_elements(
        double_elements: list[list], selected_items: list
    ) -> None:
    print('The following serial numbers are repeated this number of times:')
    for d in double_elements:
        print(f'{d[0]}: {d[1]}')
        for t, fa in selected_items:
            u, s = t
            if s == d[0]:
                print(f'\t{u}\n{fa}')
    print('Please check your data and try again.')

def process_workbook_data(rows: list[tuple]) -> None:
    """
    Imports selected data from a workbook and stores it
    in a pickle DB file if there is no doubled elements (serials).
    The latter means error in the provided data, so no dump is done.
    """
    selected_items = select_fixed_asset_documents(rows)
    # double_elements = check_serials(selected_items)
    double_elements = None
    if double_elements:
        print_double_elements(double_elements, selected_items)
    else:
        with open(FILE_DB, 'wb') as stream:
            dump(selected_items, stream)

def load_fixed_assets() -> list[FixedAssetDocument]:
    try:
        with open(FILE_DB, 'rb') as reader:
            fixed_assets = load(reader, encoding='utf-8')
    except FileNotFoundError:
        exit_with_info(f'File \'{FILE_DB}\' cannot be opened.')
    if fixed_assets is None:
        return []
    else:
        return fixed_assets

def print_fixed_assets(
        fixed_assets_documents: list[FixedAssetDocument]
    ) -> None:
    print()
    # for ordinal, doc_name, fixed_asset in fixed_assets_documents:
    for document in fixed_assets_documents:
        # unit, serial = doc_name
        # print(f'{ordinal}, {unit}-{serial}\n', fixed_asset)
        print(document)

def create_fixed_asset_document(assets: list [FixedAsset], nr: int) -> None:
    for doc_name, ordinal, fixed_asset in assets:
        if ordinal == nr:
            try:
                fa_document = FixedAssetDocument(
                    # fixed_asset=fixed_asset,
                    document_name=doc_name)
            except AttributeError as e:
                exit_with_info(
                    f'Error:\n{fixed_asset.model_dump()}\n{doc_name}\n{e}'
                    )

    print(fa_document)
