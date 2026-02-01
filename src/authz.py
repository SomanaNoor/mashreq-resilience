"""
Authorization Module - Stage 10: Logic & Security
==================================================
Implements Role-Based Access Control (RBAC) for the pipeline.

Roles:
- ANALYST: Can view data and RECOMMEND decisions.
- REVIEWER: Can view data and APPROVE/DISMISS decisions.
- ADMIN: Full access.

Responsible AI Mapping:
- Governance: Enforces human oversight hierarchy.
"""

from enum import Enum
from typing import Dict, List, Optional

class Role(Enum):
    ANALYST = "analyst"
    REVIEWER = "reviewer"
    ADMIN = "admin"
    SYSTEM = "system"

class Action(Enum):
    VIEW = "view"
    RECOMMEND = "recommend"
    APPROVE = "approve"
    DISMISS = "dismiss"
    EXPORT = "export"

# Policy Matrix
# Role -> Allowed Actions
RBAC_POLICY: Dict[Role, List[Action]] = {
    Role.ANALYST: [Action.VIEW, Action.RECOMMEND, Action.EXPORT],
    Role.REVIEWER: [Action.VIEW, Action.RECOMMEND, Action.APPROVE, Action.DISMISS, Action.EXPORT],
    Role.ADMIN: [Action.VIEW, Action.RECOMMEND, Action.APPROVE, Action.DISMISS, Action.EXPORT],
    Role.SYSTEM: [Action.VIEW, Action.RECOMMEND, Action.APPROVE, Action.DISMISS] # System needs full rights for automation if needed
}

def check_permission(role_str: str, action: Action) -> bool:
    """
    Check if a role is authorized to perform an action.
    
    Args:
        role_str: Role string (e.g. 'analyst')
        action: Action enum
        
    Returns:
        bool: True if authorized
    """
    try:
        role = Role(role_str.lower())
    except ValueError:
        return False
        
    allowed_actions = RBAC_POLICY.get(role, [])
    return action in allowed_actions

def validate_decision_authority(role_str: str, decision: str) -> bool:
    """
    Validate if a role can make a specific decision.
    
    Args:
        role_str: Role string
        decision: 'APPROVED', 'DISMISSED', 'MORE_REVIEW'
        
    Returns:
        bool: True if authorized
    """
    if decision == 'MORE_REVIEW':
        return check_permission(role_str, Action.RECOMMEND)
    
    if decision in ['APPROVED', 'DISMISSED']:
        return check_permission(role_str, Action.APPROVE) or check_permission(role_str, Action.DISMISS)
        
    return False
