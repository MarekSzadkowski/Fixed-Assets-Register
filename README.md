# Fixed Assets Register

## Purpose

Written for commercial use by my wife, entirely in Python, a small script designed to help her and her unit to keep track of their fixed asset documents.

Since in the corporate world *"Excel is everywhere"*, this Python script imports the data from an 
[Excel file](Wordbook.md) and stores it in a simple, pickle-formatted DB file. When needed a fixed asset document is created, which is another Excel file. For this purpose, the script utilizes the power of Openpyxl and Pydantic, as well as basic tests written in pytest.

The picture below shows how such document looks like.

![Fixed Asset Document (excel)](fixed-asset-document.png "Fixed Asset Document")

For me it was also an opportunity to create an entry in my portfolio to present some python techniques used, like pooling or ...

```python
    for row in rows:
        yield {key: row[index] for key, index in INDEXES.items()}
```

... working with a generator while remapping excel's rows to dictionaries - a preferred, *pythonic* way to present data structures.

## Installation

Make sure you have git and Python installed, the script runs with python 3.11 and 3.12. Then simply go through the steps below.

1. Clone this repository with:
```sh
   git clone https://github.com/MarekSzadkowski/Fixed-Assets-Register.git
```
This will create **`Fixed-Assets-Register`** directory with files downloaded from Github. You want to change this name to something else, otherwise the tests will not work. See more in the [Known Issues](#known-issues) section. Here I call it **`main`**.

2. Change the directory:
```sh
   mv Fixed-Assets-Register main
```
3. Go to the directory:
```sh
   cd main
```
4. Create Python's environment:
```sh
   python -m venv .env
```
5. Activate it - on Linux and Mac:
```sh
   source .env/bin/activate
```
on Windows:
```sh
   .env\Scripts\activate
```
6. Install requirements:
```sh
   pip install -r requirements.txt
```

Voila! You are ready to go.

## Usage

### TL;DR

On Linux and Mac just run it: ./main.py \[parameter\], on Windows however you must use: python main.py \[parameter\]

First run the program with the **config** parameter. It will create a settings file called settings.txt

Then import data from a workbook, issuing `./main.py import-wb`.

To create a Fixed Asset Document use `./main.py create-ducument serial`, where *serial* is the 6 digits you can take from the dump.

You can also create documents for every record you have in your db - instead of *serial* use `--all`.

As you saw above you may skip a parameter, in this case the program would call the report function which dumps the content of DB to the screen. However if no data exists yet, it stops with according message.

## TODO

1. Search function - not needed at the time being.

## Known issues

register.models.py, line 22: COMMITTEE - it is defined but not used anywhere - its usability is questionable ATM.

Tests: You may know already the default name you get from GitHub is the one corresponding to the repository name - `Fixed-Assets-Register` in this case. After many tries I came to conclusion Pytest doesn't like hyphens in the name of the main directory, that's why if you don't change the default name and leave it as is tests will probably don't work for you as never worked for me.

If you happen to find a bug please feel free to file it through Issue button above.

## Tweaking the program

If you would like to modify the script to import your excel-generated documents, just modify **INDEXES** in register.wordbook.py according to your needs. Modifying the FixedAsset class (register.models.py) and its validation methods may be needed too.
