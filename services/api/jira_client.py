import os
from loguru import logger

try:
    from jira import JIRA
except Exception:
    JIRA = None

# Jira Config (move these into .env in production)
JIRA_URL = "https://jadhavsanyog400.atlassian.net"
JIRA_TOKEN = "ATATT3xFfGF0fEcOVW4_Z-KNMLd8YPTV2IeDmUedJdHPs7onE7Uos9LISYqfg3hhBfgGFOiBc_L9jfDroV_ZYam6XmRpzV25m_rF47-I8qOn4llu7CDL62b-aOuQjwnb1dVtXyxZzA0o-hdd8YMZr9v82O1_AAZ61oKM69D0TkCcI3F40S8wdkQ=C3ACE213"
JIRA_USER = "jadhavsanyog.400@gmail.com"
JIRA_PROJECT = "DEM"

# Severity → Priority mapping
SEVERITY_TO_PRIORITY = {
    "Critical": {"name": "Highest"},
    "Major": {"name": "High"},
    "Moderate": {"name": "Medium"},
    "Minor": {"name": "Low"},
    "Trivial": {"name": "Lowest"},
}


def get_client():
    if not (JIRA and JIRA_URL and (JIRA_TOKEN or JIRA_USER)):
        logger.warning("Jira not fully configured; running in dry-run mode.")
        return None
    try:
        if JIRA_TOKEN and JIRA_USER:
            return JIRA(server=JIRA_URL, basic_auth=(JIRA_USER, JIRA_TOKEN))
        return JIRA(server=JIRA_URL, token_auth=JIRA_TOKEN)
    except Exception as e:
        logger.error(f"Failed to init JIRA client: {e}")
        return None


def set_assignee(issue, assignee_email: str):
    """Resolve Jira accountId from email and assign user"""
    client = get_client()
    try:
        users = client.search_users(query=assignee_email)
        if not users:
            logger.warning(f"No Jira user found for {assignee_email}")
            return
        account_id = users[0].accountId
        issue.update(fields={"assignee": {"id": account_id}})
        logger.info(f"Assigned issue {issue.key} to {assignee_email} ({account_id})")
    except Exception as e:
        logger.warning(f"Assignee {assignee_email} not settable: {e}")


def create_issue(summary: str, description: str, category: str, severity: str, assignee: str | None = None):
    client = get_client()
    if client is None:
        logger.info(f"[DRY-RUN] Would create issue with summary={summary}")
        return None

    try:
        priority_value = SEVERITY_TO_PRIORITY.get(severity, {"name": "Medium"})

        fields = {
            "project": {"key": JIRA_PROJECT},
            "summary": summary,
            "description": f"{description}\n\nAI Triage Suggestion:\nCategory: {category}, Severity: {severity}, Assignee: {assignee}",
            "issuetype": {"name": "Task"},
            "priority": priority_value,
        }

        issue = client.create_issue(fields=fields)

        if assignee and assignee.lower() != "unassigned":
            set_assignee(issue, assignee)

        logger.info(f"Created Jira issue {issue.key}")
        return issue.key
    except Exception as e:
        logger.error(f"Jira create failed: {e}")
        return None


def update_issue(issue_key: str, fields: dict, comment: str | None = None):
    """Update an existing Jira issue"""
    client = get_client()
    if client is None:
        logger.info(f"[DRY-RUN] Would update {issue_key} with fields={fields}, comment={comment}")
        return True
    try:
        issue = client.issue(issue_key)
        if fields:
            issue.update(fields=fields)
        if comment:
            client.add_comment(issue, comment)
        logger.info(f"Updated Jira issue {issue_key}")
        return True
    except Exception as e:
        logger.error(f"Jira update failed: {e}")
        return False
