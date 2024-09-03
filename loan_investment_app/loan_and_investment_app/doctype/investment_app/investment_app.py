# Copyright (c) 2024, Paul and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class InvestmentApp(Document):
    def on_submit(self):
        self.create_journal()

    @frappe.whitelist()
    def create_journal(self):
        try:
            # Get the default company
            company = frappe.defaults.get_user_default('company') or frappe.db.get_single_value('Global Defaults', 'default_company')
            
            # Fetch the default account from the Mode of Payment Account child table
            default_paid_to_account = frappe.db.get_value(
                "Mode of Payment Account", 
                {"parent": self.mode_of_payment, "company": company}, 
                "default_account"
            )
            if not default_paid_to_account:
                frappe.throw(_("Default account for the mode of payment not found. Please check the configuration."))

            # Initialize the investment accounts for deposits
            capital_account = None
            company_set = None
            cost_center = None
            portfolio_account = None

            if self.transaction_type == "Deposit" or self.transaction_type in ["Invest", "Transfer", "Withdraw"]:
                # Fetch the investment account details directly from the database
                investment_account = frappe.db.sql("""
                    SELECT capital_account, investment_interest, portfolio_account,company,cost_center
                    FROM `tabInvestment Settings`
                    LIMIT 1
                """, as_dict=True)
                # frappe.msgprint(_(str(investment_account)))
                
                if not investment_account:
                    frappe.throw(_("Investment account details not found in Investment Settings."))

                capital_account = investment_account[0]['capital_account']
                company_set = investment_account[0]['company']
                cost_center = investment_account[0]['cost_center']
                portfolio_account = investment_account[0]['portfolio_account']
                # frappe.msgprint(_(str(investment_account)))

                # Create a new Journal Entry document 
                journal_entry = frappe.new_doc('Journal Entry')
                journal_entry.voucher_type = 'Journal Entry'
                journal_entry.company = company_set
                journal_entry.posting_date = self.posting_date
                journal_entry.user_remark = self.remarks
                journal_entry.custom_transaction_type = self.transaction_type
                journal_entry.custom_investmet_id = self.name

                if self.transaction_type == "Deposit":
                    # Credit capital_account, Debit mode of payment account cost_center
                    journal_entry.append('accounts', {
                        'account': capital_account,
                        'debit_in_account_currency': 0,
                        'credit_in_account_currency': self.amount,
                        'party_type': "Member",
                        'party': self.party,
                        'cost_center': cost_center,
                        'user_remark': self.remarks
                    })
                    journal_entry.append('accounts', {
                        'account': default_paid_to_account,
                        'debit_in_account_currency': self.amount,
                        'credit_in_account_currency': 0,
                        'cost_center': cost_center,
                        'user_remark': self.remarks
                    })

                elif self.transaction_type == "Invest":
                    # Debit investment_interest, Credit portfolio_account
                    journal_entry.append('accounts', {
                        'account': capital_account,
                        'debit_in_account_currency': self.amount,
                        'credit_in_account_currency': 0,
                        'party_type': "Member",
                        'party': self.party,
                        'cost_center': cost_center,
                        'user_remark': self.remarks
                    })
                    journal_entry.append('accounts', {
                        'account': portfolio_account,
                        'debit_in_account_currency': 0,
                        'credit_in_account_currency': self.amount,
                        'party_type': "Member",
                        'party': self.party,
                        'cost_center': cost_center,
                        'user_remark': self.remarks
                    })

                elif self.transaction_type == "Transfer":
                    # Debit capital_account, Credit portfolio_account
                    journal_entry.append('accounts', {
                        'account': capital_account,
                        'debit_in_account_currency': self.amount,
                        'credit_in_account_currency': 0,
                        'party_type': "Member",
                        'party': self.party,
                        'cost_center': cost_center,
                        'user_remark': self.remarks
                    })
                    journal_entry.append('accounts', {
                        'account': portfolio_account,
                        'debit_in_account_currency': 0,
                        'credit_in_account_currency': self.amount,
                        'party_type': "Member",
                        'party': self.party,
                        'cost_center': cost_center,
                        'user_remark': self.remarks
                    })

                elif self.transaction_type == "Withdraw":
                    # Debit capital_account, Credit mode of payment account
                    journal_entry.append('accounts', {
                        'account': capital_account,
                        'debit_in_account_currency': self.amount,
                        'credit_in_account_currency': 0,
                        'party_type': "Member",
                        'party': self.party,
                        'cost_center': cost_center,
                        'user_remark': self.remarks
                    })
                    journal_entry.append('accounts', {
                        'account': default_paid_to_account,
                        'debit_in_account_currency': 0,
                        'credit_in_account_currency': self.amount,
                        'cost_center': cost_center,
                        'user_remark': self.remarks
                    })
                
                journal_entry.insert()
                journal_entry.submit()  # Uncomment this line to submit the journal entry
                frappe.msgprint(_("Journal Entry created successfully: {0}").format(journal_entry.name))
                return {"message": _("Journal Entry created successfully!"), "name": journal_entry.name}
            else:
                frappe.throw(_("Invalid transaction type: {0}").format(self.transaction_type))
        
        except Exception as e:
            frappe.log_error(message=str(e), title=_("Failed to create Journal Entry"))
            frappe.throw(_("Failed to create Journal Entry: {0}").format(str(e)))
