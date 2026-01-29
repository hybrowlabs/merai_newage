// Save this file as: ticket_master_list.js
// Add to Ticket Master DocType: Setup > Customize Form > Ticket Master > 
// In "List JS" field, paste this code

frappe.listview_settings['Ticket Master'] = {
    onload: function(listview) {
        console.log('Ticket Master list view loaded');
        
        // Check for pending filters from dashboard
        try {
            const pendingFilters = sessionStorage.getItem('pending_list_filters');
            
            if (pendingFilters) {
                console.log('Found pending filters:', pendingFilters);
                const filters = JSON.parse(pendingFilters);
                
                // Clear the stored filters
                sessionStorage.removeItem('pending_list_filters');
                
                // Apply each filter
                setTimeout(() => {
                    filters.forEach(filter => {
                        const [doctype, fieldname, condition, value] = filter;
                        console.log(`Applying filter: ${fieldname} ${condition} ${value}`);
                        
                        // Add filter to list view
                        listview.filter_area.add(doctype, fieldname, condition, value);
                    });
                    
                    // Refresh the list to apply filters
                    listview.refresh();
                }, 500);
            }
        } catch (e) {
            console.error('Error applying dashboard filters:', e);
        }
        
        // Also listen for postMessage events
        window.addEventListener('message', function(event) {
            if (event.data && event.data.type === 'apply_dashboard_filters') {
                console.log('Received filters via postMessage:', event.data.filters);
                
                try {
                    event.data.filters.forEach(filter => {
                        const [doctype, fieldname, condition, value] = filter;
                        listview.filter_area.add(doctype, fieldname, condition, value);
                    });
                    listview.refresh();
                } catch (e) {
                    console.error('Error applying filters from postMessage:', e);
                }
            }
        });
    }
};