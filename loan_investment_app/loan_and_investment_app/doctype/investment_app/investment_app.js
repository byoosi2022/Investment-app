// Copyright (c) 2024, paul and contributors
// For license information, please see license.txt
frappe.ui.form.on('Investment App', {
    // Triggered when the form is refreshed
    onload: function (frm) {
        handle_transaction_type(frm);
    },
    refresh: function (frm) {
        if (!frm.doc.investment_schedule || frm.doc.investment_schedule.length === 0) {
            calculate_and_populate_schedule(frm);
            // Save the document after populating the schedule
            frm.save();
        }
    },
    // Triggered when transaction_type field is changed
    transaction_type: function (frm) {
        handle_transaction_type(frm);
    },

    party: function (frm) {
        update_party_name(frm);
    },

    interest_rate: function (frm) {
        calculate_and_populate_schedule(frm);
    },
    amount: function (frm) {
        calculate_and_populate_schedule(frm);
    },
    start_date: function (frm) {
        if (frm.doc.investment_period) {
            populate_investment_schedule(frm);
        }
    },
    end_date: function (frm) {
        if (frm.doc.investment_period && frm.doc.start_date) {
            populate_investment_schedule(frm);
        }
    },
    investment_period: function (frm) {
        if (frm.doc.investment_period) {
            set_end_date(frm); // Ensure end date is set first
            populate_investment_schedule(frm);
        }
    }


});


function calculate_and_populate_schedule(frm) {
    // Calculate percentage amount and withdrawal amount transaction_type === 'Invest' || transaction_type === 'Re-invest'
    if (frm.doc.transaction_type === 'Invest' || frm.doc.transaction_type === 'Re-invest') {
        let percent_amount = (frm.doc.interest_rate / 100) * frm.doc.amount;
        let withdraw_amount = frm.doc.amount + percent_amount;
        frm.set_value('percent_amount', percent_amount);
        frm.set_value('withdral_amount', withdraw_amount); // Corrected the field name

        frm.set_df_property('withhold_tax', 'hidden', 1);
        frm.set_df_property('total_interest_amount', 'hidden', 1);
        frm.set_df_property('total_amount_after_tax', 'hidden', 1);



        if (frm.doc.interest_rate && frm.doc.amount && frm.doc.start_date) {
            // Initialize principal amount
            let principal_amount = frm.doc.amount;

            // Parse start and end dates
            let start_date = frappe.datetime.str_to_obj(frm.doc.start_date);
            let end_date = frm.doc.end_date ? frappe.datetime.str_to_obj(frm.doc.end_date) : null;

            // Calculate the difference in months between start and end dates
            let months_diff;
            if (end_date) {
                let start_year = start_date.getFullYear();
                let start_month = start_date.getMonth();
                let end_year = end_date.getFullYear();
                let end_month = end_date.getMonth();

                months_diff = (end_year - start_year) * 12 + (end_month - start_month);

                // Include the last month if the end date is after the start date
                if (start_date.getDate() <= end_date.getDate()) {
                    months_diff += 1; // Include the last month
                }
            } else {
                // Default to 12 months if no end date is provided
                months_diff = 12;
            }

            // Calculate monthly amount based on percentage amount
            let monthly_amount = percent_amount / months_diff;

            // Start available amount at 31000 instead of 30000
            let available_amount = principal_amount + monthly_amount;

            // Clear existing schedule table
            frm.clear_table('investment_schedule');

            // Populate the Investment Schedule table
            for (let i = 0; i < months_diff; i++) {
                let scheduled_date = frappe.datetime.add_months(start_date, i);

                // Ensure scheduled_date is a valid Date object
                if (typeof scheduled_date === "string") {
                    scheduled_date = frappe.datetime.str_to_obj(scheduled_date);
                }

                // Validate the date object
                if (!(scheduled_date instanceof Date) || isNaN(scheduled_date)) {
                    console.error("Invalid scheduled date", scheduled_date);
                    continue; // Skip invalid date
                }

                // Add the monthly increment to the available amount starting from the second month
                if (i > 0) {
                    available_amount += monthly_amount;
                }

                // Format the scheduled date
                let formatted_start_date = frappe.datetime.obj_to_str(scheduled_date);

                // Calculate and format the end date (add 28 days to the scheduled start date)
                let scheduled_end_date = new Date(scheduled_date);
                scheduled_end_date.setDate(scheduled_end_date.getDate() + 28);
                let formatted_end_date = frappe.datetime.obj_to_str(scheduled_end_date);

                // Add the new row to the schedule
                frm.add_child('investment_schedule', {
                    start_date: formatted_start_date,
                    end_date: formatted_end_date,
                    principal_amount: i === 0 ? principal_amount : 0, // Set principal_amount only for the first month
                    available_amount: available_amount, // Incremented value for each month
                    amount: monthly_amount // Constant monthly amount
                });
            }

            // Update the schedule table
            frm.refresh_field('investment_schedule');
        }

    }
}

