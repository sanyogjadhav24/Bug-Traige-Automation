from loguru import logger

try:
    from jira import JIRA, JIRAError
except ImportError:
    JIRA = None
    JIRAError = Exception

# Direct Jira configuration
JIRA_URL = "https://jadhavsanyog400.atlassian.net"
JIRA_TOKEN = "ATATT3xFfGF0q3aaHNhw1wSXy56zrDLRNoJFJ-Je4BB_VLSNZiOVzgetkZ33eCMM3lZjh-vcxsC9chiuflTtve0blQ8I8CHnLAWinRzJaFIY9o9iVTa6O9sUpezLwfS8f8VvKQLIctBFZ8kCR3aQnkASxyso0fk1w6vksCYlDf0psf3WAW9lbiU=0AABF31C"
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
    """Get configured JIRA client instance."""
    if not JIRA:
        logger.warning("Jira library not installed; running in dry-run mode.")
        return None
    
    if not (JIRA_URL and JIRA_TOKEN and JIRA_USER):
        logger.warning("Jira not fully configured; running in dry-run mode. Set JIRA_URL, JIRA_USER, and JIRA_TOKEN.")
        return None
    
    try:
        return JIRA(server=JIRA_URL, basic_auth=(JIRA_USER, JIRA_TOKEN))
    except Exception as e:
        logger.error(f"Failed to initialize JIRA client: {e}")
        return None


def check_jira_access(project_key: str = None) -> bool:
    """Check if configured credentials have CREATE_ISSUES permission for the project."""
    client = get_client()
    if client is None:
        return False
    
    try:
        # Verify authentication
        client.myself()
        
        # Check CREATE_ISSUES permission
        project = project_key or JIRA_PROJECT
        perms = client.my_permissions(permissions=["CREATE_ISSUES"], projectKey=project)
        create_perm = perms.get("permissions", {}).get("CREATE_ISSUES", {})
        has_permission = create_perm.get("havePermission", False)
        
        logger.info(f"CREATE_ISSUES permission for project {project}: {has_permission}")
        return bool(has_permission)
        
    except JIRAError as je:
        if "401" in str(je) or "AUTHENTICATED_FAILED" in str(je):
            logger.error("Jira authentication failed. Check JIRA_USER/JIRA_TOKEN environment variables.")
        else:
            logger.error(f"Jira permission check failed: {je}")
        return False
    except Exception as e:
        logger.error(f"Failed to check Jira permissions: {e}")
        return False


def set_assignee(issue, assignee_email: str):
    """Resolve Jira user by email and assign to issue."""
    client = get_client()
    if client is None:
        logger.warning("Cannot set assignee - Jira client not available.")
        return
    
    try:
        users = client.search_users(query=assignee_email)
        if not users:
            logger.warning(f"No Jira user found for email: {assignee_email}")
            return
            
        account_id = users[0].accountId
        issue.update(fields={"assignee": {"id": account_id}})
        logger.info(f"Assigned issue {issue.key} to {assignee_email}")
        
    except Exception as e:
        logger.warning(f"Failed to set assignee {assignee_email}: {e}")


def create_issue(summary: str, description: str, category: str = "", severity: str = "", assignee: str = None) -> str:
    """Create a new Jira issue with AI predictions."""
    client = get_client()
    if client is None:
        logger.info(f"[DRY-RUN] Would create issue: {summary}")
        return None
    
    try:
        priority_value = SEVERITY_TO_PRIORITY.get(severity, {"name": "Medium"})
        
        issue_description = f"{description}"
        if category or severity or assignee:
            issue_description += f"\n\n--- AI Triage Results ---"
            if category:
                issue_description += f"\nCategory: {category}"
            if severity:
                issue_description += f"\nSeverity: {severity}"
            if assignee:
                issue_description += f"\nRecommended Assignee: {assignee}"
        
        fields = {
            "project": {"key": JIRA_PROJECT},
            "summary": summary,
            "description": issue_description,
            "issuetype": {"name": "Task"},
            "priority": priority_value,
        }
        
        issue = client.create_issue(fields=fields)
        
        # Set assignee if specified and not "unassigned"
        if assignee and assignee.lower() != "unassigned":
            set_assignee(issue, assignee)
            
        logger.info(f"Successfully created Jira issue {issue.key}")
        return issue.key
        
    except JIRAError as je:
        logger.error(f"Failed to create Jira issue: {je}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating Jira issue: {e}")
        return None


def update_issue(issue_key: str, fields: dict = None, comment: str = None) -> bool:
    """Update an existing Jira issue with new fields or comments."""
    client = get_client()
    if client is None:
        logger.info(f"[DRY-RUN] Would update issue {issue_key}")
        return True
    
    try:
        issue = client.issue(issue_key)
        
        if fields:
            issue.update(fields=fields)
            
        if comment:
            client.add_comment(issue, comment)
            
        logger.info(f"Successfully updated Jira issue {issue_key}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update Jira issue {issue_key}: {e}")
        return False