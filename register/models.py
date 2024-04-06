from datetime import datetime  # pylint: disable=unused-import
from json import load, dump
from pathlib import Path
from re import match, split, sub
from typing import Any

from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl import load_workbook
from openpyxl.styles import Font

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    ValidationInfo,
)
from pydantic.alias_generators import to_camel


COMMITTEE = ['John Smith', 'Jane Doe']


class AppSettings(BaseModel):
    data_path: Path = Path.cwd()
    config_file: str = 'settings.txt'
    wb_filename: str | None = None
    fa_filename: str | None = None
    fa_path: str = 'FA_documents'
    last_column: int | None = None
    committee: list = Field(
        min_length=1,
        max_length=3,
        default=COMMITTEE
    )
    configured: bool = False

    def model_post_init(self, __context: Any) -> None:
        self.fa_path = str(self.data_path / self.fa_path)
        filename = self.data_path / self.config_file
        if Path.is_file(filename):
            with open(filename, encoding='utf-8') as config_file:
                config = load(config_file)

            self.__dict__.update(config)
            self.data_path = Path(config.get('data_path'))

    def list_excel_files(self) -> list[str] | None:
        path = self.data_path.home()
        elements = path.rglob('*.xlsx')
        return [str(e) for e in elements]

    def save(self):
        if  self.configured:
            filename = self.data_path / self.config_file
            json_dict = {
                "data_path": str(self.data_path),
                "config_file": self.config_file,
                "wb_filename": self.wb_filename,
                "fa_path": self.fa_path,
                "fa_filename": self.fa_filename,
                "last_column": self.last_column,
                "configured": self.configured,
            }
            try:
                with open(filename,'w', encoding='utf-8') as config_file:
                    dump(json_dict, config_file, indent=2)
            except OSError as e:
                print(f'Write error: ({e})')


DATE_PATTERN: str = r'^\d{2}-\d{2}-\d{4}$'


