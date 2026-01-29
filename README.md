# Tableau Issue-Resolution Chatbot

AI-powered troubleshooting assistant for Tableau Dashboards and Prep Flows, built for Deutsche Bank's internal team.

## Overview

This chatbot helps users diagnose and resolve issues with Tableau dashboards and Prep flows by:
- Analyzing pre-parsed Tableau metadata (data sources, calculated fields, joins, parameters, etc.)
- Referencing historical issues and their resolutions
- Providing contextual troubleshooting guidance using LLM

## Features

- **Smart Context Retrieval**: Automatically loads relevant dashboard metadata and historical issues
- **Conversational Interface**: Streamlit-based chat UI for natural troubleshooting conversations
- **Historical Learning**: References past issues and resolutions specific to each dashboard
- **Feedback System**: Tracks resolution rates and user satisfaction
- **Flexible LLM Integration**: Supports multiple API formats for LLM connectivity

## Quick Start

### 1. Installation

```bash
# Clone or navigate to the repository
cd tableau-chatbot

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure with your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your LLM credentials:

```env
EMAIL_ACC=your.email@db.com
LLM_API_KEY=your_api_key_here
LLM_API_URL=https://api.uat1.mlcore.uat.gcp.db.com/api/llm/process
LLM_MODEL=gemini-2.5-flash
KANNON_ID=2010.045
```

### 3. Generate Mock Data (for testing)

```bash
python scripts/generate_mock_data.py
```

This creates:
- Sample Tableau workbook XML (`data/mock_samples/sample_workbook.twb`)
- Sample Prep flow XML (`data/mock_samples/sample_prepflow.tfl`)
- Historical issues Excel file (`data/historical_issues/issues_export.xlsx`)

### 4. Parse Tableau Files

Parse your actual Tableau files to extract metadata:

```bash
# For workbooks
python parsers/workbook_parser.py data/mock_samples/sample_workbook.twb sales_dashboard data/parsed_metadata/workbooks

# For prep flows
python parsers/prep_flow_parser.py data/mock_samples/sample_prepflow.tfl customer_prep_flow data/parsed_metadata/prep_flows
```

### 5. Run the Application

```bash
streamlit run ui/app.py
```

The application will open in your browser at `http://localhost:8501`

## Project Structure

```
tableau-chatbot/
├── config/
│   ├── settings.py               # Central configuration
│   └── dashboard_registry.json   # Dashboard metadata registry
├── data/
│   ├── parsed_metadata/          # Pre-processed Tableau metadata (JSON)
│   ├── historical_issues/        # Excel exports from SharePoint
│   ├── mock_samples/             # Mock Tableau XML for testing
│   └── feedback_logs/            # User feedback database
├── parsers/
│   ├── workbook_parser.py        # Extract from .twb/.twbx files
│   └── prep_flow_parser.py       # Extract from .tfl/.tflx files
├── core/
│   ├── llm_adapter.py            # Flexible LLM integration
│   ├── context_manager.py        # Load & combine contexts
│   ├── prompt_builder.py         # Construct prompts
│   └── feedback_logger.py        # Log user feedback
├── ui/
│   └── app.py                    # Main Streamlit application
└── scripts/
    └── generate_mock_data.py     # Create mock Tableau XMLs
```

## Adding New Dashboards

### Step 1: Parse Tableau File

```bash
python parsers/workbook_parser.py path/to/your/dashboard.twb your_dashboard_name data/parsed_metadata/workbooks
```

### Step 2: Add to Dashboard Registry

Edit `config/dashboard_registry.json`:

```json
{
  "dashboards": [
    {
      "name": "your_dashboard_name",
      "display_name": "Your Dashboard Display Name",
      "type": "workbook",
      "description": "Brief description of what this dashboard does",
      "owner": "Team Name",
      "source_file": "dashboard.twb"
    }
  ]
}
```

### Step 3: Restart Application

Restart the Streamlit app to load the new dashboard.

## Updating Historical Issues

### Option 1: Manual Update

1. Export issues from SharePoint to Excel
2. Ensure column names match:
   - `Dashboard/Workflow Name`
   - `Issue Description`
   - `Root Cause`
   - `Resolution`
3. Replace `data/historical_issues/issues_export.xlsx`
4. No restart needed - loaded dynamically

### Option 2: Automated Update (Future)

Create a script to fetch from SharePoint API:

```python
# scripts/update_issues.py
import pandas as pd
from sharepoint_api import download_export

def update_issues():
    df = download_export('https://sharepoint.db.com/...')
    df.to_excel('data/historical_issues/issues_export.xlsx', index=False)
```

## Configuration Options

Edit `.env` to customize behavior:

```env
# LLM Parameters
LLM_TEMPERATURE=0.7        # Lower = more focused, Higher = more creative
LLM_MAX_TOKENS=2048        # Maximum response length
LLM_ADAPTER_TYPE=auto      # auto, openai, custom, sdk

# Context Configuration
MAX_HISTORICAL_ISSUES=5    # Number of past issues to include
MAX_CHAT_HISTORY=4         # Number of previous exchanges to remember
```

## Troubleshooting

### LLM Connection Failed

**Problem:** "Failed to connect to LLM"

