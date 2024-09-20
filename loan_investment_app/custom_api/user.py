from frappe import _
import frappe
from frappe.utils import today
from datetime import datetime

@frappe.whitelist()
def get_logged_in_user_info():
    # Get the current logged-in user and current date
    user = frappe.get_doc("User", frappe.session.user)
    current_date = frappe.utils.today()

    # Basic user info
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

    # Initialize variables for member and account details
    member_name = None
    custom_investor_account_number = None
    custom_investor_account_name = None
    custom_investor_bank_name = None
    balance_portfolia = 0
    balance_withdrawal_payable = 0
    balance_deposit = 0
    balance_interest = 0
    email_id = None
    pan_number = None
    membership_type = None
    custom_member_id = None
    amount_in_wallet = 0  # Initialize amount_in_wallet to ensure it has a default value

    # If an investment account exists, fetch member details
    if investment_account:
        member_data = frappe.db.sql("""
            SELECT name, member_name, email_id, custom_resident, membership_type, 
                   custom_investor_account_name, custom_investor_account_number, custom_investor_bank_name
            FROM `tabMember`
            WHERE name = %s
        """, (investment_account[0].for_value,), as_dict=True)

        if member_data:
            # Assign member details
            member_name = member_data[0].member_name
            custom_investor_account_number = member_data[0].custom_investor_account_number
            custom_investor_account_name = member_data[0].custom_investor_account_name
            custom_investor_bank_name = member_data[0].custom_investor_bank_name
            email_id = member_data[0].email_id
            pan_number = member_data[0].custom_resident
            membership_type = member_data[0].membership_type
            custom_member_id = member_data[0].name
            

        # Fetch the portfolio and withdrawal payable account settings
        accounts = frappe.db.sql("""
            SELECT portfolio_account, investment_interest, capital_account, investor_withdrawal_payable_account
            FROM `tabInvestment Settings`
        """, as_dict=True)

        if accounts:
            portfolia = accounts[0].portfolio_account
            withdrawal_payable = accounts[0].investor_withdrawal_payable_account
            deposit = accounts[0].capital_account
            interest = accounts[0].investment_interest

            # Fetch total credits and debits for the member in both the portfolio and withdrawal accounts
            balance_data = frappe.db.sql("""
                SELECT 
                    SUM(CASE WHEN account = %s THEN credit ELSE 0 END) AS total_credit_portfolia,
                    SUM(CASE WHEN account = %s THEN debit ELSE 0 END) AS total_debit_portfolia,
                    SUM(CASE WHEN account = %s THEN credit ELSE 0 END) AS total_credit_withdrawal,
                    SUM(CASE WHEN account = %s THEN debit ELSE 0 END) AS total_debit_withdrawal,
                    SUM(CASE WHEN account = %s THEN credit ELSE 0 END) AS total_credit_deposit,
                    SUM(CASE WHEN account = %s THEN debit ELSE 0 END) AS total_debit_deposit,
                    SUM(CASE WHEN account = %s THEN credit ELSE 0 END) AS total_credit_interest,
                    SUM(CASE WHEN account = %s THEN debit ELSE 0 END) AS total_debit_interest
                FROM `tabGL Entry`
                WHERE party_type = 'Member' AND party = %s
            """, (portfolia, portfolia, withdrawal_payable, withdrawal_payable, deposit, deposit, interest, interest, investment_account[0].for_value), as_dict=True)

            if balance_data:
                total_credit_portfolia = balance_data[0].total_credit_portfolia or 0
                total_debit_portfolia = balance_data[0].total_debit_portfolia or 0
                total_credit_withdrawal = balance_data[0].total_credit_withdrawal or 0
                total_debit_withdrawal = balance_data[0].total_debit_withdrawal or 0
                total_credit_deposit = balance_data[0].total_credit_deposit or 0
                total_debit_deposit = balance_data[0].total_debit_deposit or 0
                total_credit_interest = balance_data[0].total_credit_interest or 0
                total_debit_interest = balance_data[0].total_debit_interest or 0

                # Calculate balances
                balance_portfolia = total_credit_portfolia - total_debit_portfolia
                balance_withdrawal_payable = total_credit_withdrawal - total_debit_withdrawal
                balance_deposit = total_credit_deposit - total_debit_deposit
                balance_interest = total_credit_interest - total_debit_interest
                amount_in_wallet = balance_interest + balance_portfolia  # Now amount_in_wallet is always initialized

    # Prepare the response with all user and account information
    user_info2 = {
        "member": investment_account[0].for_value if investment_account else None,
        "current_date": current_date,
        "member_name": member_name,
        "custom_investor_account_number": custom_investor_account_number,
        "custom_investor_account_name": custom_investor_account_name,
        "custom_investor_bank_name": custom_investor_bank_name,
        "email_id": email_id,
        "custom_member_id": custom_member_id,
        "custom_resident": pan_number,
        "membership_type": membership_type,
        "balance_portfolia": balance_portfolia,
        "balance_withdrawal_payable": balance_withdrawal_payable,
        "balance_deposit": balance_deposit,
        "balance_interest": balance_interest,
        "balance_amount_in_wallet": amount_in_wallet,
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
                AND inv_app.investment_status = 'Approved'  -- Filter for parent status
                AND inv_app.transaction_type IN ('Re-invest', 'Invest')  -- Filter for transaction type
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
