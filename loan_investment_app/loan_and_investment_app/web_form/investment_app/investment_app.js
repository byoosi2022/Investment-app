frappe.ready(function() {
    // Bind events here
    setTimeout(function () {
        // Fetch the user information
        frappe.call({
            method: 'loan_investment_app.custom_api.user.get_logged_in_user_info',
            callback: function (response) {
                console.log(response);
                if (response.message) {
                    // Set the fetched user information to the appropriate fields
                    frappe.web_form.set_value('posting_date', response.message.current_date);
                    frappe.web_form.set_value('party_type', "Member");
                    frappe.web_form.set_value('party_id', response.message.member);
                    frappe.web_form.set_value('party_name', response.message.member_name);
                }
            }
        });

        // Event listener for transaction_type field
        frappe.web_form.on('transaction_type', function(field, value) {
            handle_transaction_type(value);
        });

        // Event listeners for interest_rate and amount fields
        frappe.web_form.on('interest_rate', function(field, value) {
            calculate_percent_amount();
        });
        frappe.web_form.on('amount', function(field, value) {
            calculate_percent_amount();
        });
        frappe.web_form.on('start_date', function(field, value) {
            calculate_percent_amount();
        });
        frappe.web_form.on('end_date', function(field, value) {
            calculate_percent_amount();
            populate_investment_schedule(); // Populate schedule when end_date is selected
        });

        // Initial handling of transaction_type visibility
        handle_transaction_type(frappe.web_form.get_value('transaction_type'));

        // Initial percent amount calculation
        calculate_percent_amount();
    }, 1000); // Adjust the timeout value as needed

    // Function to calculate percent_amount and set it in the form
    function calculate_percent_amount() {
        let interest_rate = parseFloat(frappe.web_form.get_value('interest_rate'));
        let amount = parseFloat(frappe.web_form.get_value('amount'));
        let start_date = frappe.web_form.get_value('start_date');
        let end_date = frappe.web_form.get_value('end_date');

        if (interest_rate && amount) {
            // Calculate the percentage amount
            let percent_amount = (interest_rate / 100) * amount;

            // Set the calculated value in the percent_amount field
            frappe.web_form.set_value('percent_amount', percent_amount);
        }
    }
    // Function to populate the investment schedule child table
function populate_investment_schedule() {
    let start_date = frappe.web_form.get_value('start_date');
    let end_date = frappe.web_form.get_value('end_date');
    let interest_rate = parseFloat(frappe.web_form.get_value('interest_rate'));
    let amount = parseFloat(frappe.web_form.get_value('amount'));

    if (start_date && end_date && interest_rate && amount) {
        start_date = frappe.datetime.str_to_obj(start_date);
        end_date = frappe.datetime.str_to_obj(end_date);

        // Calculate the difference in months
        let months_diff = (end_date.getFullYear() - start_date.getFullYear()) * 12 +
            (end_date.getMonth() - start_date.getMonth());

        // Clear existing rows in the investment_schedule child table
        let child_table = frappe.web_form.fields_dict['investment_schedule'];
        console.log(child_table)
        // Clear the child table's grid_rows
        child_table.grid.grid_rows = [];

        // Create an array to hold new rows
        let new_rows = [];

        // Populate new rows for each month in the difference
        for (let i = 0; i < months_diff; i++) {
            let scheduled_date = frappe.datetime.add_months(start_date, i);
            let monthly_amount = (interest_rate / 100) * amount / months_diff;

            // Create a new row object
            let new_row = {
                date: frappe.datetime.obj_to_str(scheduled_date),
                amount: monthly_amount,
                // Add any other fields you need here
            };

            new_rows.push(new_row);
        }

        // Set the child table's rows to the new rows
        new_rows.forEach(row => {
            child_table.add_row(row); // Add row to the grid
        });

        // Refresh the grid to display the newly added rows
        child_table.grid.refresh();
    }
}

// Function to clear the name field of each child row
function clearNameField(child) {
    if (child && child.grid && child.grid.grid_rows && child.grid.grid_rows.length > 0) {
        // Loop through all child rows
        child.grid.grid_rows.forEach(function (row) {
            // Set the name field of each child row to empty
            if (row.doc) {
                row.doc.name = ""; // Clear the name field
                // Optionally, you can clear other fields here
                // row.doc.field_name = ""; 
            }
        });
    }
}


    // Function to handle the visibility of fields based on transaction_type
    function handle_transaction_type(transaction_type) {
        const fields = ['interest_rate', 'start_date', 'end_date', 'percent_amount', 'mode_of_payment'];
        
        if (transaction_type === 'Invest' || transaction_type === 'Re-invest') {
            // Make fields visible for 'Invest' and 'Re-invest'
            frappe.web_form.set_df_property('interest_rate', 'hidden', 0);
            frappe.web_form.set_df_property('start_date', 'hidden', 0);
            frappe.web_form.set_df_property('end_date', 'hidden', 0);
            frappe.web_form.set_df_property('percent_amount', 'hidden', 0);
            frappe.web_form.set_df_property('mode_of_payment', 'hidden', 1);
        } else if (transaction_type === 'Deposit' || transaction_type === 'Withdraw') {
            // Make mode_of_payment visible for 'Deposit' and 'Withdraw'
            frappe.web_form.set_df_property('interest_rate', 'hidden', 0);
            frappe.web_form.set_df_property('start_date', 'hidden', 1);
            frappe.web_form.set_df_property('end_date', 'hidden', 1);
            frappe.web_form.set_df_property('percent_amount', 'hidden', 1);
            frappe.web_form.set_df_property('mode_of_payment', 'hidden', 1);
        } else if (transaction_type === 'Transfer') {
            // Hide all fields for 'Transfer'
            fields.forEach(field => {
                frappe.web_form.set_df_property(field, 'hidden', 1);
            });
        } else {
            // Default case: Hide all fields
            fields.forEach(field => {
                frappe.web_form.set_df_property(field, 'hidden', 1);
            });
        }
    }
});
