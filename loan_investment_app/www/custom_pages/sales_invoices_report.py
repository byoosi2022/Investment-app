import frappe
from frappe.utils import today

@frappe.whitelist()
def get_logged_in_user_info():
    user = frappe.get_doc("User", frappe.session.user)
    current_date = today()
    
    user_info = {
        "email": user.email,
        "current_date": current_date
    }
    
    # Fetch user permissions related to the investment account where 'allow' is 'Member'
    investment_account = frappe.db.sql("""
        SELECT for_value, allow, user
        FROM `tabUser Permission`
        WHERE user = %s AND allow = 'Member'
    """, (user_info["email"],), as_dict=True)

    # Initialize member_name as None
    member_name = None

    # Fetch member name if an investment account was found
    if investment_account:
        member_data = frappe.db.sql("""
            SELECT member_name
            FROM `tabMember`
            WHERE name = %s
        """, (investment_account[0].for_value,), as_dict=True)

        # Check if member_data is found and set member_name
        if member_data:
            member_name = member_data[0].member_name

    user_info2 = {
        "member": investment_account[0].for_value if investment_account else None,
        "current_date": current_date,
        "member_name": member_name
    }

    return user_info2

def get_context(context):
    # Get the logged-in user's information
    user_info = get_logged_in_user_info()
    specific_party = user_info['member']  # Filter by the logged-in user's member

    # Fetch report data from the 'Investment App' doctype for the specific party
    context.report_data = frappe.get_list(
        'Investment App',  # Replace with your doctype
        fields=['party_name', 'party', 'posting_date', 'transaction_type', 'amount'],
        filters={
            'party': specific_party,  # Filter by specific party
            # 'transaction_type': 'Re-invest'  # Filter by transaction type
        },
        limit_page_length=50  # Limit the number of records to retrieve
    )

    # Title for the report
    context.title = "Investment Report"
