"""
Story Consistency Layer v6.0 Configuration

Feature flags for controlling the Story Consistency Layer behavior.
"""

# Enable/disable the Story Consistency Layer
USE_STORY_CONSISTENCY_LAYER = True

# Automatically apply corrected narration when revisions are suggested
CONSISTENCY_AUTO_CORRECT = True

# Hard block DM output when critical issues are detected (False = warnings only)
CONSISTENCY_HARD_BLOCK = False

# Log level for consistency layer (INFO, WARNING, ERROR)
CONSISTENCY_LOG_LEVEL = "INFO"
