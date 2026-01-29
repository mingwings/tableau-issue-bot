"""
Main Streamlit Application for Tableau Troubleshooting Assistant
"""

import streamlit as st
from pathlib import Path
import sys
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.context_manager import ContextManager
from core.prompt_builder import PromptBuilder
from core.llm_adapter import LLMAdapterFactory
from core.feedback_logger import FeedbackLogger
from config.settings import SETTINGS, validate_settings

# Page configuration
st.set_page_config(
    page_title=SETTINGS['APP_TITLE'],
    page_icon=SETTINGS['APP_ICON'],
    layout=SETTINGS['LAYOUT']
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'selected_dashboard' not in st.session_state:
    st.session_state.selected_dashboard = None
if 'selected_dashboard_type' not in st.session_state:
    st.session_state.selected_dashboard_type = None
if 'llm_adapter' not in st.session_state:
    st.session_state.llm_adapter = None
if 'context_manager' not in st.session_state:
    st.session_state.context_manager = None
if 'prompt_builder' not in st.session_state:
    st.session_state.prompt_builder = None
if 'feedback_logger' not in st.session_state:
    st.session_state.feedback_logger = None
if 'show_feedback_form' not in st.session_state:
    st.session_state.show_feedback_form = {}
if 'initialization_complete' not in st.session_state:
    st.session_state.initialization_complete = False


def initialize_components():
    """Initialize all core components"""
    if st.session_state.initialization_complete:
        return True

    try:
        # Validate configuration
        if not validate_settings():
            st.error("Configuration validation failed. Please check your .env file.")
            st.stop()

        # Initialize components
        with st.spinner("Initializing components..."):
            st.session_state.context_manager = ContextManager()
            st.session_state.prompt_builder = PromptBuilder()
            st.session_state.feedback_logger = FeedbackLogger()

        # Initialize LLM adapter
        with st.spinner("Connecting to LLM..."):
            st.session_state.llm_adapter = LLMAdapterFactory.create_adapter()

            if not st.session_state.llm_adapter.validate_connection():
                st.error("Failed to connect to LLM. Please check your API credentials in .env file.")
                st.stop()

        st.session_state.initialization_complete = True
        st.success("Successfully initialized! Ready to help with Tableau troubleshooting.")
        return True

    except Exception as e:
        st.error(f"Initialization failed: {e}")
        st.stop()
        return False


def load_dashboard_registry():
    """Load dashboard registry from JSON file"""
    registry_path = SETTINGS['DASHBOARD_REGISTRY']

    if not registry_path.exists():
        st.error(f"Dashboard registry not found at {registry_path}")
        st.info("Please create config/dashboard_registry.json with your dashboards.")
        st.stop()

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        return registry.get('dashboards', [])
    except Exception as e:
        st.error(f"Error loading dashboard registry: {e}")
        st.stop()


def main():
    """Main application logic"""

    # Header
    st.title(f"{SETTINGS['APP_ICON']} {SETTINGS['APP_TITLE']}")
    st.markdown("---")

    # Initialize components
    initialize_components()

    # Sidebar
    with st.sidebar:
        st.header("Configuration")

        # Dashboard selector
        st.subheader("Select Dashboard/Workflow")
        dashboards = load_dashboard_registry()

        if not dashboards:
            st.warning("No dashboards configured. Please add dashboards to config/dashboard_registry.json")
            st.stop()

        dashboard_options = {d['display_name']: d for d in dashboards}
        selected_display_name = st.selectbox(
            "Choose Dashboard:",
            options=list(dashboard_options.keys()),
            index=0
        )

        selected_dashboard = dashboard_options[selected_display_name]

        # If dashboard changed, clear chat history
        if (st.session_state.selected_dashboard != selected_dashboard['name'] or
            st.session_state.selected_dashboard_type != selected_dashboard['type']):

            st.session_state.selected_dashboard = selected_dashboard['name']
            st.session_state.selected_dashboard_type = selected_dashboard['type']
            st.session_state.chat_history = []
            st.session_state.show_feedback_form = {}

        # Dashboard info
        st.markdown("---")
        st.info(f"**Type:** {selected_dashboard['type'].replace('_', ' ').title()}")
        st.caption(f"**Owner:** {selected_dashboard.get('owner', 'N/A')}")
        st.caption(selected_dashboard.get('description', ''))

        # Stats (if available)
        st.markdown("---")
        st.subheader("Feedback Stats")
        stats = st.session_state.feedback_logger.get_feedback_stats(st.session_state.selected_dashboard)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Queries", stats['total'])
        with col2:
            st.metric("Resolution Rate", f"{stats['resolution_rate']}%")

    # Main content area
    st.markdown(f"### {selected_display_name}")
    st.caption("Ask me about any issues you're experiencing with this dashboard or workflow.")

    # Display chat history
    for idx, entry in enumerate(st.session_state.chat_history):
        with st.chat_message(entry['role']):
            st.markdown(entry['content'])

            # Show feedback widget for assistant messages
            if entry['role'] == 'assistant' and SETTINGS['ENABLE_FEEDBACK']:
                feedback_key = f"feedback_{idx}"

                if feedback_key not in st.session_state.show_feedback_form:
                    st.markdown("---")
                    st.markdown("**Did this resolve your issue?**")

                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("✓ Yes", key=f"yes_{idx}"):
                            # Log positive feedback
                            user_query = st.session_state.chat_history[idx - 1]['content'] if idx > 0 else ""
                            st.session_state.feedback_logger.log_feedback(
                                dashboard=st.session_state.selected_dashboard,
                                query=user_query,
                                response=entry['content'],
                                resolved=True
                            )
                            st.success("Thanks for the feedback!")
                            st.session_state.show_feedback_form[feedback_key] = 'submitted'
                            st.rerun()

                    with col2:
                        if st.button("✗ No", key=f"no_{idx}"):
                            st.session_state.show_feedback_form[feedback_key] = 'show'
                            st.rerun()

                # Show feedback form if "No" was clicked
                if st.session_state.show_feedback_form.get(feedback_key) == 'show':
                    feedback_comment = st.text_area(
                        "What could be improved?",
                        key=f"comment_{idx}",
                        placeholder="Please describe what didn't work or what additional help you need..."
                    )
                    if st.button("Submit Feedback", key=f"submit_{idx}"):
                        user_query = st.session_state.chat_history[idx - 1]['content'] if idx > 0 else ""
                        st.session_state.feedback_logger.log_feedback(
                            dashboard=st.session_state.selected_dashboard,
                            query=user_query,
                            response=entry['content'],
                            resolved=False,
                            comments=feedback_comment
                        )
                        st.success("Feedback logged. Thank you!")
                        st.session_state.show_feedback_form[feedback_key] = 'submitted'
                        st.rerun()

    # Chat input
    if user_query := st.chat_input("Describe your issue..."):
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_query
        })

        # Display user message
        with st.chat_message('user'):
            st.markdown(user_query)

        # Generate response
        with st.chat_message('assistant'):
            with st.spinner("Analyzing context and generating response..."):
                try:
                    # Get context
                    context = st.session_state.context_manager.build_context_summary(
                        st.session_state.selected_dashboard,
                        st.session_state.selected_dashboard_type
                    )

                    # Build prompt
                    chat_history_for_prompt = st.session_state.chat_history[:-1]  # Exclude current query
                    prompt_components = st.session_state.prompt_builder.build_prompt(
                        context=context,
                        user_query=user_query,
                        chat_history=chat_history_for_prompt if SETTINGS['ENABLE_CHAT_HISTORY'] else None
                    )

                    # Generate response
                    response = st.session_state.llm_adapter.generate(
                        prompt=prompt_components['user'],
                        system_prompt=prompt_components['system'],
                        temperature=SETTINGS['LLM_TEMPERATURE'],
                        max_tokens=SETTINGS['LLM_MAX_TOKENS']
                    )

                    # Display response
                    st.markdown(response)

                    # Add to history
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response
                    })

                    # Rerun to show feedback widget
                    st.rerun()

                except Exception as e:
                    st.error(f"Error generating response: {e}")
                    st.error("Please check your configuration and try again.")

    # Footer
    st.markdown("---")
    st.caption("Powered by LLM | Built for Internal Use")


if __name__ == '__main__':
    main()
