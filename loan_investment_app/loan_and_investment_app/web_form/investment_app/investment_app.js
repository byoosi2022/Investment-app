frappe.ready(function() {
	// bind events here
	setTimeout(function () {
        // frappe.msgprint('Loaded Successfully');
        // console.log('Form loaded successfully');
        // Fetch the user information
        frappe.call({
            method: 'loan_investment_app.custom_api.user.get_logged_in_user_info',
            callback: function (response) {
                console.log(response)
                if (response.message) {
                    // Set the fetched user information to the appropriate fields
                    frappe.web_form.set_value('posting_date', response.message.current_date);
                    frappe.web_form.set_value('party_type', "Member");
                    frappe.web_form.set_value('party_id', response.message.member);
                    frappe.web_form.set_value('party_name', response.message.member_name);
                }
            }
        });
        // init script here
    }, 1000); // Adjust the timeout value as needed

})