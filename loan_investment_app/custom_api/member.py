import frappe
from frappe import _

# Define the validate function
def validate_member(doc, method=None):
    # Get the logged-in user
    user = frappe.session.user
    
    # Check if the logged-in user has the "Investor" role, but allow Administrator
    if "Investor" in frappe.get_roles(user) and "Administrator" not in frappe.get_roles(user):
        # Check if the user already has a Member entry (excluding the current one)
        existing_member = frappe.db.exists("Member", {"owner": user, "name": ("!=", doc.name)})
        
        # If there is an existing entry, prevent saving
        if existing_member:
            frappe.throw(_("You are already registered as a Member and cannot create another entry."))
