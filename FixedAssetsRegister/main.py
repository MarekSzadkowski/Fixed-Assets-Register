#! /usr/bin/env python3

from curses.ascii import isdigit
from datetime import datetime
from os import _exit
from pickle import dump, load
from typing import Any, cast

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
import click

from models import App_Settings, FixedAsset, FixedAssetDocument


def exit_with_info(info: str, do_exit=True) -> None:
    print(info)
    if do_exit:
        _exit(1)

def get_app_settings() -> App_Settings:
    app_settings = App_Settings()

    if app_settings.wb_filename == '':
        files = app_settings.list_files()
        app_settings.wb_filename = files[1]
    return app_settings

def get_wordbook(filename) -> Workbook | None:
    '''Loads an Excel file from the given location on disk'''

    try:
        return load_workbook(filename, read_only=True)
    except FileNotFoundError:
        exit_with_info(
            f'Cannot find {filename}.\nPlease check your settings.')

def obtain_cell_values_from_wordbook(wb: Workbook, max_col) -> list:
    '''Returns cell values from given dimensions'''

    sheet: Worksheet = cast(Worksheet, wb.active)
    return list(sheet.iter_rows(2, max_col=max_col, values_only=True))

def obtain_last_column_from_worksheet(sheet: Worksheet) -> int:
    row = next(sheet.iter_rows(1, 1, 1, values_only=True), None)

    if row:  # if row is not None:
        for index, col in enumerate(row, 1):
            if col is None:
                return index
    return 0

def skip_on_pattern(value: str) -> bool:
    '''
    True if data belongs to a group that makes an asset - marked as 'do '
    '''
    return value[:3] == 'do '

def create_document_name(row: tuple) -> str | None:
    '''
    Unit and six last digits from the inventory number.
    Returns None if serial contains something else than digits, as it means
    uncomplete stuff - something is currently being built and it costs are
    not known yet.
    '''
    if row[2] is not None:
        serial = row[2][-6:]
        for char in serial:
            if not isdigit(char):
                return None
        return (row[12], serial)

def fix_date(_date: Any) -> str:
    if _date is None:
        _date = ''
    else:
        try:
            _date = _date.strftime('%d-%m-%Y')
        except AttributeError:
            # date may be given as string not complying the actual
            # standards i.e as 'date,date' in this case the former is taken.
            _date = _date.strip()
            if ',' in _date:
                _date, sparse =_date.replace(' ', '').split(',')
            if ' ' in _date:
                _date, sparse = _date.split(' ')
    return _date

