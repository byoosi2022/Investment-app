from frappe import _
import frappe
from frappe.utils import today
from datetime import datetime

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

    # Initialize variables
    member_name = None
    custom_investor_account_number = None
    custom_investor_account_name = None
    custom_investor_bank_name = None
    total_credit = 0
    total_debit = 0
    balance = 0  # Initialize balance

    # Fetch member details if an investment account was found
    if investment_account:
        member_data = frappe.db.sql("""
            SELECT  name,member_name, email_id,custom_resident,membership_type,custom_investor_account_name, custom_investor_account_number, custom_investor_bank_name
            FROM `tabMember`
            WHERE name = %s
        """, (investment_account[0].for_value,), as_dict=True)

        # Check if member data is found and set member details 
        if member_data:
            member_name = member_data[0].member_name
            custom_investor_account_number = member_data[0].custom_investor_account_number
            custom_investor_account_name = member_data[0].custom_investor_account_name
            custom_investor_bank_name = member_data[0].custom_investor_bank_name
            email_id = member_data[0].email_id
            pan_number = member_data[0].custom_resident
            membership_type = member_data[0].membership_type
            custom_member_id = member_data[0].name

        # Fetch total credits and debits for the member in the account
        balance_data = frappe.db.sql("""
            SELECT SUM(credit) AS total_credit, SUM(debit) AS total_debit
            FROM `tabGL Entry`
            WHERE account = '22514 - Investors Withdrawal Payable Account - MACL'
            AND party_type = 'Member'
            AND party = %s
        """, (investment_account[0].for_value,), as_dict=True)

        # Set totals if data is found
        if balance_data:
            total_credit = balance_data[0].total_credit or 0
            total_debit = balance_data[0].total_debit or 0

            # Calculate balance
            balance = total_credit - total_debit

    # Prepare user information with the total credits, debits, and balance
    user_info2 = {
        "member": investment_account[0].for_value if investment_account else None,
        "current_date": current_date,
        "member_name": member_name,
        "custom_investor_account_number": custom_investor_account_number,
        "custom_investor_account_name": custom_investor_account_name,
        "custom_investor_bank_name": custom_investor_bank_name,
        "email_id": email_id,
        "custom_member_id":custom_member_id,
        "custom_resident": pan_number,
        "membership_type":membership_type,
        "total_credit": total_credit,  # Total credits
        "total_debit": total_debit,     # Total debits
        "balance": balance                # Balance (total_credit - total_debit)
    }

    return user_info2


@frappe.whitelist()
def get_party_name(party):
    # Initialize member_name to avoid reference before assignment errors
    member_name = ""

    # Fetch member name if a party (investment account) is provided
    if party:
        member_data = frappe.db.sql("""
            SELECT member_name
            FROM `tabMember`
            WHERE name = %s
        """, (party,), as_dict=True)

        # Check if member_data is found and set member_name
        if member_data and member_data[0].get('member_name'):
            member_name = member_data[0]['member_name']

    # Return the party name (member_name)
    return {
        "member_name": member_name
    }
    
from dateutil.relativedelta import relativedelta

from datetime import datetime
import frappe

from datetime import datetime
import frappe

@frappe.whitelist()
def fetch_investment_schedule(start_date=None, end_date=None):
    user = frappe.get_doc("User", frappe.session.user)
    user_info = {
        "email": user.email,
    }

    # Fetch user permissions related to the investment account where 'allow' is 'Member'
    investment_account = frappe.db.sql("""
        SELECT for_value
        FROM `tabUser Permission`
        WHERE user = %s AND allow = 'Member'
    """, (user_info["email"],), as_dict=True)

    # Initialize variables
    member_name = None
    total_percent_amount = 0  # To sum percent_amount

    # Fetch member details if an investment account was found
    if investment_account:
        member_data = frappe.db.sql("""
            SELECT member_name, name
            FROM `tabMember`
            WHERE name = %s
        """, (investment_account[0].for_value,), as_dict=True)

        # If member data was found, set member_name
        if member_data:
            member_name = member_data[0].name

            # Fetch only submitted investment schedules for the member based on the parent investment app
            investment_schedule_data = frappe.db.sql("""
                SELECT inv_schedule.*
                FROM `tabInvestment Schedule` inv_schedule
                JOIN `tabInvestment App` inv_app ON inv_schedule.parent = inv_app.name
                WHERE inv_app.party = %s
                AND inv_app.docstatus = 1
                AND inv_app.investment_status = 'Investment Approved'  -- Corrected filter for parent status
                ORDER BY inv_schedule.start_date ASC  -- Using 'start_date' field in child table
            """, (member_name,), as_dict=True)

            # Check if start_date and end_date are provided, and parse them to date objects
            if start_date and end_date:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()  # Convert to date object
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()  # Convert to date object

                # Loop through the investment schedule data and sum up the percent_amount for valid entries
                for schedule in investment_schedule_data:
                    schedule_start_date = schedule['start_date']  # Start date from child table
                    schedule_end_date = schedule['end_date']      # End date from child table

                    # Ensure schedule dates are date objects
                    if isinstance(schedule_start_date, datetime):
                        schedule_start_date = schedule_start_date.date()
                    if isinstance(schedule_end_date, datetime):
                        schedule_end_date = schedule_end_date.date()

                    # Check if the provided date range intersects with the schedule's date range
                    if (start_date <= schedule_end_date) and (end_date >= schedule_start_date):
                        # Sum the percent_amount
                        total_percent_amount += schedule.get('amount', 0)

            return {
                "member_name": member_name,
                "investment_schedule_data": investment_schedule_data,
                "total_percent_amount": total_percent_amount  # Return the calculated percent_amount
            }

    return None
