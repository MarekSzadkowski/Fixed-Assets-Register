from itertools import islice
from multiprocessing import Pool
from pickle import dump, load
from re import match
from typing import Any

from pydantic import ValidationError

from .financial_sources import FINANCIAL_SOURCES
from .helpers import exit_with_info, user_input
from .models import AppSettings, FixedAsset, FixedAssetDocument
from .workbook import setup_workbook


FILE_DB = 'fixed_assets.db'


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
    'inventory_number' from which the serial is derived,
    i.e. the last six digits of it.

    Returns None if serial contains something else than digits, as it means
    incomplete stuff - something is currently being built and its costs are
    unknown yet, otherwise the matched string.
    """
    matched = match(r'^\d{6}$', inventory_number[-6:])
    if matched:
        return matched.string
    return None

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

def set_financial_source(row: dict[str, Any]) -> bool:
    """
    If financial_source (row['financial_source']) is given (which is mostly true),
    it is translated to psp and cost_center repectivly.
    Sometimes financial_source may be given as a string however, if this is the
    case we check if the strng starts with 'P' or 'p'.
    If it does, we return False - we don't need to create a FixedAsset document.

    Parameters:
    row (dictionary): The current row of the Excel data.

    Returns:
    bool: True if financial_source was set, False otherwise.
    """
    financial_source = row['financial_source']
    if isinstance(financial_source, str) and financial_source[0] == 'P':
        return False

    if financial_source is None:
        row['psp'] = row['cost_center'] = ''
    else:
        source = financial_cost_values(financial_source)
        if source is None:
            row['psp'] = row['cost_center'] = str(financial_source)
        else:
            row['psp'], row['cost_center'] = source

    return True

def create_fixed_asset(row: dict[str, Any]) -> FixedAsset:
    """
    Parameters:
    row (dictionary): The current row of the Excel data.

    Returns:
    FixedAsset: The created FixedAsset object.
    """
    fixed_asset = dict(islice(row.items(), 3, None))
    return FixedAsset.model_validate(fixed_asset)

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
    fixed_asset_documents = []
    for i, row in enumerate(rows, 1):
        ordinal_number = row['ordinal_number']
        inventory_number = row['inventory_number']

        if (ordinal_number is None or inventory_number is None
            or skip_on_pattern(inventory_number)
            and i > 1 and ordinal_number == rows[i - 1]['ordinal_number']):
            continue

        serial = get_serial(row['inventory_number'])
        if not serial or not set_financial_source(row):
            continue

        try:
            fixed_asset = create_fixed_asset(row)
        except ValidationError as e:
            exit_with_info(
                f'\nError at ordinal_number {row['ordinal_number']}:\n\n'
                + f'{e}:\n\n{row}'
            )
        fixed_asset_document = FixedAssetDocument(
            document_name_unit=row['unit'],
            document_name_serial=serial,
            fixed_asset=fixed_asset
        )

        fixed_asset_documents.append(fixed_asset_document)
    return fixed_asset_documents

def check_duplicated_serials(
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
    # if report:
    #     pass
        # print_report(report)

    # double_elements = check_duplicated_serials(selected_items)
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
        fixed_assets_documents: list[FixedAssetDocument],
        gdpr: bool = False,
    ) -> None:
    """
    Prints all data in the DB

    Parameters:
    fixed_assets_documents (list of FixedAssetDocument objects).
    gdpr (bool). If True, hide material duty person in the output,
    printing 'GDPR' - General Data Protection Regulation.
    """
    for document in fixed_assets_documents:
        print(
            f'{document.document_name_unit}-{document.document_name_serial}'
        )
        if gdpr:
            document.fixed_asset.material_duty_person = 'GDPR'
        print(document.fixed_asset.model_dump_json(by_alias=True, indent=2))

def generate_document(fixed_asset_document: FixedAssetDocument) -> None:
    try:
        fixed_asset_document.generate_document()
    except (
        FileNotFoundError,
        OSError,
        KeyboardInterrupt,
        ValueError,
    ) as e:
        raise RuntimeError(f'{e}') from e

def generate_fixed_asset_document(
        fixed_asset_documents: list[FixedAssetDocument],
        serial: str,
    ) -> None:
    """
    Makes the fixed asset document (Excel file) based on the passed serial.
    """
    if serial == '--all':
        documents_to_generate = fixed_asset_documents
    else:
        documents_to_generate = [
            document for document in fixed_asset_documents
            if document.document_name_serial == serial
        ]

    with Pool() as p:
        try:
            p.map(generate_document, documents_to_generate)
        except RuntimeError as e:
            p.terminate()
            exit_with_info(f'Error: {e}')

def get_app_settings() -> AppSettings:
    """
    Returns the complete AppSettings object depending on users input.
    """
    try:
        app_settings = AppSettings()
    except ValidationError as e:
        exit_with_info(f'Error: {e}')

    print('Please wait while your Excel files are being looked for...')
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
