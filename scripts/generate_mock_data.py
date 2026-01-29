"""
Generate mock Tableau XML files and historical issues data for testing
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
from xml.dom import minidom


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def generate_mock_workbook():
    """Generate sample Tableau Workbook XML"""

    workbook = ET.Element('workbook', {
        'source-build': '2023.1.0',
        'version': '18.1',
        'xmlns:user': 'http://www.tableausoftware.com/xml/user'
    })

    # Datasources container
    datasources = ET.SubElement(workbook, 'datasources')

    # Datasource 1: Sales data
    ds1 = ET.SubElement(datasources, 'datasource', {
        'name': 'Sample-Superstore',
        'caption': 'Sales Data',
        'inline': 'true'
    })

    # Connection
    connection1 = ET.SubElement(ds1, 'connection', {
        'class': 'sqlserver',
        'dbname': 'SalesDB',
        'server': 'sql-server-01.db.com',
        'schema': 'dbo',
        'username': 'sales_user'
    })

    # Calculated field 1: Profit Margin
    column1 = ET.SubElement(ds1, 'column', {
        'caption': 'Profit Margin',
        'datatype': 'real',
        'name': '[Calculated_Profit_Margin]',
        'role': 'measure',
        'type': 'quantitative'
    })
    calc1 = ET.SubElement(column1, 'calculation', {
        'formula': '[Profit] / [Sales]',
        'class': 'tableau'
    })

    # Calculated field 2: YTD Sales
    column2 = ET.SubElement(ds1, 'column', {
        'caption': 'YTD Sales',
        'datatype': 'real',
        'name': '[Calculated_YTD_Sales]',
        'role': 'measure',
        'type': 'quantitative'
    })
    calc2 = ET.SubElement(column2, 'calculation', {
        'formula': 'SUM(IF [Order Date] &lt;= TODAY() THEN [Sales] END)',
        'class': 'tableau'
    })

    # Calculated field 3: Sales Category
    column3 = ET.SubElement(ds1, 'column', {
        'caption': 'Sales Category',
        'datatype': 'string',
        'name': '[Calculated_Sales_Category]',
        'role': 'dimension',
        'type': 'nominal'
    })
    calc3 = ET.SubElement(column3, 'calculation', {
        'formula': 'IF [Sales] &gt; 10000 THEN "High" ELSEIF [Sales] &gt; 5000 THEN "Medium" ELSE "Low" END',
        'class': 'tableau'
    })

    # Join/Relation
    relation = ET.SubElement(ds1, 'relation', {
        'type': 'join',
        'join': 'inner',
        'connection': 'sqlserver'
    })

    # Left table
    left_relation = ET.SubElement(relation, 'relation', {
        'type': 'table',
        'table': '[dbo].[Orders]',
        'name': 'Orders'
    })

    # Right table
    right_relation = ET.SubElement(relation, 'relation', {
        'type': 'table',
        'table': '[dbo].[Customers]',
        'name': 'Customers'
    })

    # Join clause
    clause = ET.SubElement(relation, 'clause', {
        'type': 'join',
        'expression': '[Orders].[CustomerID] = [Customers].[CustomerID]'
    })

    # Parameters
    param1 = ET.SubElement(workbook, 'parameter', {
        'name': 'Date Range Start',
        'type': 'date',
        'value': '#2025-01-01#',
        'caption': 'Start Date'
    })

    param2 = ET.SubElement(workbook, 'parameter', {
        'name': 'Date Range End',
        'type': 'date',
        'value': '#2025-12-31#',
        'caption': 'End Date'
    })

    param3 = ET.SubElement(workbook, 'parameter', {
        'name': 'Region Filter',
        'type': 'string',
        'value': 'All',
        'caption': 'Select Region'
    })

    # Worksheets container
    worksheets = ET.SubElement(workbook, 'worksheets')

    # Worksheet 1
    worksheet1 = ET.SubElement(worksheets, 'worksheet', {
        'name': 'Sales Overview'
    })

    # Filter in worksheet
    filter1 = ET.SubElement(worksheet1, 'filter', {
        'column': '[Region]',
        'class': 'categorical'
    })

    filter2 = ET.SubElement(worksheet1, 'filter', {
        'column': '[Order Date]',
        'class': 'quantitative'
    })

    # Save
    output_path = Path(__file__).parent.parent / 'data' / 'mock_samples' / 'sample_workbook.twb'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write with pretty formatting
    xml_str = prettify_xml(workbook)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)

    print(f"[OK] Generated mock workbook: {output_path}")


def generate_mock_prepflow():
    """Generate sample Tableau Prep Flow XML"""

    flow = ET.Element('datasource', {
        'formatted-name': 'Customer Analysis Flow',
        'inline': 'true',
        'version': '18.1'
    })

    # Process container
    process = ET.SubElement(flow, 'process')

    # Input node 1
    input1 = ET.SubElement(process, 'node', {
        'type': 'input',
        'name': 'Customer Data',
        'id': 'node1'
    })
    ET.SubElement(input1, 'connection', {
        'class': 'sqlserver',
        'server': 'sql-server-01.db.com',
        'dbname': 'CRM_DB',
        'schema': 'dbo',
        'table-name': 'Customers'
    })

    # Input node 2
    input2 = ET.SubElement(process, 'node', {
        'type': 'input',
        'name': 'Order Data',
        'id': 'node2'
    })
    ET.SubElement(input2, 'connection', {
        'class': 'sqlserver',
        'server': 'sql-server-01.db.com',
        'dbname': 'SalesDB',
        'schema': 'dbo',
        'table-name': 'Orders'
    })

    # Clean node
    clean_node = ET.SubElement(process, 'node', {
        'type': 'clean',
        'name': 'Clean Customer Names',
        'id': 'node3',
        'input': 'node1'
    })
    ET.SubElement(clean_node, 'operation', {
        'type': 'remove-nulls',
        'field': 'CustomerName'
    })

    # Join node
    join_node = ET.SubElement(process, 'node', {
        'type': 'join',
        'name': 'Join Customer and Orders',
        'id': 'node4',
        'join-type': 'left'
    })

    # Join inputs
    ET.SubElement(join_node, 'input', {
        'source': 'node3',
        'alias': 'Customers'
    })
    ET.SubElement(join_node, 'input', {
        'source': 'node2',
        'alias': 'Orders'
    })

    # Join clauses
    join_conditions = ET.SubElement(join_node, 'join-conditions')
    ET.SubElement(join_conditions, 'join-clause', {
        'left-field': 'CustomerID',
        'right-field': 'CustomerID',
        'operator': '=',
        'left-source': 'Customers',
        'right-source': 'Orders'
    })

    # Aggregate node
    agg_node = ET.SubElement(process, 'node', {
        'type': 'aggregate',
        'name': 'Calculate Customer Totals',
        'id': 'node5',
        'input': 'node4'
    })

    # Group by fields
    groupby = ET.SubElement(agg_node, 'groupby')
    ET.SubElement(groupby, 'field', {'name': 'CustomerID'})
    ET.SubElement(groupby, 'field', {'name': 'CustomerName'})

    # Aggregations
    aggregations = ET.SubElement(agg_node, 'aggregations')
    ET.SubElement(aggregations, 'field', {
        'name': 'TotalSales',
        'calculation': 'SUM',
        'source-field': 'Sales'
    })
    ET.SubElement(aggregations, 'field', {
        'name': 'OrderCount',
        'calculation': 'COUNT',
        'source-field': 'OrderID'
    })

    # Filter node
    filter_node = ET.SubElement(process, 'node', {
        'type': 'filter',
        'name': 'Filter High Value Customers',
        'id': 'node6',
        'input': 'node5'
    })
    ET.SubElement(filter_node, 'condition', {
        'field': 'TotalSales',
        'operator': 'greater-than',
        'value': '10000'
    })

    # Output node
    output_node = ET.SubElement(process, 'node', {
        'type': 'output',
        'name': 'Customer Summary Output',
        'id': 'node7',
        'input': 'node6'
    })
    ET.SubElement(output_node, 'connection', {
        'class': 'hyper',
        'dbname': 'CustomerSummary.hyper',
        'schema': 'Extract',
        'table-name': 'CustomerMetrics'
    })

    # Save
    output_path = Path(__file__).parent.parent / 'data' / 'mock_samples' / 'sample_prepflow.tfl'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write with pretty formatting
    xml_str = prettify_xml(flow)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)

    print(f"[OK] Generated mock prep flow: {output_path}")


def generate_mock_issues_excel():
    """Generate sample historical issues Excel file"""

    # Create sample issues data
    issues_data = {
        'Dashboard/Workflow Name': [
            'sales_dashboard',
            'sales_dashboard',
            'sales_dashboard',
            'customer_prep_flow',
            'customer_prep_flow',
            'sales_dashboard',
            'customer_prep_flow',
            'sales_dashboard'
        ],
        'Issue Description': [
            'Dashboard showing blank values for Q4 2025 data',
            'Profit Margin calculation showing incorrect percentages',
            'Region filter not working properly - shows all regions even when filtered',
            'Join step failing with error: duplicate key values',
            'Output file not being generated after successful run',
            'YTD Sales metric showing negative values',
            'Aggregate step running extremely slowly (>30 minutes)',
            'Parameter Date Range End not updating dashboard data'
        ],
        'Root Cause': [
            'Parameter "Date Range End" was set to 2025-09-30, not including Q4',
            'Calculated field [Profit Margin] formula had division by zero issue when Sales = 0',
            'Filter was using wrong field name - used [Region Name] instead of [Region]',
            'Source table Customers had duplicate CustomerID values due to data quality issue',
            'Output connection credentials expired, causing silent failure',
            'Calculated field [YTD Sales] had incorrect date comparison logic using >= instead of <=',
            'Join on unindexed columns in large tables (Customers: 5M rows, Orders: 20M rows)',
            'Parameter was configured with allowable values list that did not include dates beyond 2025-10-31'
        ],
        'Resolution': [
            'Updated parameter "Date Range End" to 2025-12-31 to include full year',
            'Modified formula to: IF [Sales] = 0 THEN 0 ELSE [Profit] / [Sales] END',
            'Corrected filter field reference from [Region Name] to [Region] in worksheet filters',
            'Added DISTINCT clause in input step to deduplicate; filed ticket with data team to fix source',
            'Refreshed output connection credentials and added error notification in flow',
            'Fixed formula to: SUM(IF [Order Date] <= TODAY() THEN [Sales] END)',
            'Created indexes on CustomerID in both tables; reduced runtime to 3 minutes',
            'Removed allowable values restriction on Date Range End parameter to allow all dates'
        ]
    }

    # Create DataFrame
    df = pd.DataFrame(issues_data)

    # Save to Excel
    output_path = Path(__file__).parent.parent / 'data' / 'historical_issues' / 'issues_export.xlsx'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_excel(output_path, index=False, engine='openpyxl')

    print(f"[OK] Generated mock issues file: {output_path}")
    print(f"  - Created {len(df)} sample issue records")


if __name__ == '__main__':
    print("\nGenerating mock data for Tableau chatbot...")
    print("=" * 60)

    generate_mock_workbook()
    generate_mock_prepflow()
    generate_mock_issues_excel()

    print("=" * 60)
    print("\n[OK] Mock data generation complete!")
    print("\nGenerated files:")
    print("  - data/mock_samples/sample_workbook.twb")
    print("  - data/mock_samples/sample_prepflow.tfl")
    print("  - data/historical_issues/issues_export.xlsx")
