// Copyright (c) 2026, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt

// frappe.query_reports["Vendor Aging Report"] = {
// 	"filters": [

// 	]
// };



// Vendor Aging Report — filters & color formatter

frappe.query_reports["Vendor Aging Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "report_date",
			label: __("Ageing As On Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "ageing_based_on",
			label: __("Ageing Based On"),
			fieldtype: "Select",
			options: "Due Date\nPosting Date\nDocument Date",
			default: "Due Date",
			reqd: 1,
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		const aging_buckets = [
			"bucket_0_30", "bucket_31_60", "bucket_61_90",
			"bucket_91_120", "bucket_121_150", "bucket_151_180",
			"bucket_181_365", "bucket_366_720", "bucket_720_plus"
		];

		const colors = {
			"bucket_0_30":     "#fff9c4",
			"bucket_31_60":    "#ffe0b2",
			"bucket_61_90":    "#ffccbc",
			"bucket_91_120":   "#ffcdd2",
			"bucket_121_150":  "#ef9a9a",
			"bucket_151_180":  "#e57373",
			"bucket_181_365":  "#ef5350",
			"bucket_366_720":  "#e53935",
			"bucket_720_plus": "#b71c1c",
		};

		if (data && aging_buckets.includes(column.fieldname)) {
			const amt = data[column.fieldname];
			if (amt && amt !== 0) {
				const bg  = colors[column.fieldname];
				const txt = parseFloat(amt) > 100000 ? "white" : "#212121";
				value = `<span style="background:${bg};color:${txt};padding:2px 6px;border-radius:3px;font-weight:600;">${value}</span>`;
			}
		}

		if (column.fieldname === "grn_status" && data) {
			if (data.grn_status === "No Insp. Lot") {
				value = `<span style="color:#c62828;font-weight:600;">${value}</span>`;
			} else {
				value = `<span style="color:#2e7d32;font-weight:600;">${value}</span>`;
			}
		}

		if (column.fieldname === "due_days" && data) {
			if (data.due_days > 90) {
				value = `<span style="color:#c62828;font-weight:bold;">${value}</span>`;
			} else if (data.due_days > 30) {
				value = `<span style="color:#e65100;">${value}</span>`;
			}
		}

		return value;
	},
};