**Solution:**
1. Verify `LLM_API_KEY` and `LLM_API_URL` are correct in `.env`
2. Check network connectivity to the API endpoint
3. Ensure `EMAIL_ACC` matches your Deutsche Bank email

### Dashboard Metadata Not Found

**Problem:** "Metadata file not found"

**Solution:**
1. Ensure you've parsed the Tableau file using the parser scripts
2. Check that the dashboard name in `dashboard_registry.json` matches the parsed JSON filename
3. Verify JSON file exists in `data/parsed_metadata/workbooks/` or `data/parsed_metadata/prep_flows/`

### Historical Issues Not Loading

**Problem:** No historical issues displayed

**Solution:**
1. Verify `issues_export.xlsx` exists in `data/historical_issues/`
2. Check that column names match expected schema:
   - `Dashboard/Workflow Name`
   - `Issue Description`
   - `Root Cause`
   - `Resolution`
3. Ensure dashboard name in Excel matches the dashboard registry name

## Testing Components

### Test XML Parsers

```bash
# Test workbook parser
python parsers/workbook_parser.py data/mock_samples/sample_workbook.twb test_dashboard

# Test prep flow parser
python parsers/prep_flow_parser.py data/mock_samples/sample_prepflow.tfl test_flow
```

### Test Context Manager

```bash
python core/context_manager.py
```

### Test LLM Adapter

```bash
python core/llm_adapter.py
```

### Test Prompt Builder

```bash
python core/prompt_builder.py
```

### Test Feedback Logger

```bash
python core/feedback_logger.py
```

## Deployment to DaS Platform

### Prerequisites

1. Package all dependencies in `requirements.txt`
2. Configure environment variables in DaS secrets
3. Upload Tableau metadata JSON files

### Deployment Steps

1. **Package Application:**
   ```bash
   zip -r tableau-chatbot.zip . -x "*.pyc" "*__pycache__*" ".git/*" "*.db"
   ```

2. **Upload to DaS:**
   - Navigate to DaS portal
   - Create new application
   - Upload `tableau-chatbot.zip`
   - Set Python version: 3.9+

3. **Configure Secrets:**
   - Add `LLM_API_KEY` to DaS secrets
   - Add `LLM_API_URL` to DaS secrets
   - Add `EMAIL_ACC` to DaS secrets
   - Add `KANNON_ID` to DaS secrets

4. **Set Entry Point:**
   ```bash
   streamlit run ui/app.py --server.port 8501
   ```

5. **Test Deployment:**
   - Access application URL
   - Verify LLM connectivity
   - Test dashboard loading
   - Submit test query

## Analytics & Monitoring

### View Feedback Statistics

Access the feedback database:

```python
from core.feedback_logger import FeedbackLogger

logger = FeedbackLogger()
stats = logger.get_feedback_stats()  # Overall stats
stats_by_dashboard = logger.get_feedback_stats('sales_dashboard')  # Per dashboard

print(f"Resolution Rate: {stats['resolution_rate']}%")
```

### Export Feedback to CSV

```python
logger.export_to_csv('feedback_export.csv')
```

### View Unresolved Issues

```python
unresolved = logger.get_unresolved_issues()
for issue in unresolved:
    print(f"{issue['timestamp']}: {issue['user_query']}")
```

## Architecture

### Data Flow

1. **User selects dashboard** → Loads `dashboard_registry.json`
2. **User asks question** → Triggers context retrieval
3. **Context Manager** → Loads metadata JSON + filters historical issues
4. **Prompt Builder** → Combines system prompt + context + user query
5. **LLM Adapter** → Sends to LLM API
6. **Response displayed** → Shows in chat interface
7. **User provides feedback** → Logs to SQLite database

### Components

- **Parsers**: Extract metadata from Tableau XML files → JSON
- **Context Manager**: Combine metadata + historical issues → formatted context
- **Prompt Builder**: Construct prompts with context injection
- **LLM Adapter**: Flexible API integration with auto-fallback
- **Feedback Logger**: Track user satisfaction and resolution rates
- **Streamlit UI**: Chat interface with sidebar configuration

## Best Practices

### For End Users

1. **Be specific**: Describe the exact issue you're seeing
2. **Include details**: Error messages, affected data, time ranges
3. **Provide feedback**: Click Yes/No to help improve responses
4. **Try suggestions**: Follow troubleshooting steps in order

### For Administrators

1. **Keep metadata current**: Re-parse dashboards after major changes
2. **Update historical issues regularly**: Export from SharePoint monthly
3. **Monitor feedback stats**: Identify dashboards with low resolution rates
4. **Review unresolved issues**: Improve prompts based on failures
5. **Validate parsed metadata**: Spot-check JSON files for accuracy

## Future Enhancements

- [ ] Streaming responses for better UX
- [ ] Multi-file batch parsing
- [ ] Direct SharePoint API integration
- [ ] Advanced analytics dashboard
- [ ] User authentication and personalization
- [ ] Integration with ticketing system
- [ ] Tableau Server API for live metadata

## Support

For issues or questions:
- **Internal Team**: Contact Data Analytics Team
- **GitHub Issues**: [Report bugs or request features]
- **Documentation**: Refer to this README and inline code comments

## License

For Internal Use Only - Deutsche Bank

---

**Version:** 1.0.0
**Last Updated:** 2026-01-29
**Maintained by:** Data Analytics Team