class FixedAsset(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        coerce_numbers_to_str=True,
        extra='forbid',
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    date: str
    name_of_item: str
    invoice: str
    issuer: str
    value: str
    material_duty_person: str
    psp: str
    cost_center: str
    inventory_number: str
    use_purpose: str
    serial_number: str
    id_vim: str
    invoice_date: str | None


    @field_validator('invoice', 'issuer', mode='before')
    @classmethod
    def parse_default(cls, value: Any) -> str:
        if value is None:
            return 'appendix'
        return value

    @field_validator('date',
                     'material_duty_person',
                     'use_purpose',
                     'serial_number',
                     'id_vim',
                     mode='before',
    )
    @classmethod
    def parse_value(cls, value: Any) -> str:
        if value is None:
            return ''
        return value

    @field_validator('date', 'invoice_date', mode='before')
    @classmethod
    def before_date_parser(cls, date: str) -> str:
        """
        Validates the 'date' and 'invoice_date' fields.

        This is the first step in the validation process as pydantic does it
        this way. Notece the mode='before' is used. Although this is the third
        'before' validator, it goes as the first - the order is important.

        Args:
            date, invoice_date (datetime): The datetime object to be validated.
            mode (str): The validation mode.

        Returns:
            str: The validated date value in the format 'dd-mm-yyyy'.
        """
        if isinstance(date, datetime):
            return date.strftime('%d-%m-%Y')
        return date

    @field_validator('date', 'invoice_date')
    @classmethod
    def after_date_parser(cls, value: str) -> str:
        """
        Usually excel's date is a datetime object, but sometimes may be given
        as a string not complying with the actual standards, e.g. as
        'date, date' literals. In this case the former one is taken.

        Parameters:
        date (str | None): The input date string to be corrected.

        Returns:
        str: The corrected date string.

        Raises:
        ValueError: If the date was given as a string but not
        in the correct format.
        """
        if value == '' or value is None:
            return value
        try:
            cls._parse_date(cls, value)
        except ValueError:
            date_string = cls._format_date(cls, value)
            date = match(DATE_PATTERN, date_string)
            try:
                return date.group()
            except AttributeError as e:
                raise ValueError(f'Invalid date format: {value}') from e
        return value

    @field_validator('cost_center')
    @classmethod
    def date_after_parser(
        cls,
        cost_center: str,
        validated_values: ValidationInfo
    ) -> str:
        """
        Sometimes financial_source is a very complex string, in such cases
        values of 'invoice' and 'issuer' are usually not given, therefore None,
        which needed fixing so the class' constructor wouldn't complain.
        Now we can check it again. We DO NOT have a value of financial_source,
        but we can check the value of cost_center, which in such cases is copied
        to the psp and cost_center fields.
        """
        values = validated_values.data
        if  'date' in values:
            if values['date'] == '' and ' ' not in cost_center:
                raise ValueError('Please specify date as DD-MM-YYYY')
        return cost_center

    def _parse_date(self, date_str: str) -> None:
        """
        Raises ValidationError if the date is not in the correct format.

        Parameters:
        date (str): The input date string to be checked.
        """
        if not match(DATE_PATTERN, date_str):
            raise ValueError(date_str)
        return date_str

    def _format_date(self, date_str: str) -> str:
        """
        Corrects the date format by removing any comma or space,
        replaces dots with dashes and returns the corrected date.

        Parameters:
        date (str): The input date string to be corrected.

        Returns:
        str: The corrected date string.
        """
        date_str, _ = split(r'\,| ', date_str, 1)
        date_str = sub(r'\.|\/', '-', date_str)
        return date_str


CELLS = (
    'D3',
    'A5',
    'A9',
    'C9',
    'C11',
    'A21',
    'A23',
    'D23',
    'A25',
    'A11',
    'A13',
    'D27',
)


class FixedAssetDocument(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    document_name_unit: str
    document_name_serial: str
    fixed_asset: FixedAsset

    @field_validator('document_name_unit', mode='before')
    @classmethod
    def document_name_unit_parser(cls, value: str) -> str:
        """
        Parses the document name and removes any slashes in the name.
        """
        if value == '' or value is None:
            return 'unknown_unit'
        if '/' in value:
            value = sub(r'\/', '_', value)
        return value

    @classmethod
    def _populate_worksheet(
            cls,
            sheet: Worksheet,
            fixed_asset: dict[str, Any]
        ) -> None:
        """
        Populates the worksheet with the fixed asset data.
        Additionaly, if "fixed_asset['id_vim']" value is set, we change
        the color of its cell (D27, which is outside of the document) to grey.
        """
        if invoice_date := fixed_asset.pop('invoice_date', None):
            fixed_asset['invoice'] = \
                f'{fixed_asset["invoice"]} on {invoice_date}'
        if fixed_asset['id_vim'] != '':
            fixed_asset['id_vim'] = f'ID VIM: {fixed_asset["id_vim"]}'
            id_vim_cell = sheet['D27']
            id_vim_cell.font = Font(color='00969696')
        cells = dict(zip(CELLS, fixed_asset.values()))
        for cell, value in cells.items():
            sheet[cell] = value

    @classmethod
    def _load_template(cls) -> None:
        """
        Loads the template file.
        """
        settings = AppSettings()
        template_filename = Path(settings.fa_filename)
        try:
            document: Workbook = load_workbook(template_filename)
            return (document, settings.fa_path)
        except ValueError as e:
            raise FileNotFoundError('Template file not found.') from e

    def generate_document(self) -> None:
        """
        Makes the fixed asset document.

        Notice the variable 'document' we use here is a Workbook object,
        not FixedAssetDocument.
        """
        document, path = self._load_template()
        self._populate_worksheet(
            document.active,
            self.fixed_asset.model_dump()
        )
        document_name = \
            f'{self.document_name_unit}-{self.document_name_serial}'
        document.active.title = document_name
        document.save(Path(f'{path}/{document_name}.xlsx'))
