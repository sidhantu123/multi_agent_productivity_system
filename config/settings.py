"""Configuration settings for the Gmail agent application"""

# LangGraph configuration
THREAD_ID = "gmail_conversation_1"
INTERRUPT_BEFORE = ["user_input"]

# Display settings
SEPARATOR_LENGTH = 80
MEMORY_SEPARATOR_LENGTH = 60

# Gmail configuration
GOOGLE_CREDENTIALS_PATH = "config/google_credentials.json"
GOOGLE_TOKEN_PATH = "config/google_token.json"

