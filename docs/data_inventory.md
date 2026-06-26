# Data Inventory

This repo stores only lightweight reusable snapshots.

## `data_snapshots/tech_money_flow/`

Generated on 2026-06-26 from online AKShare interfaces.

- `industry_all.csv`: raw industry money-flow table.
- `concept_all.csv`: raw concept money-flow table.
- `star_board_all.csv`: STAR Market main-fund ranking table.
- `chinext_all.csv`: ChiNext main-fund ranking table.
- `tech_industry.csv`: technology-related industries filtered by keywords.
- `tech_concept.csv`: technology-related concepts filtered by keywords.
- `tech_star_board.csv`: technology-related STAR Market stocks.
- `tech_chinext.csv`: technology-related ChiNext stocks.
- `report.md`: human-readable report from the scan.

## `data_snapshots/baostock_csi300_sample/`

Small Baostock sample from the CSI300 constituent set.

- five stock daily CSVs;
- constituent CSV;
- download summary.

This is useful for schema and field checks only.

## `data_snapshots/baostock_csi300_partial/`

Partial interrupted CSI300 online fetch.

This is not a complete CSI300 dataset. It is preserved only because it is small and can help future sessions avoid rechecking basic CSV schema.

## Excluded On Purpose

- full Qlib binary data archive;
- partial `qlib_bin.tar.gz`;
- virtual environments;
- cloned upstream Qlib/AlphaGen source trees;
- full-market historical database.
