Read `sales.csv`. It has a header row and the columns
`region,units,price`.

Apply exactly these rules, in this order:

1. A row is **malformed** if any field is empty. Malformed rows are excluded
   and counted in `rows_skipped`.
2. After that, a row that is byte-identical to an earlier kept row is a
   **duplicate**. Duplicates are excluded and counted in `duplicates`.
3. `revenue_total` is the sum of `units * price` over the kept rows, to exactly
   two decimal places.

Write `out/summary.txt` containing exactly three lines in this order:

    rows_skipped=N
    duplicates=N
    revenue_total=X.XX

Do not add commentary.