def financial_cost_values(financial_source: str) -> list[str, str] | None:
    '''
    Returns a list of psp and cost_center elements if financial_source is found
    in the dictionary below. None oterwise.
    '''
    financial_sources = {
        '550-D111-00-1110000': {'psp': '0801-D111-00011-01', 'cost_center': '1110000'},
        '550-D111-00-1110002': {'psp': '0801-D111-00011-01', 'cost_center': '1110002'},
        '550-D111-00-1110003': {'psp': '0801-D111-00011-01', 'cost_center': '1110003'},
        '550-D111-00-1110100': {'psp': '0801-D111-00011-01', 'cost_center': '1110100'},
        '550-D111-00-1110102': {'psp': '0801-D111-00011-01', 'cost_center': '1110102'},
        '550-D111-00-1110103': {'psp': '0801-D111-00011-01', 'cost_center': '1110103'},
        '550-D111-00-1110104': {'psp': '0801-D111-00011-01', 'cost_center': '1110104'},
        '550-D111-00-1110105': {'psp': '0801-D111-00011-01', 'cost_center': '1110105'},
        '550-D111-00-1110108': {'psp': '0801-D111-00011-01', 'cost_center': '1110108'},
        '550-D111-00-1110109': {'psp': '0801-D111-00011-01', 'cost_center': '1110109'},
        '550-D111-00-1110111': {'psp': '0801-D111-00011-01', 'cost_center': '1110111'},
        '550-D111-00-1110112': {'psp': '0801-D111-00011-01', 'cost_center': '1110112'},
        '550-D111-00-1110113': {'psp': '0801-D111-00011-01', 'cost_center': '1110113'},
        '550-D111-00-1110114': {'psp': '0801-D111-00011-01', 'cost_center': '1110114'},
        '550-D111-00-1110115': {'psp': '0801-D111-00011-01', 'cost_center': '1110115'},
        '550-D111-00-1110116': {'psp': '0801-D111-00011-01', 'cost_center': '1110116'},
        '550-D111-00-1110119': {'psp': '0801-D111-00011-01', 'cost_center': '1110119'},
        '550-D111-00-1110200': {'psp': '0801-D111-00011-01', 'cost_center': '1110200'},
        '550-D111-00-1110300': {'psp': '0801-D111-00011-01', 'cost_center': '1110300'},
        '550-D111-00-1112000': {'psp': '0801-D111-00011-01', 'cost_center': '1112000'},
        '550-D111-00-1113300': {'psp': '0801-D111-00011-01', 'cost_center': '1113300'},
        '550-D111-00-1114000': {'psp': '0801-D111-00011-01', 'cost_center': '1114000'},
        '550-D111-00-1115100': {'psp': '0801-D111-00011-01', 'cost_center': '1115100'},
        '550-D111-00-1119000': {'psp': '0801-D111-00011-01', 'cost_center': '1119000'},
        '550-D111-00-1119004': {'psp': '0801-D111-00011-01', 'cost_center': '1119004'},
        '550-D111-00-1119801': {'psp': '0801-D111-00011-01', 'cost_center': '1119801'},
        '550-D111-00-1119802': {'psp': '0801-D111-00011-01', 'cost_center': '1119802'},
        '501-D111-01-1110000': {'psp': '0801-D111-50101-01', 'cost_center': '1110000'},
        '501-D111-01-1110002': {'psp': '0801-D111-50101-01', 'cost_center': '1110002'},
        '501-D111-01-1110003': {'psp': '0801-D111-50101-01', 'cost_center': '1110003'},
        '501-D111-01-1110100': {'psp': '0801-D111-50101-01', 'cost_center': '1110100'},
        '501-D111-01-1110102': {'psp': '0801-D111-50101-01', 'cost_center': '1110102'},
        '501-D111-01-1110103': {'psp': '0801-D111-50101-01', 'cost_center': '1110103'},
        '501-D111-01-1110104': {'psp': '0801-D111-50101-01', 'cost_center': '1110104'},
        '501-D111-01-1110105': {'psp': '0801-D111-50101-01', 'cost_center': '1110105'},
        '501-D111-01-1110108': {'psp': '0801-D111-50101-01', 'cost_center': '1110108'},
        '501-D111-01-1110109': {'psp': '0801-D111-50101-01', 'cost_center': '1110109'},
        '501-D111-01-1110111': {'psp': '0801-D111-50101-01', 'cost_center': '1110111'},
        '501-D111-01-1110112': {'psp': '0801-D111-50101-01', 'cost_center': '1110112'},
        '501-D111-01-1110113': {'psp': '0801-D111-50101-01', 'cost_center': '1110113'},
        '501-D111-01-1110114': {'psp': '0801-D111-50101-01', 'cost_center': '1110114'},
        '501-D111-01-1110115': {'psp': '0801-D111-50101-01', 'cost_center': '1110115'},
        '501-D111-01-1110116': {'psp': '0801-D111-50101-01', 'cost_center': '1110116'},
        '501-D111-01-1110119': {'psp': '0801-D111-50101-01', 'cost_center': '1110119'},
        '501-D111-01-1110200': {'psp': '0801-D111-50101-01', 'cost_center': '1110200'},
        '501-D111-01-1110300': {'psp': '0801-D111-50101-01', 'cost_center': '1110300'},
        '501-D111-01-1112000': {'psp': '0801-D111-50101-01', 'cost_center': '1112000'},
        '501-D111-01-1113300': {'psp': '0801-D111-50101-01', 'cost_center': '1113300'},
        '501-D111-01-1114000': {'psp': '0801-D111-50101-01', 'cost_center': '1114000'},
        '501-D111-01-1115100': {'psp': '0801-D111-50101-01', 'cost_center': '1115100'},
        '501-D111-01-1119000': {'psp': '0801-D111-50101-01', 'cost_center': '1119000'},
        '501-D111-01-1119004': {'psp': '0801-D111-50101-01', 'cost_center': '1119004'},
        '501-D111-01-1119801': {'psp': '0801-D111-50101-01', 'cost_center': '1119801'},
        '501-D111-01-1119802': {'psp': '0801-D111-50101-01', 'cost_center': '1119802'},
        '500-D111-01-1110000': {'psp': '0801-D111-00003-01', 'cost_center': '1110000'},
        '500-D111-01-1110002': {'psp': '0801-D111-00003-01', 'cost_center': '1110002'},
        '500-D111-01-1110003': {'psp': '0801-D111-00003-01', 'cost_center': '1110003'},
        '500-D111-01-1110100': {'psp': '0801-D111-00003-01', 'cost_center': '1110100'},
        '500-D111-01-1110102': {'psp': '0801-D111-00003-01', 'cost_center': '1110102'},
        '500-D111-01-1110103': {'psp': '0801-D111-00003-01', 'cost_center': '1110103'},
        '500-D111-01-1110104': {'psp': '0801-D111-00003-01', 'cost_center': '1110104'},
        '500-D111-01-1110105': {'psp': '0801-D111-00003-01', 'cost_center': '1110105'},
        '500-D111-01-1110108': {'psp': '0801-D111-00003-01', 'cost_center': '1110108'},
        '500-D111-01-1110109': {'psp': '0801-D111-00003-01', 'cost_center': '1110109'},
        '500-D111-01-1110111': {'psp': '0801-D111-00003-01', 'cost_center': '1110111'},
        '500-D111-01-1110112': {'psp': '0801-D111-00003-01', 'cost_center': '1110112'},
        '500-D111-01-1110113': {'psp': '0801-D111-00003-01', 'cost_center': '1110113'},
        '500-D111-01-1110114': {'psp': '0801-D111-00003-01', 'cost_center': '1110114'},
        '500-D111-01-1110115': {'psp': '0801-D111-00003-01', 'cost_center': '1110115'},
        '500-D111-01-1110116': {'psp': '0801-D111-00003-01', 'cost_center': '1110116'},
        '500-D111-01-1110119': {'psp': '0801-D111-00003-01', 'cost_center': '1110119'},
        '500-D111-01-1110200': {'psp': '0801-D111-00003-01', 'cost_center': '1110200'},
        '500-D111-01-1110300': {'psp': '0801-D111-00003-01', 'cost_center': '1110300'},
        '500-D111-01-1112000': {'psp': '0801-D111-00003-01', 'cost_center': '1112000'},
        '500-D111-01-1113300': {'psp': '0801-D111-00003-01', 'cost_center': '1113300'},
        '500-D111-01-1114000': {'psp': '0801-D111-00003-01', 'cost_center': '1114000'},
        '500-D111-01-1115100': {'psp': '0801-D111-00003-01', 'cost_center': '1115100'},
        '500-D111-01-1119000': {'psp': '0801-D111-00003-01', 'cost_center': '1119000'},
        '500-D111-01-1119004': {'psp': '0801-D111-00003-01', 'cost_center': '1119004'},
        '500-D111-01-1119801': {'psp': '0801-D111-00003-01', 'cost_center': '1119801'},
        '500-D111-01-1119802': {'psp': '0801-D111-00003-01', 'cost_center': '1119802'},
        'pozostałość śr. budżetowych z lat ubiegłych':
            {'psp': '0801-D111-00110-01', 'cost_center': ''},
        '500-12/Twórcy ': {'psp': '0801-D111-00010-01', 'cost_center': '1110000'},
        '500-D111-12-1119000': {'psp': '0801-D111-00100-01', 'cost_center': '1119000'},
        '501-D111-20-': {'psp': '0801-D111-50120-01', 'cost_center': '1110000'},
    }
    if financial_source in financial_sources:
        return [
            financial_sources[financial_source]['psp'],
            financial_sources[financial_source]['cost_center'],
        ]
    else:
        return None

