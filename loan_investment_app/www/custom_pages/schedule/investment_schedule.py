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

def get_context(context, posting_date=None):
    # Get the logged-in user's information
    user_info = get_logged_in_user_info()
    specific_party = user_info['member']  # Filter by the logged-in user's member

    # Fetch report data from the 'Investment App' doctype for the specific party
    investments = frappe.get_list(
        'Investment App',
        fields=['name', 'party_name', 'party', 'posting_date', 'transaction_type', 'amount'],
        filters={
            'party': specific_party,
            'transaction_type': ['in', ['Re-invest', 'Invest']]
        },
        limit_page_length=50
    )

    total_interest = 0  # Initialize total interest variable
    total_available = 0  # Initialize total available amount variable
    total_principal = 0

    # Fetch investment schedule for each investment
    for investment in investments:
        investment['investment_schedule'] = frappe.get_all(
            'Investment Schedule',
            fields=['start_date', 'end_date', 'principal_amount', 'amount', 'available_amount'],
            filters={'parent': investment['name']}
        )
        
        # Sort investment_schedule by principal_amount in descending order
        investment['investment_schedule'].sort(key=lambda x: x['principal_amount'], reverse=True)

        # Calculate totals from the investment schedule 
        for schedule in investment['investment_schedule']:
            total_interest += schedule['amount']  # Assuming 'amount' is the interest amount
            total_available += schedule['available_amount']
            total_principal += schedule['principal_amount']

    context.report_data = investments
    context.total_interest = total_interest  # Add total interest to context
    context.total_available = total_available  # Add total available amount to context
    context.total_principal = total_principal

    # Debug: print the fetched report data
    print("Fetched Report Data:", context.report_data)
    print("Total Interest:", total_interest)
    print("Total Available Amount:", total_available)

    context.title = "Investment Schedule Report"
