"""
Tableau Prep Flow XML Parser
Extracts: input sources, step sequence, join conditions, outputs
Output: JSON keyed by flow name
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import json
from pathlib import Path


class PrepFlowParser:
    """Parser for Tableau Prep Flow (.tfl/.tflx) XML files"""

    def __init__(self, xml_path: str):
        """
        Initialize parser with path to Tableau Prep flow XML

        Args:
            xml_path: Path to .tfl or extracted .tflx file
        """
        self.xml_path = xml_path
        try:
            self.tree = ET.parse(xml_path)
            self.root = self.tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML file: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {xml_path}")

    def extract_input_sources(self) -> List[Dict[str, str]]:
        """Extract input data sources"""
        inputs = []

        for input_node in self.root.findall('.//node[@type="input"]'):
            input_info = {
                'id': input_node.get('id', ''),
                'name': input_node.get('name', ''),
                'connection': self._extract_input_connection(input_node)
            }
            inputs.append(input_info)

        return inputs

    def _extract_input_connection(self, node: ET.Element) -> Dict[str, str]:
        """Extract connection details from an input node"""
        conn = node.find('.//connection')
        if conn is None:
            return {}

        return {
            'class': conn.get('class', ''),
            'server': conn.get('server', ''),
            'dbname': conn.get('dbname', ''),
            'schema': conn.get('schema', ''),
            'table': conn.get('table-name', '')
        }

    def extract_step_sequence(self) -> List[Dict[str, Any]]:
        """Extract ordered sequence of transformation steps"""
        steps = []
        step_number = 0

        # Process all nodes in order
        for node in self.root.findall('.//node'):
            node_type = node.get('type')
            if not node_type:
                continue

            step_number += 1
            step_info = {
                'step_number': step_number,
                'type': node_type,
                'id': node.get('id', ''),
                'name': node.get('name', ''),
                'input_source': node.get('input', ''),
                'description': ''
            }

            # Add type-specific details
            if node_type == 'join':
                step_info['join_type'] = node.get('join-type', '')
            elif node_type == 'aggregate':
                step_info['aggregations'] = self._extract_aggregations(node)
            elif node_type == 'filter':
                step_info['condition'] = self._extract_filter_condition(node)
            elif node_type == 'clean':
                step_info['operation'] = self._extract_clean_operation(node)

            steps.append(step_info)

        return steps

    def _extract_aggregations(self, node: ET.Element) -> List[Dict[str, str]]:
        """Extract aggregation details from an aggregate node"""
        aggs = []

        for field in node.findall('.//aggregations/field'):
            aggs.append({
                'name': field.get('name', ''),
                'calculation': field.get('calculation', ''),
                'source_field': field.get('source-field', '')
            })

        return aggs

    def _extract_filter_condition(self, node: ET.Element) -> Dict[str, str]:
        """Extract filter condition from a filter node"""
        cond = node.find('.//condition')
        if cond is None:
            return {}

        return {
            'field': cond.get('field', ''),
            'operator': cond.get('operator', ''),
            'value': cond.get('value', '')
        }

    def _extract_clean_operation(self, node: ET.Element) -> Dict[str, str]:
        """Extract cleaning operation details"""
        op = node.find('.//operation')
        if op is None:
            return {}

        return {
            'type': op.get('type', ''),
            'field': op.get('field', '')
        }

    def extract_joins(self) -> List[Dict[str, Any]]:
        """Extract join nodes with conditions"""
        joins = []

        for join_node in self.root.findall('.//node[@type="join"]'):
            join_info = {
                'id': join_node.get('id', ''),
                'name': join_node.get('name', ''),
                'join_type': join_node.get('join-type', 'inner'),
                'inputs': self._extract_join_inputs(join_node),
                'conditions': self._extract_join_conditions(join_node)
            }
            joins.append(join_info)

        return joins

    def _extract_join_inputs(self, join_node: ET.Element) -> Dict[str, str]:
        """Extract input sources for a join"""
        inputs = {}

        input_elements = join_node.findall('.//input')
        for idx, inp in enumerate(input_elements):
            side = 'left' if idx == 0 else 'right'
            inputs[side] = {
                'source': inp.get('source', ''),
                'alias': inp.get('alias', '')
            }

        return inputs

    def _extract_join_conditions(self, join_node: ET.Element) -> List[Dict[str, str]]:
        """Extract join key pairs from join-conditions"""
        conditions = []

        for clause in join_node.findall('.//join-clause'):
            conditions.append({
                'left_field': clause.get('left-field', ''),
                'right_field': clause.get('right-field', ''),
                'operator': clause.get('operator', '='),
                'left_source': clause.get('left-source', ''),
                'right_source': clause.get('right-source', '')
            })

        return conditions

    def extract_outputs(self) -> List[Dict[str, str]]:
        """Extract output destinations"""
        outputs = []

        for output_node in self.root.findall('.//node[@type="output"]'):
            output_info = {
                'id': output_node.get('id', ''),
                'name': output_node.get('name', ''),
                'input_source': output_node.get('input', ''),
                'connection': self._extract_output_connection(output_node)
            }
            outputs.append(output_info)

        return outputs

    def _extract_output_connection(self, node: ET.Element) -> Dict[str, str]:
        """Extract output connection details"""
        conn = node.find('.//connection')
        if conn is None:
            return {}

        return {
            'class': conn.get('class', ''),
            'dbname': conn.get('dbname', ''),
            'schema': conn.get('schema', ''),
            'table': conn.get('table-name', '')
        }

    def parse_to_dict(self, flow_name: str) -> Dict[str, Any]:
        """
        Parse entire prep flow to structured dictionary

        Args:
            flow_name: Identifier for this flow

        Returns:
            Dictionary containing all extracted metadata
        """
        return {
            'flow_name': flow_name,
            'type': 'prep_flow',
            'input_sources': self.extract_input_sources(),
            'steps': self.extract_step_sequence(),
            'joins': self.extract_joins(),
            'outputs': self.extract_outputs(),
            'metadata': {
                'source_file': Path(self.xml_path).name,
                'flow_version': self.root.get('version', 'unknown')
            }
        }

    def save_to_json(self, output_path: str, flow_name: str) -> None:
        """
        Save parsed data to JSON file

        Args:
            output_path: Path where JSON should be saved
            flow_name: Identifier for this flow
        """
        data = self.parse_to_dict(flow_name)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved prep flow metadata to: {output_file}")


def parse_prep_flow(xml_path: str, flow_name: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Convenience function to parse a Tableau Prep flow

    Args:
        xml_path: Path to .tfl file
        flow_name: Identifier for the flow
        output_dir: Optional directory to save JSON output

    Returns:
        Parsed metadata dictionary
    """
    parser = PrepFlowParser(xml_path)
    metadata = parser.parse_to_dict(flow_name)

    if output_dir:
        output_path = Path(output_dir) / f"{flow_name}.json"
        parser.save_to_json(str(output_path), flow_name)

    return metadata


if __name__ == '__main__':
    # Example usage
    import sys

    if len(sys.argv) < 3:
        print("Usage: python prep_flow_parser.py <input_file.tfl> <flow_name> [output_dir]")
        print("\nExample:")
        print("  python prep_flow_parser.py ../data/mock_samples/sample_prepflow.tfl customer_prep_flow ../data/parsed_metadata/prep_flows")
        sys.exit(1)

    input_file = sys.argv[1]
    flow_nm = sys.argv[2]
    output_directory = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        result = parse_prep_flow(input_file, flow_nm, output_directory)
        print(f"\nSuccessfully parsed prep flow '{flow_nm}':")
        print(f"  - Input sources: {len(result['input_sources'])}")
        print(f"  - Steps: {len(result['steps'])}")
        print(f"  - Joins: {len(result['joins'])}")
        print(f"  - Outputs: {len(result['outputs'])}")
    except Exception as e:
        print(f"Error parsing prep flow: {e}", file=sys.stderr)
        sys.exit(1)
