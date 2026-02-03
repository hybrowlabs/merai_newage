// // Save this file as: ticket_master_list.js
// // Add to Ticket Master DocType: Setup > Customize Form > Ticket Master > 
// // In "List JS" field, paste this code

// frappe.listview_settings['Ticket Master'] = {
//     onload: function(listview) {
//         console.log('Ticket Master list view loaded');
        
//         // Check for pending filters from dashboard
//         try {
//             const pendingFilters = sessionStorage.getItem('pending_list_filters');
            
//             if (pendingFilters) {
//                 console.log('Found pending filters:', pendingFilters);
//                 const filters = JSON.parse(pendingFilters);
                
//                 // Clear the stored filters
//                 sessionStorage.removeItem('pending_list_filters');
                
//                 // Apply each filter
//                 setTimeout(() => {
//                     filters.forEach(filter => {
//                         const [doctype, fieldname, condition, value] = filter;
//                         console.log(`Applying filter: ${fieldname} ${condition} ${value}`);
                        
//                         // Add filter to list view
//                         listview.filter_area.add(doctype, fieldname, condition, value);
//                     });
                    
//                     // Refresh the list to apply filters
//                     listview.refresh();
//                 }, 500);
//             }
//         } catch (e) {
//             console.error('Error applying dashboard filters:', e);
//         }
        
//         // Also listen for postMessage events
//         window.addEventListener('message', function(event) {
//             if (event.data && event.data.type === 'apply_dashboard_filters') {
//                 console.log('Received filters via postMessage:', event.data.filters);
                
//                 try {
//                     event.data.filters.forEach(filter => {
//                         const [doctype, fieldname, condition, value] = filter;
//                         listview.filter_area.add(doctype, fieldname, condition, value);
//                     });
//                     listview.refresh();
//                 } catch (e) {
//                     console.error('Error applying filters from postMessage:', e);
//                 }
//             }
//         });
//     }
// };


// Save this file as: ticket_master_list.js
// Add to Ticket Master DocType: Setup > Customize Form > Ticket Master > 
// In "List JS" field, paste this code

frappe.listview_settings['Ticket Master'] = {
    onload: function(listview) {
        console.log('=== Ticket Master List View Loaded ===');
        
        // Flag to prevent duplicate filter application
        let filtersApplied = false;
        
        // CRITICAL: Clear ALL existing filters first
        function clearAllFilters() {
            console.log('Clearing all existing filters...');
            
            try {
                // Method 1: Clear filter area
                if (listview.filter_area) {
                    listview.filter_area.clear();
                }
                
                // Method 2: Clear programmatically
                if (listview.page && listview.page.clear_filters) {
                    listview.page.clear_filters();
                }
                
                // Method 3: Remove all filter pills
                const filterPills = document.querySelectorAll('.filter-pill');
                filterPills.forEach(pill => {
                    try {
                        pill.remove();
                    } catch(e) {
                        console.error('Error removing filter pill:', e);
                    }
                });
                
                console.log('All filters cleared successfully');
            } catch (e) {
                console.error('Error during filter clearing:', e);
            }
        }
        
        // Function to apply filters
        function applyFilters(filters) {
            if (filtersApplied) {
                console.log('Filters already applied, skipping duplicate application');
                return;
            }
            
            console.log('Applying filters:', filters);
            
            try {
                // First, clear everything
                clearAllFilters();
                
                // Small delay to ensure clearing is complete
                setTimeout(() => {
                    // Apply each filter
                    filters.forEach(filter => {
                        const [doctype, fieldname, condition, value] = filter;
                        console.log(`Adding filter: ${fieldname} ${condition} ${value}`);
                        
                        try {
                            listview.filter_area.add(doctype, fieldname, condition, value);
                        } catch (e) {
                            console.error(`Error adding filter ${fieldname}:`, e);
                        }
                    });
                    
                    // Refresh the list to apply filters
                    setTimeout(() => {
                        listview.refresh();
                        filtersApplied = true;
                        console.log('Filters applied and list refreshed');
                    }, 100);
                }, 100);
            } catch (e) {
                console.error('Error applying filters:', e);
            }
        }
        
        // Check for pending filters from dashboard (Method 1: sessionStorage)
        try {
            const pendingFilters = sessionStorage.getItem('pending_list_filters');
            
            if (pendingFilters) {
                console.log('Found pending filters in sessionStorage:', pendingFilters);
                const filters = JSON.parse(pendingFilters);
                
                // Clear the stored filters to prevent re-application
                sessionStorage.removeItem('pending_list_filters');
                
                // Apply filters after a short delay
                setTimeout(() => {
                    applyFilters(filters);
                }, 500);
            }
        } catch (e) {
            console.error('Error checking sessionStorage filters:', e);
        }
        
        // Listen for postMessage events (Method 2: postMessage)
        window.addEventListener('message', function(event) {
            // Verify message origin for security
            if (event.origin !== window.location.origin) {
                console.warn('Ignoring message from untrusted origin:', event.origin);
                return;
            }
            
            if (event.data && event.data.type === 'clear_all_filters') {
                console.log('Received clear_all_filters command');
                clearAllFilters();
                filtersApplied = false;
            }
            
            if (event.data && event.data.type === 'apply_dashboard_filters') {
                console.log('Received apply_dashboard_filters command:', event.data.filters);
                
                // Reset the applied flag if clearExisting is true
                if (event.data.clearExisting) {
                    filtersApplied = false;
                    clearAllFilters();
                }
                
                setTimeout(() => {
                    applyFilters(event.data.filters);
                }, 300);
            }
        });
        
        console.log('List view setup complete, waiting for filters...');
    },
    
    // Add custom buttons if needed
    get_indicator: function(doc) {
        // Custom status indicators
        const status_colors = {
            'Open': 'blue',
            'Pending': 'orange',
            'In Progress': 'yellow',
            'Resolved': 'green',
            'Cancelled': 'grey',
            'Closed': 'grey'
        };
        
        return [__(doc.workflow_state), status_colors[doc.workflow_state] || 'grey', 'workflow_state,=,' + doc.workflow_state];
    }
};