// Helper function to format date as 'YYYY-MM-DD'
function formatDate(date) {
    if (!(date instanceof Date)) {
        throw new Error("Invalid date object");
    }
    let day = String(date.getDate()).padStart(2, '0'); // Pad day with zero if needed
    let month = String(date.getMonth() + 1).padStart(2, '0'); // Pad month with zero (months are 0-indexed)
    let year = date.getFullYear(); // Get the full year
    return `${year}-${month}-${day}`; // Return formatted date as 'YYYY-MM-DD'
}

// Function to handle the visibility of fields based on transaction_type
function handle_transaction_type(frm) {
    let fields = [
        'interest_rate', 'investor_account_number', 'posting_date',
        'start_date', 'withdraw_percen_amount', 'withdraw_grand_totals',
        'investment_schedule', 'investor_account_name', 'pay_to', 'withdraw_amount',
        'end_date', 'total_amount_invested', 'address', 'total_interest_earned',
        'investment_period', 'balance_wallet', 'available_amount_in_wallet',
        'amount_withdrawn', 'interest_withdrawn', 'investor_bank_name',
        'percent_amount', 'mode_of_payment'
    ];

    // Default to hiding all fields
    fields.forEach(field => {
        frm.set_df_property(field, 'hidden', 1);
    });

    // Adjust visibility based on transaction_type
    switch (frm.doc.transaction_type) {
        case 'Invest':
        case 'Re-invest':
            // Make fields visible for 'Invest' and 'Re-invest' 
            frm.set_df_property('interest_rate', 'hidden', 0);
            frm.set_df_property('start_date', 'hidden', 0);
            frm.set_df_property('end_date', 'hidden', 0);
            frm.set_df_property('percent_amount', 'hidden', 0);
            frm.set_df_property('mode_of_payment', 'hidden', 1);
            frm.set_df_property('amount_withrowned', 'hidden', 0);
            frm.set_df_property('interets_withrowned', 'hidden', 0);
            frm.set_df_property('withhold_tax', 'hidden', 0);
            frm.set_df_property('percent_amount', 'hidden', 0);
            frm.set_df_property('total_interest_amount', 'hidden', 0);
            frm.set_df_property('total_amount_after_tax', 'hidden', 0);
            frm.set_df_property('interest_rate', 'hidden', 0);
            frm.set_df_property('start_date', 'hidden', 0);
            frm.set_df_property('end_date', 'hidden', 0);
            frm.set_df_property('investment_period', 'hidden', 0);
            frm.set_df_property('investment_schedule', 'hidden', 0);
            break;

        case 'Deposit':
            // Hide specific fields for 'Request for Payments' pay_to
            frm.set_df_property('amount_withrowned', 'hidden', 1);
            frm.set_df_property('interets_withrowned', 'hidden', 1);
            frm.set_df_property('withhold_tax', 'hidden', 1);
            frm.set_df_property('mode_of_payment', 'hidden', 0);
            frm.set_df_property('percent_amount', 'hidden', 1);
            frm.set_df_property('total_interest_amount', 'hidden', 1);
            frm.set_df_property('total_amount_after_tax', 'hidden', 1);
            frm.set_df_property('interest_rate', 'hidden', 1);
            frm.set_df_property('start_date', 'hidden', 1);
            frm.set_df_property('end_date', 'hidden', 1);
            frm.set_df_property('investment_period', 'hidden', 1);
            frm.set_df_property('investor_bank_name', 'hidden', 1);
            frm.set_df_property('investor_account_number', 'hidden', 1);
            frm.set_df_property('investor_account_name', 'hidden', 1);
            frm.set_df_property('pay_to', 'hidden', 1);
            break;
        case 'Withdraw':
            // Make mode_of_payment visible for 'Deposit' and 'Withdraw'
            frm.set_df_property('interest_rate', 'hidden', 0);
            frm.set_df_property('start_date', 'hidden', 1);
            frm.set_df_property('end_date', 'hidden', 1);
            frm.set_df_property('percent_amount', 'hidden', 0);
            frm.set_df_property('mode_of_payment', 'hidden', 0);
            frm.set_df_property('withhold_tax', 'hidden', 0);
            frm.set_df_property('total_interest_amount', 'hidden', 0);
            frm.set_df_property('total_amount_after_tax', 'hidden', 0);
            break;

        case 'Transfer':
            // Hide all fields for 'Transfer'
            frm.set_df_property('interest_rate', 'hidden', 1);
            frm.set_df_property('start_date', 'hidden', 1);
            frm.set_df_property('end_date', 'hidden', 1);
            frm.set_df_property('percent_amount', 'hidden', 1);
            frm.set_df_property('mode_of_payment', 'hidden', 1);
            break;

        case 'Request for Payments':
            // Hide specific fields for 'Request for Payments' pay_to
            frm.set_df_property('amount_withrowned', 'hidden', 1);
            frm.set_df_property('interets_withrowned', 'hidden', 1);
            frm.set_df_property('withhold_tax', 'hidden', 1);
            frm.set_df_property('percent_amount', 'hidden', 1);
            frm.set_df_property('total_interest_amount', 'hidden', 1);
            frm.set_df_property('total_amount_after_tax', 'hidden', 1);
            frm.set_df_property('interest_rate', 'hidden', 1);
            frm.set_df_property('start_date', 'hidden', 1);
            frm.set_df_property('end_date', 'hidden', 1);
            frm.set_df_property('investment_period', 'hidden', 1);
            frm.set_df_property('investor_bank_name', 'hidden', 0);
            frm.set_df_property('investor_account_number', 'hidden', 0);
            frm.set_df_property('investor_account_name', 'hidden', 0);
            frm.set_df_property('pay_to', 'hidden', 0);
            break;
    }
}


