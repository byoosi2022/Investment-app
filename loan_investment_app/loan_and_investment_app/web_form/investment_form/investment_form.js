frappe.ready(function() {
	// bind events here
	  setTimeout(function () {
        // Fetch the user information
        frappe.call({
            method: 'loan_investment_app.custom_api.user.get_logged_in_user_info',
            callback: function (response) {
                console.log(response);
                if (response.message) {
                    // Set the fetched user information to the appropriate fields  
                    frappe.web_form.set_value('custom_member_id', response.message.custom_member_id);
					frappe.web_form.set_value('custom_resident', response.message.custom_resident);
                    frappe.web_form.set_value('email_id', response.message.email_id);
                    frappe.web_form.set_value('member_name', response.message.member_name);
                    frappe.web_form.set_value('custom_investor_bank_name', response.message.custom_investor_bank_name);
                    frappe.web_form.set_value('custom_investor_account_number', response.message.custom_investor_account_number);
                    frappe.web_form.set_value('custom_investor_account_name', response.message.custom_investor_account_name);
                    frappe.web_form.set_value('membership_type', response.message.membership_type);
                }
            }
        });

    }, 1000); // Adjust the timeout value as needed

})