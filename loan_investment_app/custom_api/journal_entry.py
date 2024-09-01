import frappe
from frappe import _

@frappe.whitelist()
def create_journal_entry(posting_date, amount, party_type, party, mode_of_payment, trans_type, remarks, company=None):
    try:
        # Get the default company if none is provided
        if not company:
            company = frappe.defaults.get_user_default('company') or frappe.db.get_single_value('Global Defaults', 'default_company')
        
        # Fetch the default account from the Mode of Payment Account child table
        default_paid_to_account = frappe.db.get_value("Mode of Payment Account", 
                                                      {"parent": mode_of_payment, "company": company}, 
                                                      "default_account")
        if trans_type == "Deposit":
            invest_set = frappe.get_doc('Investment Settings')
            account_depo = invest_set.investment_account
            
        journal_entry = frappe.new_doc('Journal Entry')
        journal_entry.voucher_type = 'Journal Entry'
        journal_entry.posting_date = posting_date
        journal_entry.user_remark = remarks
        
        journal_entry.append('accounts', {       
            'account': account_depo,
            'debit_in_account_currency': 0,
            'credit_in_account_currency': amount,
            'party_type': party_type,
            'party': party,
            'user_remark': remarks
        })
        
        journal_entry.append('accounts', {
            'account': default_paid_to_account,
            'debit_in_account_currency': amount,
            'credit_in_account_currency': 0,
            'party_type': party_type,
            'party': party,
            'user_remark': remarks
        })

        # Insert the document into the database
        journal_entry.insert()
        # Submit the document if needed
        # journal_entry.submit()
        
        # Return success message
        return {"message": _("Investment created successfully!"), "name": journal_entry.name}
    except Exception as e:
        # Return structured error message instead of throwing an exception
        return {"error": _("Failed to create Journal Entry: {0}").format(str(e))}
