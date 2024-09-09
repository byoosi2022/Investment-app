frappe.ready(function() {
    // Bind events here
    setTimeout(function () {
        // Fetch the user information
        frappe.call({
            method: 'loan_investment_app.custom_api.user.get_logged_in_user_info',
            callback: function (response) {
                // console.log(response);
                if (response.message) {
                    // Set the fetched user information to the appropriate fields
                    frappe.web_form.set_value('posting_date', response.message.current_date);
                    frappe.web_form.set_value('party_type', "Member");
                    frappe.web_form.set_value('party_id', response.message.member);
                    frappe.web_form.set_value('party_name', response.message.member_name);
                    frappe.web_form.set_value('investor_bank_name', response.message.custom_investor_bank_name);
                    frappe.web_form.set_value('investor_account_number', response.message.custom_investor_account_number);
                    frappe.web_form.set_value('investor_account_name', response.message.custom_investor_account_name);
                    frappe.web_form.set_value('balance_walet', response.message.balance);
                }
            }
        });

        // Event listener for transaction_type field
        frappe.web_form.on('transaction_type', function(field, value) {
            handle_transaction_type(value);
            populate_schedule_table(value)
        });

        // Event listeners for interest_rate and amount fields interest_rate
        frappe.web_form.on('interest_rate', function(field, value) {
            calculate_percent_amount();
            frappe.web_form.set_df_property('end_date', 'hidden', 0);
        });
        frappe.web_form.on('amount', function(field, value) {
            calculate_percent_amount();
        });
        frappe.web_form.on('start_date', function(field, value) {
            calculate_percent_amount();
        });
    
        // Trigger when the end_date field changes
        frappe.web_form.on('end_date', function(field, value) {
            calculate_percent_amount();  // Call to calculate the percentage amount again when the end date changes

        // Fetch the start_date value to pass it along with the end_date
        let start_date = frappe.web_form.get_value('start_date');
        let tranct_type = frappe.web_form.get_value('transaction_type');

        if (!start_date) {
            console.error("Start date not provided. Cannot proceed.");
            return;
        }

       
        // Call populate_schedule_table with both the start_date and end_date
        if (tranct_type == 'Withdraw'){
            populate_schedule_table('Withdraw', start_date, value);  // Pass the transaction type 'Withdraw', start_date, and end_date

        }

        if (tranct_type == 'Invest' || tranct_type == 'Re-invest'){
            populate_investment_schedule();  // Call the function to populate the investment schedule if needed
        }
       
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
        if (interest_rate && amount) {
            // Calculate the percentage amount
            let percent_amount = (interest_rate / 100) * amount;
            let withdraw_amount = percent_amount + amount;

            // Set the calculated value in the percent_amount field
            frappe.web_form.set_value('percent_amount', percent_amount);
            frappe.web_form.set_value('withdral_amount', withdraw_amount);
        }
    }
    
// Function to populate the investment schedule child table
function populate_investment_schedule() {
    let start_date = frappe.web_form.get_value('start_date');
    let end_date = frappe.web_form.get_value('end_date');
    let interest_rate = parseFloat(frappe.web_form.get_value('interest_rate'));
    let amount = parseFloat(frappe.web_form.get_value('amount'));

    // Define the initial principal amount
    let principal_amount = amount;  // Use the provided amount as principal

    if (start_date && end_date && interest_rate && amount) {
        // Convert the start and end dates to JavaScript Date objects
        start_date = frappe.datetime.str_to_obj(start_date);
        end_date = frappe.datetime.str_to_obj(end_date);

        // Calculate the difference in months between the start and end dates
        let months_diff;
        let start_year = start_date.getFullYear();
        let start_month = start_date.getMonth(); // 0-based index (0 = January)
        let end_year = end_date.getFullYear();
        let end_month = end_date.getMonth(); // 0-based index (0 = January)

        months_diff = (end_year - start_year) * 12 + (end_month - start_month);
        
        // Include the last month if the start day is before or on the end day
        if (start_date.getDate() <= end_date.getDate()) {
            months_diff += 1;
        }

        // Clear existing rows in the investment_schedule child table
        let child_table = frappe.web_form.get_field('investment_schedule');
        // Clear the existing data in the child table
        child_table.df.data = [];

        // Calculate the monthly amount
        let monthly_amount = (interest_rate / 100) * amount / months_diff;
        let available_amount = principal_amount;  // Initial available amount equals the principal

        // Populate new rows for each month in the difference
        let new_rows = [];
        for (let i = 0; i < months_diff; i++) {
        // Calculate the scheduled start date for the current month
        let scheduled_start_date = frappe.datetime.add_months(start_date, i);

        // Ensure scheduled_start_date is a Date object
        if (!(scheduled_start_date instanceof Date)) {
            scheduled_start_date = new Date(scheduled_start_date); // Convert to Date if it's not
            }

        // Increment available amount by the monthly amount for each month
        available_amount += monthly_amount;

        // Function to format the date as 'DD-MM-YYYY'
        function formatDate(date) {
            if (!(date instanceof Date)) {
            throw new Error("Invalid date object");
            }
            let day = String(date.getDate()).padStart(2, '0'); // Get day and pad with zero
            let month = String(date.getMonth() + 1).padStart(2, '0'); // Get month (0-indexed) and pad with zero
            let year = date.getFullYear(); // Get full year
            return `${day}-${month}-${year}`; // Return formatted date
        }

        // Format the scheduled start date
        let formatted_start_date = formatDate(scheduled_start_date);
    
        // Calculate the end date by adding 30 days to the scheduled_start_date
        let end_date = new Date(scheduled_start_date); // Create a new Date object
        end_date.setDate(end_date.getDate() + 28); // Strictly add 30 days
        let formatted_end_date = formatDate(end_date); // Format the end date

    // Create a new row object
    let new_row = {
        start_date: frappe.datetime.obj_to_str(scheduled_start_date),  // Use formatted start date
        end_date: formatted_end_date,      // Use formatted end date
        principal_amount: i === 0 ? principal_amount : 0,  // Principal in the first month only
        available_amount: available_amount,
        amount: monthly_amount,
    };

    new_rows.push(new_row);
}

        // Set the new rows in the child table
        child_table.df.data = new_rows;

        // Refresh the field to show the updated rows
        child_table.refresh();
    }
}

function populate_schedule_table(transaction_type, start_date, end_date) {
    if (transaction_type === 'Withdraw') {
        // Fetch the investment schedule for the withdrawal with the provided date range
        frappe.call({
            method: 'loan_investment_app.custom_api.user.fetch_investment_schedule',
            args: {
                start_date: start_date,  // Pass start date as argument
                end_date: end_date       // Pass end date as argument
            },
            callback: function (response) {
                // console.log(response);
                if (response.message) {
                    // Clear existing rows in the investment_schedule child table
                    let child_table = frappe.web_form.get_field('investment_schedule');
                    console.log(response);

                    // Set the calculated value in the percent_amount field 
                    frappe.web_form.set_value('withdraw_percen_amount', response.message.total_percent_amount);
                    let amount = parseFloat(frappe.web_form.get_value('amount'));
                    let total_amount = amount + response.message.total_percent_amount
                    frappe.web_form.set_value('withdraw_grand_totals', total_amount);
                    

                    // Check if the child table exists before proceeding
                    if (!child_table) {
                        console.error('Child table investment_schedule not found');
                        return; // Exit if the child table is not found
                    }

                    // Clear the existing data in the child table
                    child_table.df.data = [];

                    // Sort the schedule data by the 'parent' field to maintain order
                    let sorted_schedule_data = response.message.investment_schedule_data.sort((a, b) => {
                        return a.parent.localeCompare(b.parent);
                    }); 

                    // Populate new rows based on the sorted response data
                    sorted_schedule_data.forEach(schedule => {
                        // Create a new row object directly from the schedule data
                        let new_row = {
                            start_date: schedule.start_date,  // Assuming schedule has a 'date' field
                            end_date: schedule.end_date,
                            principal_amount: schedule.principal_amount || 0,  // Use provided principal amount
                            available_amount: schedule.available_amount || 0,  // Use provided available amount
                            amount: schedule.amount || 0,  // Use provided amount
                            // invest_id: schedule.parent  // Ensure parent is added in order
                        };

                        // Add the new row to the child table
                        child_table.df.data.push(new_row);
                    });

                    // Set the new rows in the child table
                    child_table.refresh();
                }
            }
        });
    }
}

    // Function to handle the visibility of fields based on transaction_type
    function handle_transaction_type(transaction_type) {
        const fields = ['interest_rate','investor_account_number', 'start_date','withdraw_percen_amount','withdraw_grand_totals',
            'investment_schedule','investor_account_name','pay_to','withdral_amount',
             'end_date','balance_walet', 'investor_bank_name','percent_amount', 'mode_of_payment'];
        
        if (transaction_type === 'Invest' || transaction_type === 'Re-invest') {
            // Make fields visible for 'Invest' and 'Re-invest'
            frappe.web_form.set_df_property('interest_rate', 'hidden', 0);
            frappe.web_form.set_df_property('start_date', 'hidden', 0);
            frappe.web_form.set_df_property('end_date', 'hidden', 1);
            frappe.web_form.set_df_property('percent_amount', 'hidden', 1);
            frappe.web_form.set_df_property('mode_of_payment', 'hidden', 1);
            frappe.web_form.set_df_property('investor_bank_name', 'hidden', 1);
            frappe.web_form.set_df_property('investor_account_number', 'hidden', 1);
            frappe.web_form.set_df_property('investment_schedule', 'hidden', 0);
            frappe.web_form.set_df_property('investor_account_name', 'hidden', 1);
        } else if (transaction_type === 'Deposit') {
            // Make mode_of_payment visible for 'Deposit' and 'Withdraw'
            frappe.web_form.set_df_property('interest_rate', 'hidden', 1);
            frappe.web_form.set_df_property('start_date', 'hidden', 1);
            frappe.web_form.set_df_property('end_date', 'hidden', 1);
            frappe.web_form.set_df_property('percent_amount', 'hidden', 1);
            frappe.web_form.set_df_property('mode_of_payment', 'hidden', 1);
            frappe.web_form.set_df_property('investment_schedule', 'hidden', 1);
            frappe.web_form.set_df_property('withdral_amount', 'hidden', 1);
            frappe.web_form.set_df_property('investor_bank_name', 'hidden', 1);
            frappe.web_form.set_df_property('investor_account_number', 'hidden', 1);
            frappe.web_form.set_df_property('investor_account_name', 'hidden', 1);
            frappe.web_form.set_df_property('balance_walet', 'hidden', 0);
        }
        else if (transaction_type === 'Withdraw') {
            // Make mode_of_payment visible for 'Deposit' and 'Withdraw' investor_bank_name
            frappe.web_form.set_df_property('interest_rate', 'hidden', 1);
            frappe.web_form.set_df_property('start_date', 'hidden', 0);
            frappe.web_form.set_df_property('end_date', 'hidden', 1);
            frappe.web_form.set_df_property('withdraw_percen_amount', 'hidden', 0);
            frappe.web_form.set_df_property('mode_of_payment', 'hidden', 1);
            frappe.web_form.set_df_property('investment_schedule', 'hidden', 0);
            frappe.web_form.set_df_property('withdral_amount', 'hidden', 1);
            frappe.web_form.set_df_property('investor_bank_name', 'hidden', 1);
            frappe.web_form.set_df_property('investor_account_number', 'hidden', 1);
            frappe.web_form.set_df_property('investor_account_name', 'hidden', 1);
            frappe.web_form.set_df_property('balance_walet', 'hidden', 0);
        }
        
        
        else if (transaction_type === 'Request Payment') { 
            // Make mode_of_payment visible for 'Deposit' and 'Withdraw' pay_to
            frappe.web_form.set_df_property('interest_rate', 'hidden', 1);
            frappe.web_form.set_df_property('start_date', 'hidden', 1);
            frappe.web_form.set_df_property('end_date', 'hidden', 1);
            frappe.web_form.set_df_property('percent_amount', 'hidden', 1);
            frappe.web_form.set_df_property('mode_of_payment', 'hidden', 1);
            frappe.web_form.set_df_property('investment_schedule', 'hidden', 1);
            frappe.web_form.set_df_property('withdral_amount', 'hidden', 1);
            frappe.web_form.set_df_property('investor_bank_name', 'hidden', 0);
            frappe.web_form.set_df_property('investor_account_number', 'hidden', 0);
            frappe.web_form.set_df_property('investor_account_name', 'hidden', 0);
            frappe.web_form.set_df_property('balance_walet', 'hidden', 0);
            frappe.web_form.set_df_property('pay_to', 'hidden', 1);
        }      
        else if (transaction_type === 'Transfer') {
            // Hide all fields for 'Transfer'
            fields.forEach(field => {
                frappe.web_form.set_df_property(field, 'hidden', 1);
                frappe.web_form.set_df_property('balance_walet', 'hidden', 0);
            });
        } else {
            // Default case: Hide all fields
            fields.forEach(field => {
                frappe.web_form.set_df_property(field, 'hidden', 1);
            });
        }
    }
});
