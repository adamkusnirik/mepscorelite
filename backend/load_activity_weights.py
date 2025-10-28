#!/usr/bin/env python3
"""
Define activity and role weights for MEP ranking calculation.
These weights are used to calculate the total score for each MEP.
"""

# Activity and role weights used for ranking calculation
WEIGHTS = {
    # Activities
    "speeches": 1,                # CRE entries
    "reports_rapporteur": 5,      # REPORT entries
    "reports_shadow": 3,          # REPORT-SHADOW entries
    "amendments": 1,              # From amendments dataset
    "questions_written": 1,       # WQ entries
    "questions_oral": 2,          # OQ entries
    "questions_major": 3,         # MINT entries
    "motions": 2,                # MOTION entries
    "motions_individual": 1,      # IMOTION entries
    "opinions_rapporteur": 3,     # COMPARL entries
    "opinions_shadow": 2,         # COMPARL-SHADOW entries
    "declarations": 1,            # WDECL entries
    "explanations": 1,            # WEXP entries
    
    # Committee roles
    "committee_chair": 10,
    "committee_vice_chair": 7,
    "committee_member": 5,
    "committee_substitute": 3,
    "committee_rapporteur": 8,
    "committee_shadow": 6,
    
    # Delegation roles
    "delegation_chair": 8,
    "delegation_vice_chair": 6,
    "delegation_member": 4,
    "delegation_substitute": 2,
    
    # EP-level roles
    "ep_president": 15,
    "ep_vice_president": 12,
    "ep_quaestor": 10,
    "ep_chair_conference": 10,    # Conference chairs (e.g., Conference of Committee Chairs)
    "ep_group_chair": 10,         # Political group chairs
    "ep_group_vice_chair": 8,     # Political group vice-chairs
    
    # Staff roles
    "staff_head": 5,              # Head of unit/service
    "staff_advisor": 3,           # Senior advisor/coordinator
    "staff_assistant": 1,         # Assistant/administrative staff
}

def get_weights():
    """
    Return the weights dictionary.
    
    Returns:
        dict: Dictionary mapping activity/role types to their weights
    """
    return WEIGHTS 