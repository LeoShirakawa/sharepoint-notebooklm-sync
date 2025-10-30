# Configuration for the application

# SharePoint Configuration
# These values must be populated from your Azure AD App Registration
SHAREPOINT_AUTHORITY = "YOUR_SHAREPOINT_AUTHORITY"
SHAREPOINT_CLIENT_ID = "YOUR_SHAREPOINT_CLIENT_ID"
# SHAREPOINT_CLIENT_SECRET is loaded from Secret Manager, not set here.
SHAREPOINT_SCOPE = ["https://graph.microsoft.com/.default"]

# The specific SharePoint site and folder to sync
SHAREPOINT_SITE_ID = "YOUR_SHAREPOINT_SITE_ID"
SHAREPOINT_FOLDER_ID = "YOUR_SHAREPOINT_FOLDER_ID"
SHAREPOINT_DRIVE_ID = "YOUR_SHAREPOINT_DRIVE_ID"

# NotebookLM Configuration
NOTEBOOK_ID = "YOUR_NOTEBOOK_ID"
PROJECT_NUMBER = "YOUR_PROJECT_NUMBER"
NOTEBOOK_LOCATION = "global"

# Email of the service account that has domain-wide delegation configured
# to impersonate USER_TO_IMPERSONATE. This needs to be provided by the user.
DELEGATOR_SERVICE_ACCOUNT_EMAIL = "YOUR_DELEGATOR_SERVICE_ACCOUNT_EMAIL"

# NotebookLM Enterprise API (Discovery Engine) のスコープ
NOTEBOOKLM_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# 代理となるユーザーのメールアドレス (DWDの 'subject')
USER_EMAIL_TO_IMPERSONATE = "YOUR_USER_EMAIL_TO_IMPERSONATE"
