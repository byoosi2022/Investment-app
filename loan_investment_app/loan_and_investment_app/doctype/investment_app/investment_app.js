// Copyright (c) 2024, paul and contributors
// For license information, please see license.txt
frappe.ui.form.on('Investment App', {
    // Triggered when the form is refreshed
    refresh: function(frm) {
        handle_transaction_type(frm);
    },
    refresh: function(frm) {
        if (!frm.doc.investment_schedule || frm.doc.investment_schedule.length === 0) {
            calculate_and_populate_schedule(frm);
             // Save the document after populating the schedule
             frm.save();
        }
    },
    // Triggered when transaction_type field is changed
    transaction_type: function(frm) {
        handle_transaction_type(frm);
    },
    interest_rate: function(frm) {
        calculate_and_populate_schedule(frm);
    },
    amount: function(frm) {
        calculate_and_populate_schedule(frm);
    },
    start_date: function(frm) {
        calculate_and_populate_schedule(frm);
    },
    end_date: function(frm) {
        calculate_and_populate_schedule(frm);
    }
});

function calculate_and_populate_schedule(frm) {
    let percent_amount = (frm.doc.interest_rate / 100) * frm.doc.amount;
    let withdraw_amount = frm.doc.amount + frm.doc.percent_amount;
    frm.set_value('percent_amount', percent_amount);
    frm.set_value('withdral_amount', withdraw_amount);

    if (frm.doc.interest_rate && frm.doc.amount && frm.doc.start_date) {
        // Calculate the percentage amount withdral_amount
        let percent_amount = (frm.doc.interest_rate / 100) * frm.doc.amount;
        let withdraw_amount = frm.doc.amount + frm.doc.percent_amount;
        frm.set_value('percent_amount', percent_amount);
        frm.set_value('withdral_amount', withdraw_amount);

        // Initialize the principal amount
        let principal_amount = frm.doc.amount;

        // Calculate the difference in months between the start and end dates
        let start_date = frappe.datetime.str_to_obj(frm.doc.start_date);
        let end_date = frm.doc.end_date ? frappe.datetime.str_to_obj(frm.doc.end_date) : null;

       
        // If the end date is provided, calculate the total number of months
        let months_diff;
        if (end_date) {
            let start_year = start_date.getFullYear();
            let start_month = start_date.getMonth(); // 0-based index (0 = January)
            let end_year = end_date.getFullYear();
            let end_month = end_date.getMonth(); // 0-based index (0 = January)

            months_diff = (end_year - start_year) * 12 + (end_month - start_month);

            // Include the last month if the end date is the end of the month or if the start date is before the end of the month
            if (start_date.getDate() <= end_date.getDate()) {
                months_diff += 1; // Include the last month
            }
        } else {
            // If end date is not provided, assume a 12-month schedule
            months_diff = 12;
        }

        // Calculate the monthly amount
        let monthly_amount = percent_amount / months_diff;
         // Start available amount at 31000 instead of 30000
         let available_amount = principal_amount + monthly_amount;

        // Clear the existing schedule table
        frm.clear_table('investment_schedule');

        // Populate the Investment Schedule table
        for (let i = 0; i < months_diff; i++) {
            let scheduled_date = frappe.datetime.add_months(start_date, i);

            // Add the monthly increment to the available amount
            if (i > 0) {
                available_amount += monthly_amount; // Increment by 1000 each month
            }

            // Add the new row to the schedule
            frm.add_child('investment_schedule', {
                date: frappe.datetime.obj_to_str(scheduled_date),
                principal_amount: i === 0 ? principal_amount : 0, // Set principal_amount only for the first month
                available_amount: available_amount, // Incremented value for each month
                amount: monthly_amount // Constant monthly amount
            });
        }

        // Update the end date to reflect the last scheduled payment
        frm.refresh_field('investment_schedule');
    }
}

// Function to handle the visibility of fields based on transaction_type
function handle_transaction_type(frm) {
    if (frm.doc.transaction_type === 'Invest' || frm.doc.transaction_type === 'Re-invest') {
        // Make fields visible for 'Invest' and 'Re-invest'
        frm.set_df_property('interest_rate', 'hidden', 0);
        frm.set_df_property('start_date', 'hidden', 0);
        frm.set_df_property('end_date', 'hidden', 0);
        frm.set_df_property('percent_amount', 'hidden', 0);
        frm.set_df_property('mode_of_payment', 'hidden', 1);
    } else if (frm.doc.transaction_type === 'Deposit' || frm.doc.transaction_type === 'Withdraw') {
        // Make mode_of_payment visible for 'Deposit' and 'Withdraw'
        frm.set_df_property('interest_rate', 'hidden', 0);
        frm.set_df_property('start_date', 'hidden', 1);
        frm.set_df_property('end_date', 'hidden', 1);
        frm.set_df_property('percent_amount', 'hidden', 0);
        frm.set_df_property('mode_of_payment', 'hidden', 0);
    } else if (frm.doc.transaction_type === 'Transfer') {
        // Hide all fields for 'Transfer'
        frm.set_df_property('interest_rate', 'hidden', 1);
        frm.set_df_property('start_date', 'hidden', 1);
        frm.set_df_property('end_date', 'hidden', 1);
        frm.set_df_property('percent_amount', 'hidden', 1);
        frm.set_df_property('mode_of_payment', 'hidden', 1);
    } else {
        // Default case: Hide all fields
        frm.set_df_property('interest_rate', 'hidden', 0);
        frm.set_df_property('start_date', 'hidden', 1);
        frm.set_df_property('end_date', 'hidden', 1);
        frm.set_df_property('percent_amount', 'hidden', 0);
        frm.set_df_property('mode_of_payment', 'hidden', 1);
    }
}
