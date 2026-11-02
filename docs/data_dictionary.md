# Data dictionary

One row represents a simulated daily campaign/audience/device observation. Rows
are independent observations; the generator does not claim a unique daily key.
There are no customer identifiers. All currency values use PKR, with two decimals.

| Column | Type | Meaning and validation |
| --- | --- | --- |
| date | YYYY-MM-DD | Observation date; demo dates span calendar year 2025 |
| campaign | string | Campaign label, eight campaigns per platform in the simulator |
| platform | category | Facebook, Instagram, Google, TikTok, YouTube |
| impressions | integer | Non-negative number of ad views |
| clicks | integer | Non-negative; cannot exceed impressions |
| spend | decimal | Non-negative advertising cost in PKR |
| conversions | integer | Non-negative; cannot exceed clicks |
| revenue | decimal | Non-negative attributed revenue in PKR |
| age | integer | Age from 18 to 100; simulator generates 18–65 |
| gender | string | Simulator uses Female, Male and Unspecified |
| city | string | Simulator uses five Pakistani cities |
| device | string | Simulator uses Mobile, Desktop and Tablet |

Required values cannot be null or blank. Numeric measures must be finite. Invalid
records cause explicit failures; the pipeline does not quietly drop them. Spark
requires this exact column order because its explicit CSV schema is positional.
Pandas-based backends accept any order and ignore extra columns.

Demographic fields support descriptive segmentation. They do not determine budget
allocation, and no personal information is needed. Revenue is attributed sales,
not profit, lifetime value, or incrementally caused sales. `profit_proxy` subtracts
advertising spend only and excludes product cost, returns, taxes and overhead.

Zero denominators are allowed: the corresponding KPI is undefined and exported as
a blank CSV field. Real-world multi-touch attribution, refunds and conversions
without a tracked click need an adapted data contract before ingestion.
