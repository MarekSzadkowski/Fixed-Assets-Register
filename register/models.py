from datetime import datetime  # pylint: disable=unused-import
from json import load, dump
from pathlib import Path
from re import match, split, sub
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo
from pydantic.alias_generators import to_camel

class AppSettings(BaseModel):
    data_path: Path = Path.cwd()
    config_file: str = 'settings.txt'
    wb_filename: str | None = None
    # sheet_name: str | None = None
    fa_filename: str | None = None
    fa_path: str = 'FA_documents'
    last_column: int | None = None
    configured: bool = False

    def model_post_init(self, __context: Any) -> None:
        self.fa_path = str(self.data_path / self.fa_path)
        filename = self.data_path / self.config_file
        if Path.is_file(filename):
            with open(filename, encoding='utf-8') as config_file:
                config = load(config_file)

            self.__dict__.update(config)
            self.data_path = Path(config.get('data_path'))

        # It seems Pydantic requires use of __context to initialize the model,
        # here it defaults to None
        super().model_post_init(__context)

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
                # "sheet_name": self.sheet_name,
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
    invoice_date: str
    issuer: str
    value: str
    material_duty_person: str
    psp: str
    cost_center: str
    inventory_number: str

    @field_validator('invoice', 'invoice_date', 'issuer', mode='before')
    @classmethod
    def parse_default(cls, value: Any) -> str:
        if value is None:
            return 'appendix'
        return value

    @field_validator('date', 'material_duty_person', mode='before')
    @classmethod
    def parse_value(cls, value: Any) -> str:
        if value is None:
            return ''
        return value

    @field_validator('date', 'invoice_date', mode='before')
    @classmethod
    def parse_date(cls, value: str) -> str:
        """
        Usually excel's date is a datetime object, but sometimes may be given
        as a string not complying with the actual standards, e.g. as
        'date, date' literals. In this case the former literal is taken.

        Parameters:
        date (str | None): The input date string to be corrected.

        Returns:
        str: The corrected date string.
        """

        if isinstance(value, datetime):
            return value.strftime('%d-%m-%Y')
        if isinstance(value, str):
            date_string = cls.__format_date(cls, value)
            date = match(DATE_PATTERN, date_string)
            if date is None:
                raise ValueError(date_string)

            return date.group()

    # Sometimes financial_source is a very complex string, in such cases values
    # of 'invoice' and 'issuer' are usually not given, therefore None, which
    # needed fixing so the class' constructor wouldn't complain.
    # Now we can check it again. We DO NOT have a value of financial_source,
    # but we can check the value of cost_center, which in such cases is copied to
    # psp and cost_center.
    @field_validator('cost_center')
    @classmethod
    def date_after_parser(
        cls,
        cost_center: str,
        validated_values: ValidationInfo
    ) -> str:
        if (validated_values.data['date'] == ''
            and ' ' not in cost_center):
            raise ValueError('Please specify a date in the format DD-MM-YYYY')
        return cost_center

    def __format_date(self, date_str: str) -> str:
        """
        Corrects the date format by removing any comma or space,
        replaces dots with dashes and returns the corrected date.

        Parameters:
        date (str): The input date string to be corrected.

        Returns:
        str: The corrected date string.
        """
        # The following line is needless cause pydantic does it for us
        # date_str = sub(r'[,\s]+', '', date_str)
        # Sadly this here however doesn't word, returns None value.
        date_string, _ = split(r'\,| ', date_str, 1)
        date_str = sub(r'\.|\/', '-', date_string)
        return date_str

class FixedAssetDocument(BaseModel):
    document_name_unit: str
    document_name_serial: str
    fixed_asset: FixedAsset
    FA_TEMPLATE: str = 'FA_template.xlsx'
    committee: list = Field(
        min_length=1,
        max_length=3,
        default=['John Smith', 'Jane Doe']
    )

class BadDateFormat(Exception):
    """
    Raised if the date is not in the correct format
    """
    def __init__(self, date: str):
        self.date = date
        self.message = f'Invalid date format: {date}'
        super().__init__(self.message)
