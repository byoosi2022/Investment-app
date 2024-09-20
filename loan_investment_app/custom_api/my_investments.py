import frappe
from frappe import _

@frappe.whitelist()
def fetch_investments_for_party():
    # Get the logged-in user
    user = frappe.session.user

    # Check if the logged-in user has the "Investor" role
    if "Investor" in frappe.get_roles(user):
        # Get the member name associated with the user
        party = frappe.db.get_value("Member", {"owner": user}, "name")
        
        # If no party is found, return an empty list or handle accordingly
        if not party:
            return []

        # Fetch investments related to the specific party
        return frappe.get_list(
            'Investment App',
            fields=['name', 'end_date', 'posting_date', 'amount','party_name'],  # Added 'amount' field
            filters={
                'party': party,  # Filter by the specific party
                'transaction_type': ['in', ['Re-invest', 'Invest']],
                'docstatus': ['!=', 2],  # Exclude canceled records
                'investment_status': 'Approved'
            }
        )

    # If the user does not have the "Investor" role, return an empty list
    return []
