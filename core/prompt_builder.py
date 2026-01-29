"""
Prompt Builder: Constructs prompts with system instructions + context + user query
"""

from typing import Dict, Optional, List
import os


class PromptBuilder:
    """Builds prompts for Tableau troubleshooting with context injection"""

    SYSTEM_PROMPT_TEMPLATE = """You are an expert Tableau troubleshooting assistant for Deutsche Bank's internal team.

Your role is to help users diagnose and resolve issues with Tableau Dashboards and Prep Flows.

You have access to:
1. Complete technical metadata about the dashboard/flow (data sources, calculated fields, joins, parameters, filters, etc.)
2. Historical issues and their resolutions from past troubleshooting sessions

Guidelines:
- Provide clear, actionable troubleshooting steps
- Reference specific components from the metadata when relevant (e.g., calculated field names, data sources, parameters)
- Draw insights from similar historical issues when applicable
- If you're uncertain, suggest diagnostic steps to gather more information
- Keep responses concise but comprehensive
- Use bullet points and numbered lists for multi-step solutions
- Always be professional and helpful

When answering:
1. Acknowledge the user's issue
2. Identify potential root causes based on the context provided
3. Provide step-by-step resolution or troubleshooting steps
4. Reference similar past issues if relevant
5. Suggest verification steps to confirm the fix worked

Remember: You're helping colleagues troubleshoot production dashboards, so accuracy and clarity are critical."""

    USER_PROMPT_TEMPLATE = """Dashboard/Flow Context:
{context}

---

User's Issue:
{user_query}

Please provide troubleshooting guidance based on the context above."""

    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize prompt builder

        Args:
            system_prompt: Custom system prompt (optional, uses default if not provided)
        """
        self.system_prompt = system_prompt or self.SYSTEM_PROMPT_TEMPLATE

    def build_prompt(self, context: str, user_query: str,
                    chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, str]:
        """
        Build complete prompt with system instructions, context, and query

        Args:
            context: Formatted context string (metadata + historical issues)
            user_query: The user's question/issue description
            chat_history: Optional list of previous chat exchanges

        Returns:
            Dict with 'system' and 'user' keys for prompt components
        """
        user_message = self.USER_PROMPT_TEMPLATE.format(
            context=context,
            user_query=user_query
        )

        # If chat history exists, prepend it to user message
        if chat_history and len(chat_history) > 0:
            history_text = self._format_chat_history(chat_history)
            user_message = f"{history_text}\n\n---\n\n{user_message}"

        return {
            'system': self.system_prompt,
            'user': user_message
        }

    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """
        Format chat history for context

        Args:
            chat_history: List of dicts with 'role' and 'content' keys

        Returns:
            Formatted history string
        """
        max_history = int(os.getenv('MAX_CHAT_HISTORY', '4'))

        # Only include last N exchanges
        recent_history = chat_history[-max_history:] if len(chat_history) > max_history else chat_history

        formatted = ["Previous Conversation:"]
        for entry in recent_history:
            role = "User" if entry['role'] == 'user' else "Assistant"
            content = entry['content']
            # Truncate very long messages
            if len(content) > 500:
                content = content[:497] + "..."
            formatted.append(f"\n{role}: {content}")

        return "\n".join(formatted)

    def build_few_shot_examples(self) -> str:
        """
        Optional: Add few-shot examples for better prompt engineering

        Returns:
            String containing example troubleshooting exchanges
        """
        examples = """
# Example Troubleshooting Exchanges

Example 1:
User: "The sales dashboard is showing blank values for Q4 2025"
Assistant: Based on the metadata, your dashboard uses the parameter [Date Range End]. Common causes for blank Q4 data:
1. Check if the parameter date range includes Q4 2025 (Oct-Dec)
   - Navigate to the parameter controls
   - Verify "Date Range End" is set to at least 2025-12-31
2. Verify the data source connection has recent data
   - Check if the SalesDB database contains Q4 2025 records
3. Review the calculated field [YTD Sales] for date logic issues
   - The formula uses date comparisons that might exclude Q4

Example 2:
User: "Prep flow is failing at the join step"
Assistant: Looking at your flow, Step 4 performs a LEFT JOIN between Customer Data and Order Data on CustomerID. Common join failure causes:
1. Null values in join keys
   - Add a Clean step before the join to remove nulls from CustomerID fields
2. Data type mismatch between join fields
   - Verify both CustomerID columns are the same data type (e.g., both INTEGER)
3. Duplicate keys causing cartesian product
   - Add an Aggregate step to deduplicate before joining

Example 3:
User: "Calculated field showing unexpected negative values"
Assistant: Your calculated field [Profit Margin] uses the formula `[Profit] / [Sales]`. Negative values can occur when:
1. Division by zero returns NULL or negative
   - Update formula to: `IF [Sales] = 0 THEN 0 ELSE [Profit] / [Sales] END`
2. Profit field contains negative values (returns/losses)
   - This is expected for loss-making transactions
3. Data quality issue in source
   - Check the source data for anomalies in Profit and Sales columns
"""
        return examples


if __name__ == '__main__':
    # Test the prompt builder
    print("Testing Prompt Builder...")
    print("=" * 60)

    builder = PromptBuilder()

    # Test basic prompt
    context = """# Tableau Workbook: Sales Dashboard

## Data Sources:
- Sales Data: sqlserver - SalesDB @ sql-server-01

## Calculated Fields:
- Profit Margin: `[Profit] / [Sales]`

## Parameters:
- Date Range End (date) = 2025-09-30"""

    user_query = "Dashboard showing blank values for Q4 2025"

    prompt = builder.build_prompt(context, user_query)

    print("\nSYSTEM PROMPT:")
    print(prompt['system'][:200] + "...\n")

    print("\nUSER PROMPT:")
    print(prompt['user'][:400] + "...\n")

    # Test with chat history
    chat_history = [
        {"role": "user", "content": "Why is my dashboard slow?"},
        {"role": "assistant", "content": "Check your data source connections and filters."}
    ]

    prompt_with_history = builder.build_prompt(context, user_query, chat_history)
    print("\nUSER PROMPT WITH HISTORY:")
    print(prompt_with_history['user'][:400] + "...\n")

    print("=" * 60)
    print("[OK] Prompt Builder test complete!")
