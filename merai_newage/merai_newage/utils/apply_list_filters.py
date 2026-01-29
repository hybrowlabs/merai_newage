# Save this file in your Frappe app at:
# merai_newage/merai_newage/utils/apply_list_filters.py

import frappe
import json

@frappe.whitelist()
def redirect_with_filters(filters_json):
    """
    API endpoint to handle filter application and return proper list view URL
    """
    try:
        filters = json.loads(filters_json)
        
        # Build the filter array for Frappe list view
        filter_list = []
        
        # Handle each filter type
        for key, value in filters.items():
            if value:
                if key.endswith('_not'):
                    # Handle not equal filters
                    actual_key = key.replace('_not', '')
                    filter_list.append(['Ticket Master', actual_key, '!=', value])
                elif key == 'creation_from' and filters.get('creation_to'):
                    # Handle date range
                    filter_list.append(['Ticket Master', 'creation', 'between', 
                                       [value + ' 00:00:00', filters['creation_to'] + ' 23:59:59']])
                elif key == 'creation_to':
                    # Skip, handled with creation_from
                    continue
                else:
                    # Standard equality filter
                    filter_list.append(['Ticket Master', key, '=', value])
        
        return {
            'success': True,
            'filters': filter_list,
            'redirect_url': '/app/ticket-master'
        }
        
    except Exception as e:
        frappe.log_error(f"Filter application error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }