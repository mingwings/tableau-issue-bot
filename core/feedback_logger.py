"""
Feedback Logger: Logs user interactions and feedback to SQLite database
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import os


class FeedbackLogger:
    """Logs user feedback and interactions for analytics"""

    def __init__(self, db_path: str = 'data/feedback_logs/feedback.db'):
        """
        Initialize feedback logger

        Args:
            db_path: Path to SQLite database file
        """
        # Handle relative paths from project root
        if not Path(db_path).is_absolute():
            db_path = Path(__file__).parent.parent / db_path

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with feedback table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user TEXT,
            dashboard TEXT NOT NULL,
            user_query TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            resolved BOOLEAN NOT NULL,
            comments TEXT,
            session_id TEXT
        )
        ''')

        conn.commit()
        conn.close()

    def log_feedback(self, dashboard: str, query: str, response: str,
                    resolved: bool, comments: Optional[str] = None,
                    session_id: Optional[str] = None):
        """
        Log a feedback entry

        Args:
            dashboard: Dashboard name/ID
            query: User's query/issue description
            response: Assistant's response
            resolved: Whether the issue was resolved (True/False)
            comments: Optional user comments (especially if not resolved)
            session_id: Optional session identifier
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO feedback (timestamp, user, dashboard, user_query,
                             assistant_response, resolved, comments, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            os.getenv('USER', os.getenv('USERNAME', 'unknown')),
            dashboard,
            query,
            response,
            resolved,
            comments,
            session_id
        ))

        conn.commit()
        conn.close()

    def get_feedback_stats(self, dashboard: Optional[str] = None) -> Dict[str, any]:
        """
        Get feedback statistics

        Args:
            dashboard: Optional dashboard name to filter by

        Returns:
            Dictionary with total, resolved, unresolved counts and resolution rate
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if dashboard:
            cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) as unresolved
            FROM feedback
            WHERE dashboard = ?
            ''', (dashboard,))
        else:
            cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) as unresolved
            FROM feedback
            ''')

        result = cursor.fetchone()
        conn.close()

        total = result[0] or 0
        resolved = result[1] or 0
        unresolved = result[2] or 0

        return {
            'total': total,
            'resolved': resolved,
            'unresolved': unresolved,
            'resolution_rate': round((resolved / total * 100), 2) if total > 0 else 0.0
        }

    def get_recent_feedback(self, limit: int = 10, dashboard: Optional[str] = None) -> List[Dict]:
        """
        Get recent feedback entries

        Args:
            limit: Maximum number of entries to return
            dashboard: Optional dashboard name to filter by

        Returns:
            List of feedback entries as dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        if dashboard:
            cursor.execute('''
            SELECT * FROM feedback
            WHERE dashboard = ?
            ORDER BY timestamp DESC
            LIMIT ?
            ''', (dashboard, limit))
        else:
            cursor.execute('''
            SELECT * FROM feedback
            ORDER BY timestamp DESC
            LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_unresolved_issues(self, dashboard: Optional[str] = None) -> List[Dict]:
        """
        Get all unresolved issues

        Args:
            dashboard: Optional dashboard name to filter by

        Returns:
            List of unresolved feedback entries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if dashboard:
            cursor.execute('''
            SELECT * FROM feedback
            WHERE dashboard = ? AND resolved = 0
            ORDER BY timestamp DESC
            ''', (dashboard,))
        else:
            cursor.execute('''
            SELECT * FROM feedback
            WHERE resolved = 0
            ORDER BY timestamp DESC
            ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def export_to_csv(self, output_path: str, dashboard: Optional[str] = None):
        """
        Export feedback to CSV file

        Args:
            output_path: Path to output CSV file
            dashboard: Optional dashboard name to filter by
        """
        import csv

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if dashboard:
            cursor.execute('SELECT * FROM feedback WHERE dashboard = ? ORDER BY timestamp DESC', (dashboard,))
        else:
            cursor.execute('SELECT * FROM feedback ORDER BY timestamp DESC')

        rows = cursor.fetchall()

        if rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows([dict(row) for row in rows])

        conn.close()
        print(f"Exported {len(rows)} feedback entries to {output_path}")


if __name__ == '__main__':
    # Test the feedback logger
    print("Testing Feedback Logger...")
    print("=" * 60)

    logger = FeedbackLogger()

    # Log some test feedback
    print("\n1. Logging test feedback entries...")
    logger.log_feedback(
        dashboard='sales_dashboard',
        query='Dashboard showing blank Q4 values',
        response='Check the Date Range End parameter',
        resolved=True,
        comments='Worked perfectly!'
    )

    logger.log_feedback(
        dashboard='sales_dashboard',
        query='Slow performance',
        response='Optimize your data source connections',
        resolved=False,
        comments='Still slow after trying this'
    )

    logger.log_feedback(
        dashboard='customer_prep_flow',
        query='Join step failing',
        response='Check for null values in join keys',
        resolved=True
    )

    # Get stats
    print("\n2. Getting feedback statistics...")
    all_stats = logger.get_feedback_stats()
    print(f"Overall stats: {all_stats}")

    sales_stats = logger.get_feedback_stats('sales_dashboard')
    print(f"Sales dashboard stats: {sales_stats}")

    # Get recent feedback
    print("\n3. Getting recent feedback...")
    recent = logger.get_recent_feedback(limit=5)
    print(f"Found {len(recent)} recent entries")
    if recent:
        print(f"Latest: {recent[0]['user_query'][:50]}...")

    # Get unresolved
    print("\n4. Getting unresolved issues...")
    unresolved = logger.get_unresolved_issues()
    print(f"Found {len(unresolved)} unresolved issues")

    print("\n" + "=" * 60)
    print("[OK] Feedback Logger test complete!")
    print(f"Database location: {logger.db_path}")
