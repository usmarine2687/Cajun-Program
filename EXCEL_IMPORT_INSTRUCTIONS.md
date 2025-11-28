# Excel Customer Import Instructions

## How to Import Customers from Excel

1. **Open the Cajun Marine application**
2. **Navigate to the Customers view**
3. **Click the "Import from Excel" button** (orange button in the header)
4. **Select your Excel file** (.xlsx or .xls format)

## Excel File Format

Your Excel file should have the following columns (column names are case-insensitive and can be in any order):

| Column Name | Required | Format | Example |
|------------|----------|--------|---------|
| **Name** | ✓ Yes | Text | John Doe |
| Phone | No | Any format (will auto-format) | (555)123-4567 or 555-123-4567 |
| Email | No | Valid email address | john@example.com |
| Address | No | Text | 123 Main St, City, LA 70001 |
| Tax Exempt | No | Yes/No or 1/0 | Yes or No |
| Tax Exempt Certificate | No | Text | TX-12345 |
| Out of State | No | Yes/No or 1/0 | Yes or No |

## Sample Template

A sample Excel template is included: **customer_import_template.xlsx**

You can use this as a starting point for your customer data.

## Import Behavior

- **New Customers**: If a customer name doesn't exist in the database, a new customer will be created
- **Existing Customers**: If a customer name already exists (case-insensitive match), the customer information will be updated
- **Duplicate Detection**: Matches customers by name only

## Import Results

After import, you'll see a summary showing:
- Number of customers created
- Number of customers updated
- Any errors encountered during import

## Tips

- Make sure the first row contains column headers
- Empty rows are automatically skipped
- Phone numbers can be in any format (will be standardized)
- For Tax Exempt and Out of State, you can use: Yes/No, Y/N, 1/0, or True/False
- If a customer name matches an existing customer, all their information will be updated

## Troubleshooting

If you encounter errors:
- Check that your Excel file has a "Name" column
- Verify email addresses are in valid format
- Ensure the file is not open in Excel (close it first)
- Check the error messages for specific row numbers that failed

## Example Excel Data

```
Name            | Phone          | Email              | Address         | Tax Exempt | Certificate | Out of State
John Doe        | (555)123-4567  | john@example.com   | 123 Main St    | No         |             | No
Jane Smith      | 555-987-6543   | jane@example.com   | 456 Oak Ave    | Yes        | TX-12345    | No
Bob Johnson     | 5555555555     | bob@example.com    | 789 Pine Rd    | No         |             | Yes
```

All of these phone number formats will be accepted and standardized!
