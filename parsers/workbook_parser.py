"""
Tableau Workbook XML Parser
Extracts: data sources, connections, calculated fields, joins, filters, parameters
Output: JSON keyed by dashboard name
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import json
from pathlib import Path


class WorkbookParser:
    """Parser for Tableau Workbook (.twb/.twbx) XML files"""

    def __init__(self, xml_path: str):
        """
        Initialize parser with path to Tableau workbook XML

        Args:
            xml_path: Path to .twb or extracted .twbx file
        """
        self.xml_path = xml_path
        try:
            self.tree = ET.parse(xml_path)
            self.root = self.tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML file: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {xml_path}")

    def extract_datasources(self) -> List[Dict[str, Any]]:
        """Extract all data sources with connection details"""
        datasources = []

        for ds in self.root.findall('.//datasource[@name]'):
            ds_name = ds.get('name')
            # Skip internal Tableau datasources
            if ds_name and (ds_name.startswith('Parameters') or ds_name == 'Sample File'):
                continue

            datasource_info = {
                'name': ds_name,
                'caption': ds.get('caption', ds_name),
                'inline': ds.get('inline', 'false'),
                'connection': self._extract_connection(ds)
            }
            datasources.append(datasource_info)

        return datasources

    def _extract_connection(self, datasource: ET.Element) -> Dict[str, Optional[str]]:
        """Extract connection details from a datasource"""
        conn = datasource.find('.//connection')
        if conn is None:
            return {}

        return {
            'class': conn.get('class'),
            'server': conn.get('server'),
            'dbname': conn.get('dbname'),
            'schema': conn.get('schema'),
            'username': conn.get('username'),
            'authentication': conn.get('authentication')
        }

    def extract_calculated_fields(self) -> List[Dict[str, str]]:
        """Extract calculated fields with formulas"""
        fields = []

        # Look for columns with calculations
        for col in self.root.findall('.//column[@caption]'):
            calc_name = col.get('name', '')

            # Skip non-calculated fields (they don't start with [Calculated_])
            if not ('Calculated' in calc_name or col.find('.//calculation') is not None):
                continue

            calculation = col.find('.//calculation')
            if calculation is not None:
                fields.append({
                    'name': col.get('caption', calc_name),
                    'internal_name': calc_name,
                    'formula': calculation.get('formula', ''),
                    'datatype': col.get('datatype', 'unknown'),
                    'role': col.get('role', ''),
                    'type': col.get('type', '')
                })

        return fields

    def extract_parameters(self) -> List[Dict[str, str]]:
        """Extract parameters used in the workbook"""
        params = []

        for param in self.root.findall('.//parameter'):
            params.append({
                'name': param.get('name', ''),
                'caption': param.get('caption', param.get('name', '')),
                'datatype': param.get('type', ''),
                'value': param.get('value', ''),
                'alias': param.get('alias', '')
            })

        return params

    def extract_filters(self) -> List[Dict[str, Any]]:
        """Extract filters applied in worksheets"""
        filters = []

        for filter_elem in self.root.findall('.//filter'):
            filter_info = {
                'column': filter_elem.get('column', ''),
                'class': filter_elem.get('class', ''),
                'field': filter_elem.get('field', '')
            }

            # Avoid duplicate empty entries
            if filter_info['column'] or filter_info['field']:
                filters.append(filter_info)

        return filters

    def extract_joins(self) -> List[Dict[str, Any]]:
        """Extract join conditions between tables"""
        joins = []

        # Find relation elements with type="join"
        for relation in self.root.findall('.//relation[@type="join"]'):
            join_info = {
                'join_type': relation.get('join', 'inner'),
                'connection': relation.get('connection', ''),
                'tables': self._extract_join_tables(relation),
                'condition': self._extract_join_clause(relation)
            }
            joins.append(join_info)

        return joins

    def _extract_join_tables(self, relation: ET.Element) -> Dict[str, str]:
        """Extract left and right tables from a join relation"""
        tables = {'left': '', 'right': ''}

        # Look for nested relation elements
        nested_relations = relation.findall('.//relation[@type="table"]')
        if len(nested_relations) >= 2:
            tables['left'] = nested_relations[0].get('table', nested_relations[0].get('name', ''))
            tables['right'] = nested_relations[1].get('table', nested_relations[1].get('name', ''))

        return tables

    def _extract_join_clause(self, relation: ET.Element) -> str:
        """Extract join ON clause expression"""
        clause = relation.find('.//clause[@type="join"]')
        if clause is not None:
            return clause.get('expression', '')

        # Alternative: check for expression attribute directly
        return relation.get('expression', '')

    def parse_to_dict(self, dashboard_name: str) -> Dict[str, Any]:
        """
        Parse entire workbook to structured dictionary

        Args:
            dashboard_name: Identifier for this dashboard

        Returns:
            Dictionary containing all extracted metadata
        """
        return {
            'dashboard_name': dashboard_name,
            'type': 'workbook',
            'datasources': self.extract_datasources(),
            'calculated_fields': self.extract_calculated_fields(),
            'parameters': self.extract_parameters(),
            'filters': self.extract_filters(),
            'joins': self.extract_joins(),
            'metadata': {
                'source_file': Path(self.xml_path).name,
                'workbook_version': self.root.get('version', 'unknown')
            }
        }

    def save_to_json(self, output_path: str, dashboard_name: str) -> None:
        """
        Save parsed data to JSON file

        Args:
            output_path: Path where JSON should be saved
            dashboard_name: Identifier for this dashboard
        """
        data = self.parse_to_dict(dashboard_name)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved workbook metadata to: {output_file}")


def parse_workbook(xml_path: str, dashboard_name: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Convenience function to parse a Tableau workbook

    Args:
        xml_path: Path to .twb file
        dashboard_name: Identifier for the dashboard
        output_dir: Optional directory to save JSON output

    Returns:
        Parsed metadata dictionary
    """
    parser = WorkbookParser(xml_path)
    metadata = parser.parse_to_dict(dashboard_name)

    if output_dir:
        output_path = Path(output_dir) / f"{dashboard_name}.json"
        parser.save_to_json(str(output_path), dashboard_name)

    return metadata


if __name__ == '__main__':
    # Example usage
    import sys

    if len(sys.argv) < 3:
        print("Usage: python workbook_parser.py <input_file.twb> <dashboard_name> [output_dir]")
        print("\nExample:")
        print("  python workbook_parser.py ../data/mock_samples/sample_workbook.twb sales_dashboard ../data/parsed_metadata/workbooks")
        sys.exit(1)

    input_file = sys.argv[1]
    dash_name = sys.argv[2]
    output_directory = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        result = parse_workbook(input_file, dash_name, output_directory)
        print(f"\nSuccessfully parsed workbook '{dash_name}':")
        print(f"  - Data sources: {len(result['datasources'])}")
        print(f"  - Calculated fields: {len(result['calculated_fields'])}")
        print(f"  - Parameters: {len(result['parameters'])}")
        print(f"  - Filters: {len(result['filters'])}")
        print(f"  - Joins: {len(result['joins'])}")
    except Exception as e:
        print(f"Error parsing workbook: {e}", file=sys.stderr)
        sys.exit(1)