function update_party_name(frm) {
    frappe.call({
        method: 'loan_investment_app.custom_api.user.get_party_name',
        args: {
            party: frm.doc.party
        },
        callback: function (response) {
            console.log(response);
            if (response.message) {
                // Set the fetched user information to the appropriate fields
                frm.set_value('party_name', response.message.member_name);

            }
        }
    });

}



//updated 20/9/2029
function populate_investment_schedule(frm) {
    let start_date = frm.doc.start_date;
    let end_date = frm.doc.end_date;
    let interest_rate = parseFloat(frm.doc.interest_rate);
    let amount = parseFloat(frm.doc.amount);
    let investment_period = frm.doc.investment_period;

    // Trim any whitespace
    investment_period = investment_period ? investment_period.trim() : '';

    console.log("Selected Investment Period:", investment_period);  // Debugging statement

    // Define the initial principal amount
    let principal_amount = amount;

    if (start_date && end_date && interest_rate && amount && investment_period) {
        // Convert the start and end dates to JavaScript Date objects
        start_date = frappe.datetime.str_to_obj(start_date);
        end_date = frappe.datetime.str_to_obj(end_date);

        // Calculate the difference in months based on the selected investment period
        let months_diff;
        switch (investment_period) {
            case '6 Months':
                months_diff = 6;
                break;
            case '1 Year':
                months_diff = 12;
                break;
            case '2 Years':
                months_diff = 24;
                break;
            case '3 Years':
                months_diff = 36;
                break;
            case '4 Years':
                months_diff = 48;
                break;
            case '5 Years':
                months_diff = 60; // Make sure this is set to 60
                break;
            case '6 Years':
                months_diff = 72;
                break;
            default:
                frappe.msgprint(__('Please select a valid investment period.'));
                return;
        }

        // Clear existing rows in the investment_schedule child table
        frm.clear_table('investment_schedule');

        // Calculate the monthly amount
        let monthly_amount = (interest_rate / 100) * amount / months_diff;
        let available_amount = principal_amount;

        // Utility function to format the date as 'DD-MM-YYYY'
        function formatDate(date) {
            let day = String(date.getDate()).padStart(2, '0');
            let month = String(date.getMonth() + 1).padStart(2, '0');
            let year = date.getFullYear();
            return `${day}-${month}-${year}`;
        }

        // Function to get the last day of a month (handling 28-day months)
        function getLastDayOfMonth(date) {
            let lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
            // If it's February, enforce 28 days (to cover the leap year case)
            if (lastDay.getMonth() === 1) {
                lastDay.setDate(28);
            }
            return lastDay;
        }

        // Populate new rows for each month in the difference
        for (let i = 0; i < months_diff; i++) {
            // Calculate the scheduled start date for the current month
            let scheduled_start_date = frappe.datetime.add_months(start_date, i);

            // Ensure it's a Date object
            if (!(scheduled_start_date instanceof Date)) {
                scheduled_start_date = new Date(scheduled_start_date);
            }

            // Increment available amount by the monthly amount for each month
            available_amount += monthly_amount;

            // Format the scheduled start date
            let formatted_start_date = formatDate(scheduled_start_date);

            // Calculate the end date as the last day of the current month (with 28-day months)
            let calculated_end_date = getLastDayOfMonth(scheduled_start_date);
            let formatted_end_date = formatDate(calculated_end_date);

            // Add a new row to the child table
            let new_row = frm.add_child('investment_schedule');
            new_row.start_date = frappe.datetime.obj_to_str(scheduled_start_date);
            new_row.end_date = formatted_end_date;  // Last day of the month or 28th day for February
            new_row.principal_amount = i === 0 ? principal_amount : 0;  // Principal in the first month only
            new_row.available_amount = available_amount;
            new_row.amount = monthly_amount;
        }

        // Refresh the field to show the updated rows
        frm.refresh_field('investment_schedule');
    } else {
        frappe.msgprint(__('Please make sure all required fields are filled.'));
    }
}