def create_fixed_asset(row: tuple[Any]) -> FixedAsset:
    '''
    If financial source (row[3]) is given (which is mostly true),
    it is translated to psp and cost_center repectivly
    '''
    if row[3] is None:
        psp = cost_center = ''
    else:
        source = financial_cost_values(row[3])
        if source is None:
            psp = cost_center = str(row[3])
        else:
            psp, cost_center = source

    return FixedAsset(
        date=fix_date(row[11]),
        name_of_item=row[6],
        invoice=str(row[4]),
        invoice_date=fix_date(row[5]),
        issuer=str(row[10]),
        value=str(row[8]),
        material_duty_person=str(row[13]),
        psp=psp,
        cost_center=cost_center,
        inventory_number=row[2],
    )

def select_fixed_asset_elements(rows: list[tuple]) -> list[tuple, FixedAsset]:
    '''
    The wordbook I was given had foliwong 16 columns:
    #. ordinal number: it represents an invoice or a group of them,
       may repeat itself many times,
       may also be skipped, AFTER it has been specified once.
    #. unused here
    #. inventory number
    #. financial source - probably the most important column in thw wordbook,
       as it constitutes the fields of psp and cost_center.
    #. invoice number
    #. invoice date
    #. name of a product/asset
    #. quantity (uusally 1)
    #. price
    #. value of the two above (formula), only this column is used here
    #. producent/supplier
    #. registering date - when the asset was accepted to the register
    #. unit - the devision an asset belongs to
    #. materia duty person
    #. 15-16 unused here
    '''
    selected_elements = []
    for i, row in enumerate(rows):
        if row[0] is None or row[2] is None:
            continue
        if skip_on_pattern(row[2]) and i > 0 and row[0] == rows[i - 1][0]:
                continue

        fix_asset_name_tuple = create_document_name(row)
        if fix_asset_name_tuple is not None:
            try:
                fixed_asset = create_fixed_asset(row)
            except TypeError:
                # shouldn,t happen but it's a good way to find
                # data which might cause a problem
                fixed_asset = None
            selected_elements.append([fix_asset_name_tuple, fixed_asset])
    return selected_elements

