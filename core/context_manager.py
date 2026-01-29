"""
Context Manager: Loads and combines Tableau metadata + historical issues for prompt context
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import os


class ContextManager:
    """Manages context retrieval from parsed Tableau metadata and historical issues"""

    def __init__(self,
                 metadata_dir: str = 'data/parsed_metadata',
                 issues_path: str = 'data/historical_issues/issues_export.xlsx'):
        """
        Initialize context manager

        Args:
            metadata_dir: Directory containing parsed metadata JSON files
            issues_path: Path to historical issues Excel file
        """
        # Handle relative paths from project root
        if not Path(metadata_dir).is_absolute():
            metadata_dir = Path(__file__).parent.parent / metadata_dir
        if not Path(issues_path).is_absolute():
            issues_path = Path(__file__).parent.parent / issues_path

        self.metadata_dir = Path(metadata_dir)
        self.issues_path = Path(issues_path)
        self.issues_df = None

        # Load historical issues on init
        if self.issues_path.exists():
            self.load_historical_issues()
        else:
            print(f"Warning: Historical issues file not found at {self.issues_path}")

    def load_dashboard_metadata(self, dashboard_name: str,
                                dashboard_type: str = 'workbook') -> Optional[Dict[str, Any]]:
        """
        Load pre-parsed metadata for a dashboard or prep flow

        Args:
            dashboard_name: Name/ID of the dashboard
            dashboard_type: 'workbook' or 'prep_flow'

        Returns:
            Dictionary containing parsed metadata, or None if not found
        """
        subdir = 'workbooks' if dashboard_type == 'workbook' else 'prep_flows'
        json_path = self.metadata_dir / subdir / f"{dashboard_name}.json"

        if not json_path.exists():
            print(f"Warning: Metadata file not found: {json_path}")
            return None

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading metadata from {json_path}: {e}")
            return None

    def load_historical_issues(self):
        """Load historical issues from Excel export"""
        try:
            self.issues_df = pd.read_excel(self.issues_path, engine='openpyxl')
            print(f"Loaded {len(self.issues_df)} historical issues from {self.issues_path.name}")
        except Exception as e:
            print(f"Warning: Could not load historical issues: {e}")
            self.issues_df = None

    def get_relevant_issues(self, dashboard_name: str,
                           limit: int = None) -> List[Dict[str, str]]:
        """
        Get historical issues relevant to selected dashboard

        Args:
            dashboard_name: Name of the dashboard to filter by
            limit: Maximum number of issues to return (default from env or 5)

        Returns:
            List of dictionaries containing issue records
        """
        if self.issues_df is None or len(self.issues_df) == 0:
            return []

        # Get limit from environment or use default
        if limit is None:
            limit = int(os.getenv('MAX_HISTORICAL_ISSUES', '5'))

        # Filter by dashboard name (case-insensitive substring match)
        try:
            filtered = self.issues_df[
                self.issues_df['Dashboard/Workflow Name'].str.contains(
                    dashboard_name, case=False, na=False
                )
            ].head(limit)

            # Convert to list of dicts
            return filtered.to_dict('records')
        except KeyError:
            print("Warning: 'Dashboard/Workflow Name' column not found in issues file")
            return []

    def build_context_summary(self, dashboard_name: str,
                             dashboard_type: str = 'workbook') -> str:
        """
        Build comprehensive context string for prompt

        Args:
            dashboard_name: Name of the dashboard
            dashboard_type: 'workbook' or 'prep_flow'

        Returns:
            Formatted context string with metadata and historical issues
        """
        # Load metadata
        metadata = self.load_dashboard_metadata(dashboard_name, dashboard_type)

        # Load relevant issues
        issues = self.get_relevant_issues(dashboard_name)

        # Format context
        context_parts = []

        # 1. Dashboard/Flow Metadata
        if metadata:
            context_parts.append(self._format_metadata(metadata, dashboard_type))
        else:
            context_parts.append(f"# {dashboard_type.replace('_', ' ').title()}: {dashboard_name}\n\n(No metadata available)")

        # 2. Historical Issues
        if issues:
            context_parts.append(self._format_issues(issues))
        else:
            context_parts.append("# Historical Issues\n\nNo previous issues found for this dashboard.")

        return "\n\n---\n\n".join(context_parts)

    def _format_metadata(self, metadata: Dict, dashboard_type: str) -> str:
        """Format metadata as readable text"""
        if dashboard_type == 'workbook':
            return self._format_workbook_metadata(metadata)
        else:
            return self._format_prepflow_metadata(metadata)

    def _format_workbook_metadata(self, metadata: Dict) -> str:
        """Format workbook metadata"""
        sections = [f"# Tableau Workbook: {metadata.get('dashboard_name', 'Unknown')}\n"]

        # Data Sources
        if metadata.get('datasources'):
            sections.append("## Data Sources:")
            for ds in metadata['datasources']:
                conn = ds.get('connection', {})
                conn_str = f"{conn.get('class', 'N/A')}"
                if conn.get('dbname'):
                    conn_str += f" - {conn['dbname']}"
                if conn.get('server'):
                    conn_str += f" @ {conn['server']}"
                sections.append(f"- **{ds.get('caption', ds.get('name', 'Unknown'))}**: {conn_str}")

        # Calculated Fields
        if metadata.get('calculated_fields'):
            sections.append("\n## Calculated Fields:")
            for field in metadata['calculated_fields'][:10]:  # Limit to 10
                sections.append(f"- **{field['name']}**: `{field['formula']}`")
            if len(metadata['calculated_fields']) > 10:
                sections.append(f"  _(... and {len(metadata['calculated_fields']) - 10} more)_")

        # Parameters
        if metadata.get('parameters'):
            sections.append("\n## Parameters:")
            for param in metadata['parameters']:
                value_str = f" = {param['value']}" if param.get('value') else ""
                sections.append(f"- **{param.get('caption', param['name'])}** ({param['datatype']}){value_str}")

        # Joins
        if metadata.get('joins'):
            sections.append("\n## Joins:")
            for join in metadata['joins']:
                tables = join.get('tables', {})
                left = tables.get('left', 'Table1')
                right = tables.get('right', 'Table2')
                sections.append(f"- **{join['join_type'].upper()} JOIN**: {left} ↔ {right}")
                if join.get('condition'):
                    sections.append(f"  - Condition: `{join['condition']}`")

        # Filters
        if metadata.get('filters'):
            sections.append("\n## Active Filters:")
            for filt in metadata['filters'][:5]:  # Limit to 5
                col = filt.get('column') or filt.get('field')
                sections.append(f"- {col} ({filt.get('class', 'unknown')})")

        return "\n".join(sections)

    def _format_prepflow_metadata(self, metadata: Dict) -> str:
        """Format prep flow metadata"""
        sections = [f"# Tableau Prep Flow: {metadata.get('flow_name', 'Unknown')}\n"]

        # Input Sources
        if metadata.get('input_sources'):
            sections.append("## Input Sources:")
            for inp in metadata['input_sources']:
                conn = inp.get('connection', {})
                table_info = conn.get('table', 'N/A')
                if conn.get('dbname'):
                    table_info = f"{conn['dbname']}.{table_info}"
                sections.append(f"- **{inp['name']}**: {table_info}")

        # Step Sequence
        if metadata.get('steps'):
            sections.append("\n## Transformation Steps:")
            for step in metadata['steps']:
                step_desc = f"{step['step_number']}. **{step['type'].upper()}**: {step['name']}"
                if step.get('join_type'):
                    step_desc += f" ({step['join_type']} join)"
                sections.append(step_desc)

        # Joins
        if metadata.get('joins'):
            sections.append("\n## Join Details:")
            for join in metadata['joins']:
                inputs = join.get('inputs', {})
                left_alias = inputs.get('left', {}).get('alias', 'Left')
                right_alias = inputs.get('right', {}).get('alias', 'Right')
                sections.append(f"- **{join['name']}** ({join['join_type']}): {left_alias} + {right_alias}")

                conditions = join.get('conditions', [])
                for cond in conditions:
                    sections.append(f"  - ON: {cond['left_field']} {cond['operator']} {cond['right_field']}")

        # Outputs
        if metadata.get('outputs'):
            sections.append("\n## Output Destinations:")
            for out in metadata['outputs']:
                conn = out.get('connection', {})
                dest = conn.get('table', conn.get('dbname', 'Unknown'))
                sections.append(f"- **{out['name']}** → {dest}")

        return "\n".join(sections)

    def _format_issues(self, issues: List[Dict]) -> str:
        """Format historical issues"""
        sections = ["# Historical Issues & Resolutions\n"]

        if not issues:
            sections.append("_No previous issues found for this dashboard._")
            return "\n".join(sections)

        sections.append(f"_Found {len(issues)} similar past issue(s):_\n")

        for i, issue in enumerate(issues, 1):
            sections.append(f"## Issue {i}:")
            sections.append(f"**Description:** {issue.get('Issue Description', 'N/A')}")
            sections.append(f"**Root Cause:** {issue.get('Root Cause', 'N/A')}")
            sections.append(f"**Resolution:** {issue.get('Resolution', 'N/A')}")
            sections.append("")  # Blank line between issues

        return "\n".join(sections)


if __name__ == '__main__':
    # Test the context manager
    print("Testing Context Manager...")
    print("=" * 60)

    cm = ContextManager()

    # Test loading workbook metadata
    print("\n1. Testing workbook metadata:")
    workbook_context = cm.build_context_summary('sales_dashboard', 'workbook')
    print(workbook_context[:500] + "...\n")

    # Test loading prep flow metadata
    print("\n2. Testing prep flow metadata:")
    flow_context = cm.build_context_summary('customer_prep_flow', 'prep_flow')
    print(flow_context[:500] + "...\n")

    # Test historical issues
    print("\n3. Testing historical issues retrieval:")
    issues = cm.get_relevant_issues('sales_dashboard', limit=3)
    print(f"Found {len(issues)} issues for sales_dashboard")
    if issues:
        print(f"First issue: {issues[0].get('Issue Description', 'N/A')[:100]}...")

    print("\n" + "=" * 60)
    print("[OK] Context Manager test complete!")
