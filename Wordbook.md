# Wordbook structure

The workbook consists of the following 18 columns:

1. ordinal number:
   * it represents an invoice or a group of them,
   * may repeat itself many times,
   * may also be skipped (None), **AFTER** it has been specified once.
2. id vim
3. inventory number
4. financial source
   * very important column as it constitutes the fields of psp and cost_center
5. invoice number
6. invoice date
7. name of a product/asset
8. quantity
   * always 1 for a fixed asset
9. price
10. value
    * the two above make a formula, so only **this** column is used
11. producer/supplier
12. registering date
    * when the asset was accepted to the register
13. unit
    * the division/entity an asset belongs to
14. material duty person
15. use purpose
16. serial number
17. unused
18. unused
