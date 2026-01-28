// // Copyright (c) 2026, Siddhant Hybrowlabs and contributors
// // For license information, please see license.txt
// frappe.query_reports["Ticket Management"] = {
// 	filters: [
// 		{
// 			fieldname: "from_date",
// 			label: __("From Date"),
// 			fieldtype: "Date"
// 		},
// 		{
// 			fieldname: "to_date",
// 			label: __("To Date"),
// 			fieldtype: "Date"
// 		},
// 		{
// 			fieldname: "robot_serial_no",
// 			label: __("Robot Serial No"),
// 			fieldtype: "Link",
// 			options: "Robot Tracker"
// 		},
// 		{
// 			fieldname: "hospital_name",
// 			label: __("Hospital Name"),
// 			fieldtype: "Link",
// 			options: "Account Master"
// 		},
// 		{
// 			fieldname: "priority",
// 			label: __("Priority"),
// 			fieldtype: "Select",
// 			options: ["", "Low", "Medium"]
// 		},
// 		{
// 			fieldname: "status",
// 			label: __("Status"),
// 			fieldtype: "Select",
// 			options: ["", "Open", "In Progress", "Resolved", "Closed"]
// 		}
// 	]
// };


frappe.query_reports["Ticket Management"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			on_change: () => frappe.query_report.refresh()
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			on_change: () => frappe.query_report.refresh()
		},
		{
			fieldname: "state",
			label: __("State"),
			fieldtype: "Link",
			options: "State",
			get_query: () => {
				let filters = frappe.query_report.get_filter_values();
				return {
					query: "merai_newage.merai_newage.report.ticket_management.ticket_management.get_state",
					filters: {
						from_date: filters.from_date,
						to_date: filters.to_date
					}
				};
			}
		},
		{
			fieldname: "robot_serial_no",
			label: __("Robot Serial No"),
			fieldtype: "Link",
			options: "Robot Tracker",
			get_query: () => {
				let filters = frappe.query_report.get_filter_values();
				return {
					query: "merai_newage.merai_newage.report.ticket_management.ticket_management.get_robot_serials",
					filters: {
						from_date: filters.from_date,
						to_date: filters.to_date
					}
				};
			}
		},
		{
			fieldname: "hospital_name",
			label: __("Hospital Name"),
			fieldtype: "Link",
			options: "Account Master",
			get_query: () => {
				let filters = frappe.query_report.get_filter_values();
				return {
					query: "merai_newage.merai_newage.report.ticket_management.ticket_management.get_hospitals",
					filters: {
						from_date: filters.from_date,
						to_date: filters.to_date
					}
				};
			}
		},
		{
			fieldname: "priority",
			label: __("Priority"),
			fieldtype: "Select",
			options: ["", "Low", "Medium"]
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Open", "In Progress", "Resolved", "Closed"]
		}
	]
};