def check_serials(elemets: list[tuple, FixedAsset]) -> list[FixedAsset] | None:
    '''
    Returns None if all serials are unique, otherwise a list
    of doubled elements.
    '''
    # Well, it appeared I got wrong data on entry, it's unreliable though!
    return []

    serials = set()
    for t, fa in elemets:
        unit, serial = t
        if serial is None or serial == '':
            pass
        serials.add(serial)
    # return None
    # return elemets

def read_wordbook_data() -> list[tuple]:
    app_settings = App_Settings()
    wordbook: Workbook = get_wordbook(app_settings.wb_filename)  # type: ignore
    rows = obtain_cell_values_from_wordbook(wordbook, app_settings.last_column)
    wordbook.close()
    return rows

def process_workbook_data(rows: list[tuple]) -> None:
    '''
    Imports selected data from a wordbook and stores it
    in a pickle DB file,
    '''
    selected_items = select_fixed_asset_elements(rows)
    serials = check_serials(selected_items)
    if serials:
        [print(s) for s in serials]
        exit_with_info('')
    else:
        with open('fixed_assets.db', 'wb') as stream:
            dump(selected_items, stream)

def load_fixed_assets() -> list[FixedAsset]:
    try:
        with open('fixed_assets.db', 'rb') as reader:
            fixed_assets = load(reader, encoding='utf-8')
    except FileNotFoundError:
        exit_with_info('File \'fixed_assets.db\' cannot be opened.')
    if fixed_assets is None:
        return []
    else:
        return fixed_assets

def print_fixed_assets(fixed_assets: list[FixedAsset]) -> None:
    for t, fa in fixed_assets:
        print(f'{t[0]}-{t[1]}\n', fa)

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    '''
    This allows to use our proggie w/o any parameter,
    specyfying the default one.
    '''
    if ctx.invoked_subcommand is None:
        report()

@cli.command()
def wb() -> None:
    '''
    Imports wordbook data to a simple DB (pickle)
    '''
    wordbook_data = read_wordbook_data()
    process_workbook_data(wordbook_data)

@cli.command()
def report():
    fixed_assets = load_fixed_assets()
    print_fixed_assets(fixed_assets)

@cli.command()
def fa() -> None:
    '''
    Still to do - throws an error ATM
    '''
    fixed_assets = load_fixed_assets()
    for t, fa in fixed_assets:
        try:
            fa_document = FixedAssetDocument(**fa.__dict__, document_name=t)
        except Exception as e:
            exit_with_info(f'Error:\n{fa.model_dump()}\n{t}\n{e}')

        print(fa_document)

@cli.command()
def search(item: str) -> None:
    '''
    TODO
    '''
    fixed_assets = load_fixed_assets()

@cli.command()
def config():
    app_settings = get_app_settings()

    if app_settings.last_column == 0:
        wordbook: Workbook = get_wordbook(app_settings.wb_filename)  # type: ignore
        app_settings.last_column = obtain_last_column_from_worksheet(
            cast(Worksheet, wordbook.active))
    app_settings.save()

if __name__ == '__main__':
    cli()