function set_end_date(frm) {
    // Get start date and investment period from the form
    let start_date = frm.doc.start_date;
    let investment_period = frm.doc.investment_period;

    // Ensure the start date is valid before proceeding
    if (start_date) {
        // Convert start date string to a Date object
        let end_date = new Date(start_date);

        // Adjust the end date based on the selected investment period
        switch (investment_period) {
            case '6 Months':
                end_date.setMonth(end_date.getMonth() + 6);
                break;
            case '1 Year':
                end_date.setFullYear(end_date.getFullYear() + 1);
                break;
            case '2 Years':
                end_date.setFullYear(end_date.getFullYear() + 2);
                break;
            case '3 Years':
                end_date.setFullYear(end_date.getFullYear() + 3);
                break;
            case '4 Years':
                end_date.setFullYear(end_date.getFullYear() + 4);
                break;
            case '5 Years':
                end_date.setFullYear(end_date.getFullYear() + 5);
                break;
            case '6 Years':
                end_date.setFullYear(end_date.getFullYear() + 6);
                break;
            default:
                // Handle cases where no valid period is selected
                frappe.msgprint(__('Please select a valid investment period'));
                return;
        }

        // Always set to the last day of the month, considering months as 28 days
        end_date.setDate(28);

        // Format the end_date to 'YYYY-MM-DD'
        let formatted_end_date = end_date.toISOString().split('T')[0]; // Extract only the date portion

        // Set the calculated end date back into the form
        frm.set_value('end_date', formatted_end_date);
    } else {
        frappe.msgprint(__('Please select a start date first.'));
    }
}
