# Copyright (c) 2024, Paul and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
from frappe.utils import today
from frappe.utils import today, getdate




class InvestmentApp(Document):
    def validate(self):
        # Validate that the amount does not exceed the balance_wallet for "Request Payment" transactions
        if self.transaction_type == "Request Payment" or self.transaction_type == "Withdraw":
            if self.amount > self.balance_wallet:
                frappe.throw(_("The amount cannot exceed the balance wallet amount."))

        # if self.transaction_type == "Withdraw" and self.investment_schedule:
        #     # Fetch all InvestmentApp documents with matching conditions
        #     investment_docs = frappe.get_all(
        #         "Investment App",
        #         filters={"investment_schedule": self.investment_schedule},
        #         fields=["name", "start_date", "end_date", "balance_wallet"]
        #     )

        #     # Iterate through the fetched documents
        #     for investment in investment_docs:
        #         start_date = investment.get("start_date")
        #         end_date = investment.get("end_date")
        #         current_date = getdate(today())  # Get the current date as a date object

        #         # Ensure both start_date and end_date are valid before comparison
        #         if start_date and end_date:
        #             start_date = getdate(start_date)
        #             end_date = getdate(end_date)

        #             # Check if the schedule is within the valid range
        #             if not (start_date <= current_date <= end_date):
        #                 frappe.throw(_("Transaction cannot be made. The investment with name {0} has an expired schedule (end date: {1}).").format(investment["name"], end_date))

        #         # Validate that the withdraw amount does not exceed the balance_wallet
        #         if self.amount > investment.get("balance_wallet", 0):
        #             frappe.throw(_("The withdrawal amount exceeds the available balance in wallet for investment: {0}.").format(investment["name"]))
        #     else:
        #         frappe.throw(_("Invalid investment schedule format."))

       
    def on_submit(self):
        self.create_journal_entry()
        self.create_schedule_journal_entries()

    @frappe.whitelist()
    def create_journal_entry(self):
        try:
            company, default_paid_to_account = self.get_default_company_and_account()

            # Fetch investment accounts based on transaction type
            accounts = self.get_investment_accounts()

            # Create Journal Entry
            journal_entry = frappe.new_doc('Journal Entry')
            journal_entry.voucher_type = 'Journal Entry'
            journal_entry.company = accounts['company_set']
            journal_entry.posting_date = self.posting_date
            journal_entry.user_remark = self.remarks
            journal_entry.custom_transaction_type = self.transaction_type
            journal_entry.custom_investmet_id = self.name

            if self.transaction_type == "Deposit":
                self.add_journal_entry_row(journal_entry, accounts['capital_account'], 0, self.amount, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, default_paid_to_account, self.amount, 0, cost_center=accounts['cost_center'])

            elif self.transaction_type == "Invest":
                self.add_journal_entry_row(journal_entry, accounts['capital_account'], self.amount, 0, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, accounts['portfolio_account'], 0, self.amount, cost_center=accounts['cost_center'])

            elif self.transaction_type == "Transfer":
                self.add_journal_entry_row(journal_entry, accounts['capital_account'], self.amount, 0, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, accounts['portfolio_account'], 0, self.amount, cost_center=accounts['cost_center'])

            elif self.transaction_type == "Withdraw":
                self.add_journal_entry_row(journal_entry, accounts['withdrawal_payable_account'], 0, self.withdraw_grand_totals, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, accounts['portfolio_account'], self.amount, 0, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, accounts['investment_interest'], self.withdraw_percen_amount, 0, cost_center=accounts['cost_center'])
                # self.add_journal_entry_row(journal_entry, default_paid_to_account, 0, self.amount, cost_center=accounts['cost_center'])

            elif self.transaction_type == "Re-invest":
                self.add_journal_entry_row(journal_entry, accounts['withdrawal_payable_account'], self.amount, 0, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, accounts['portfolio_account'], 0, self.amount, cost_center=accounts['cost_center'])

            elif self.transaction_type == "Request Payment":
                self.add_journal_entry_row(journal_entry, accounts['withdrawal_payable_account'], self.withdral_amount, 0, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, self.pay_to, 0, self.withdral_amount, cost_center=accounts['cost_center'])

            else:
                frappe.throw(_("Invalid transaction type: {0}").format(self.transaction_type))

            journal_entry.insert()
            journal_entry.submit()  # Submit the Journal Entry
            frappe.msgprint(_("Journal Entry created successfully: {0}").format(journal_entry.name))
            return {"message": _("Journal Entry created successfully!"), "name": journal_entry.name}

        except Exception as e:
            frappe.log_error(message=str(e), title=_("Failed to create Journal Entry"))
            frappe.throw(_("Failed to create Journal Entry: {0}").format(str(e)))

    @frappe.whitelist()
    def create_schedule_journal_entries(self):
        try:
            company, default_paid_to_account = self.get_default_company_and_account()

            if self.transaction_type == "Invest" or self.transaction_type == "Re-invest":
                accounts = self.get_investment_accounts()

                for schedule_item in self.investment_schedule:
                    journal_entry = frappe.new_doc('Journal Entry')
                    journal_entry.voucher_type = 'Journal Entry'
                    journal_entry.company = accounts['company_set']
                    journal_entry.posting_date = schedule_item.start_date
                    journal_entry.user_remark = self.remarks
                    journal_entry.custom_transaction_type = self.transaction_type
                    journal_entry.custom_investmet_id = self.name

                    self.add_journal_entry_row(journal_entry, accounts['investment_interest'], 0, schedule_item.amount, cost_center=accounts['cost_center'])
                    self.add_journal_entry_row(journal_entry, accounts['percent_interest_account'], schedule_item.amount, 0, cost_center=accounts['cost_center'])

                    journal_entry.insert()
                    journal_entry.submit()
                    frappe.msgprint(_("Journal Entry for schedule created successfully: {0}").format(journal_entry.name))
            
            # if self.transaction_type == "Re-invest":
            #     accounts = self.get_investment_accounts()

            #     for schedule_item in self.investment_schedule:
            #         journal_entry = frappe.new_doc('Journal Entry')
            #         journal_entry.voucher_type = 'Journal Entry'
            #         journal_entry.company = accounts['company_set']
            #         journal_entry.posting_date = schedule_item.date
            #         journal_entry.user_remark = self.remarks
            #         journal_entry.custom_transaction_type = self.transaction_type
            #         journal_entry.custom_investmet_id = self.name

            #         self.add_journal_entry_row(journal_entry, accounts['withdrawal_payable_account'], self.withdral_amount, 0, cost_center=accounts['cost_center'])
            #         self.add_journal_entry_row(journal_entry, accounts['portfolio_account'], 0, self.withdral_amount, cost_center=accounts['cost_center'])

            #         journal_entry.insert()
            #         journal_entry.submit()
            #         frappe.msgprint(_("Journal Entry for schedule created successfully: {0}").format(journal_entry.name))

        except Exception as e:
            frappe.log_error(message=str(e), title=_("Failed to create Journal Entry for Schedule"))
            frappe.throw(_("Failed to create Journal Entry for Schedule: {0}").format(str(e)))

    def get_default_company_and_account(self):
        company = frappe.defaults.get_user_default('company') or frappe.db.get_single_value('Global Defaults', 'default_company')

        default_paid_to_account = frappe.db.get_value(
            "Mode of Payment Account", 
            {"parent": self.mode_of_payment, "company": company}, 
            "default_account"
        )
        if not default_paid_to_account:
            frappe.throw(_("Default account for the mode of payment not found. Please check the configuration."))

        return company, default_paid_to_account

    def get_investment_accounts(self):
        investment_account = frappe.db.sql("""
            SELECT capital_account, investment_interest, percent_interest_amount_account,
            portfolio_account, company, cost_center,investor_withdrawal_payable_account
            FROM `tabInvestment Settings`
            LIMIT 1
        """, as_dict=True)
        
        if not investment_account:
            frappe.throw(_("Investment account details not found in Investment Settings."))

        return {
            'capital_account': investment_account[0]['capital_account'],
            'company_set': investment_account[0]['company'],
            'cost_center': investment_account[0]['cost_center'],
            'portfolio_account': investment_account[0]['portfolio_account'],
            'investment_interest': investment_account[0]['investment_interest'],
            'withdrawal_payable_account': investment_account[0]['investor_withdrawal_payable_account'],
            'percent_interest_account': investment_account[0]['percent_interest_amount_account']
        }

    def add_journal_entry_row(self, journal_entry, account, debit, credit, cost_center=None):
        journal_entry.append('accounts', {
            'account': account,
            'debit_in_account_currency': debit,
            'credit_in_account_currency': credit,
            'party_type': "Member",
            'party': self.party,
            'cost_center': cost_center,
            'user_remark': self.remarks
        })
