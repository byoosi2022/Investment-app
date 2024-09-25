import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt

class InvestmentApp(Document):

    def validate(self):
      
        # Ensure transaction type is set
        if not self.transaction_type:
            frappe.throw(_("Please select the transaction type of your choice."))

        # Validate transaction amounts based on the transaction type
        if self.transaction_type == "Invest":
            if self.amount > self.portifolia_account:
                frappe.throw(_("The investment amount cannot exceed the available amount in the Deposit Account."))

        elif self.transaction_type == "Re-invest":
            if self.amount > self.balance_walet:
                frappe.throw(_("The re-investment amount cannot exceed the available amount in the Amount in Wallet Account."))

        # Set default investment status
        if not self.investment_status:
            self.investment_status = "Received"

        # Ensure that the amount is not negative or None
        if self.amount is None:
            frappe.throw(_("The transaction amount cannot be empty."))

        if self.amount <= 0:
            frappe.throw(_("The transaction amount should be a positive value."))

        # Validate specific transaction types
        if self.transaction_type == "Request for Payments":
            self.validate_payment_request()

        elif self.transaction_type == "Withdraw":
            self.validate_withdrawal()
         
    
    def validate_payment_request(self):
        """Validate payment request amount against the wallet balance."""
        if self.amount > self.balance_walet:  # Ensure 'balance_wallet' is used correctly
            frappe.throw(_("The requested payment amount cannot exceed the balance in the wallet."))

    def validate_withdrawal(self):
        """Validate withdrawal amount and investment end dates."""
        # Check if the withdrawal amount exceeds the available wallet amount total_amount_after_tax
        if self.amount > self.total_amount_invested:
            frappe.throw(_("The withdrawal amount cannot exceed the available amount invested + interests."))
            
        # Check if the withdrawal's posting date is beyond the current date
        current_date = getdate(frappe.utils.today())
        if getdate(self.posting_date) > current_date:
            frappe.throw(_("You cannot withdraw funds beyond today's date ({0}).").format(current_date))
        # Get the logged-in user
        user = frappe.session.user

         # Skip validation for users without the "Investor" role and administrators
        if not "Investor" in frappe.get_roles(user) or "Administrator" in frappe.get_roles(user):
            frappe.logger().debug(f"User {user} is either not an Investor or is an Administrator, skipping investment validation")
            return  # Exit validation for users without the "Investor" role or administrators

        # Log that the user has the "Investor" role
        frappe.logger().debug(f"User {user} has Investor role")

        # Fetch the investments for the current party associated with the investor
        investments = self.fetch_investments_for_party()

        # If no investments are found, block the save
        if not investments:
            frappe.throw(
                _("No investments found for the current investor. Please create an investment before saving.")
            )

        # Extract the month and year from the current document's posting_date
        posting_date = getdate(self.posting_date)
        posting_year = posting_date.year
        posting_month = posting_date.month

        # Flag to allow saving if a valid investment is found
        allow_save = False

        # Iterate through the investments and compare month and year
        for investment in investments:
            investment_end_date = getdate(investment["end_date"])
            investment_year = investment_end_date.year
            investment_month = investment_end_date.month

            # Check if the month and year match
            if investment_year == posting_year and investment_month == posting_month:
                # Allow save if the posting_date is equal to or greater than the investment's end_date
                if posting_date >= investment_end_date:
                    allow_save = True
                    break  # Exit the loop if a valid date is found
                else:
                    frappe.throw(
                        _("The posting date {0} must be greater than or equal to the end date {1} of investment {2} in the same month and year. Please select a valid posting date.")
                        .format(self.posting_date, investment["end_date"], investment["name"])
                    )

        # If no valid investment was found, block the save
        if not allow_save:
            frappe.throw(
                _("The posting date {0} does not meet the condition of any investment's end date within the same month and year.")
                .format(self.posting_date)
            )

    def fetch_investments_for_party(self):
        # Get the logged-in user
        user = frappe.session.user

        # Get the member name associated with the user
        # party = frappe.db.get_value("Member", {"owner": user}, "name")
        party = frappe.db.get_value("Member", {"email_id": user}, "name")

        
        # If no party is found, return an empty list or handle accordingly
        if not party:
            return []

        # Fetch investments related to the specific party
        return frappe.get_list(
            'Investment App',
            fields=['name', 'end_date', 'posting_date', 'amount', 'party_name'],
            filters={
                'party': party,  # Filter by the specific party
                'transaction_type': ['in', ['Re-invest', 'Invest']],
                'docstatus': ['!=', 2],  # Exclude canceled records
                'investment_status': 'Approved'
            }
        )


    def on_submit(self):
        """Validate withdrawal amount and investment end dates."""
        # Check if the withdrawal amount exceeds the available wallet amount total_amount_after_tax
        if self.transaction_type == "Withdraw":
          
            if self.amount > self.total_amount_after_tax:
                frappe.throw(_("The withdrawal amount cannot exceed the available Total amount after tax."))
            
            # Call the method to update withdrawal amounts for specific investments
            self.update_withdrawal_amounts_for_specific_investments()
        # Create journal entry and schedule journal entries
        self.create_journal_entry()
        self.create_schedule_journal_entries()
    
        # Update investment status
        self.investment_status = "Approved"
    
        # Save the document after updating the status
        self.save()

    def update_withdrawal_amounts_for_specific_investments(self):
        # Fetch Investment App documents with filters
        investments = frappe.get_all(
            "Investment App",
            filters={
                "party": self.party,  # Match party with the current instance's party
                "end_date": self.posting_date,  # Match end_date with posting_date from the current instance
                "transaction_type": ["in", ["Re-invest", "Invest"]]  # Match transaction type
            },
            fields=["name", "posting_date", "end_date", "withdral_amount", "amount", "party", "transaction_type"]
        )

        for investment in investments:
            investment_doc = frappe.get_doc("Investment App", investment.name)
            
            total_amount = flt(self.amount_withrowned) + flt(self.interets_withrowned)

            # Calculate the new withdrawal_amount
            new_withdrawal_amount = flt(investment_doc.withdral_amount) - total_amount  # Ensure calculations are float

            # Ensure withdrawal_amount does not go below zero
            if new_withdrawal_amount < 0:
                frappe.throw(_("Withdrawal amount cannot be negative for {0}. Current amount: {1}, Deduction: {2}").format(
                    investment_doc.name, investment_doc.withdral_amount, investment_doc.amount))

            # Update the withdrawal_amount
            investment_doc.withdral_amount = new_withdrawal_amount

            # Set or retain the party field
            if not investment_doc.party:  # If party is not set, assign a default value
                investment_doc.party = self.party  # Retain the current party

            # Save the updated document
            investment_doc.save(ignore_permissions=True)

            # Show a message to the user
            frappe.msgprint(_("Withdrawal amount updated to {0} for {1}. Party set to {2}.").format(
                new_withdrawal_amount, investment_doc.name, investment_doc.party))         
 
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
                self.add_journal_entry_row(journal_entry, accounts['withdrawal_payable_account'], 0, self.total_amount_after_tax, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, accounts['witholding_tax_payable'], 0, self.withhold_tax, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, accounts['portfolio_account'], self.amount_withrowned, 0, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, accounts['investment_interest'], self.total_interest_amount, 0, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, accounts['investment_interest'], self.withhold_tax, 0, cost_center=accounts['cost_center'])
              
            elif self.transaction_type == "Re-invest":
                self.add_journal_entry_row(journal_entry, accounts['withdrawal_payable_account'], self.amount, 0, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, accounts['portfolio_account'], 0, self.amount, cost_center=accounts['cost_center'])

            elif self.transaction_type == "Request for Payments":
                self.add_journal_entry_row(journal_entry, accounts['withdrawal_payable_account'], self.amount, 0, cost_center=accounts['cost_center'])
                self.add_journal_entry_row(journal_entry, self.pay_to, 0, self.amount, cost_center=accounts['cost_center'])

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
            portfolio_account, company, witholding_tax_payable,cost_center,investor_withdrawal_payable_account
            FROM `tabInvestment Settings`
            LIMIT 1
        """, as_dict=True)
        
        if not investment_account:
            frappe.throw(_("Investment account details not found in Investment Settings."))

        return {
            'capital_account': investment_account[0]['capital_account'],
            'company_set': investment_account[0]['company'],
            'witholding_tax_payable': investment_account[0]['witholding_tax_payable'],
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
