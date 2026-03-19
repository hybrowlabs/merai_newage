# Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, flt, today, date_diff


def execute(filters=None):
	if not filters:
		filters = {}
	if not filters.get("report_date"):
		filters["report_date"] = today()

	columns = get_columns()
	data    = get_data(filters)
	return columns, data


# ─────────────────────────────────────────────────────────────────────────────
# COLUMNS
# ─────────────────────────────────────────────────────────────────────────────
def get_columns():
	return [
		{"label": _("Vendor"),           "fieldname": "vendor",           "fieldtype": "Link",     "options": "Supplier", "width": 100},
		{"label": _("Vendor Name"),      "fieldname": "vendor_name",      "fieldtype": "Data",     "width": 200},
		{"label": _("Is MSME Registered"),      "fieldname": "is_msme",      "fieldtype": "Check",     "width": 200},

		{"label": _("City"),             "fieldname": "city",             "fieldtype": "Data",     "width": 100},
		{"label": _("State"),            "fieldname": "state",            "fieldtype": "Data",     "width": 120},
		{"label": _("Country"),          "fieldname": "country",          "fieldtype": "Data",     "width": 60},
		{"label": _("Document Number"),  "fieldname": "document_number",  "fieldtype": "Link",     "options": "Purchase Invoice", "width": 160},
		{"label": _("Invoice No"),       "fieldname": "invoice_no",       "fieldtype": "Data",     "width": 140},
		{"label": _("Document Date"),    "fieldname": "document_date",    "fieldtype": "Date",     "width": 110},
		{"label": _("Posting Date"),     "fieldname": "posting_date",     "fieldtype": "Date",     "width": 110},
		{"label": _("Due Date"),         "fieldname": "due_date",         "fieldtype": "Date",     "width": 110},
		{"label": _("Due Days"),         "fieldname": "due_days",         "fieldtype": "Int",      "width": 80},
		{"label": _("Payment Terms"),    "fieldname": "payment_terms",    "fieldtype": "Data",     "width": 110},
		{"label": _("Purchase Order"),   "fieldname": "purchase_order",   "fieldtype": "Link",     "options": "Purchase Order", "width": 150},
		{"label": _("Outstanding Amt"),  "fieldname": "outstanding_amount","fieldtype": "Currency", "width": 140},
		{"label": _("Due Amount"),       "fieldname": "due_amount",       "fieldtype": "Currency", "width": 130},
		{"label": _("Nondue Amount"),    "fieldname": "nondue_amount",    "fieldtype": "Currency", "width": 130},
		{"label": _("0-30"),             "fieldname": "bucket_0_30",      "fieldtype": "Currency", "width": 110},
		{"label": _("31-60"),            "fieldname": "bucket_31_60",     "fieldtype": "Currency", "width": 110},
		{"label": _("61-90"),            "fieldname": "bucket_61_90",     "fieldtype": "Currency", "width": 110},
		{"label": _("91-120"),           "fieldname": "bucket_91_120",    "fieldtype": "Currency", "width": 110},
		{"label": _("121-150"),          "fieldname": "bucket_121_150",   "fieldtype": "Currency", "width": 110},
		{"label": _("151-180"),          "fieldname": "bucket_151_180",   "fieldtype": "Currency", "width": 110},
		{"label": _("181-365"),          "fieldname": "bucket_181_365",   "fieldtype": "Currency", "width": 110},
		{"label": _("366-720"),          "fieldname": "bucket_366_720",   "fieldtype": "Currency", "width": 110},
		{"label": _(">720"),             "fieldname": "bucket_720_plus",  "fieldtype": "Currency", "width": 110},
		{"label": _("CGST"),             "fieldname": "cgst",             "fieldtype": "Currency", "width": 100},
		{"label": _("SGST"),             "fieldname": "sgst",             "fieldtype": "Currency", "width": 100},
		{"label": _("IGST"),             "fieldname": "igst",             "fieldtype": "Currency", "width": 100},
		{"label": _("PO Type"),          "fieldname": "po_type",          "fieldtype": "Data",     "width": 90},
		{"label": _("Item Code"),        "fieldname": "item_code",        "fieldtype": "Link",     "options": "Item", "width": 120},
		{"label": _("Item Type"),        "fieldname": "item_type",        "fieldtype": "Data",     "width": 120},
		{"label": _("Material Type"),    "fieldname": "material_type",    "fieldtype": "Data",     "width": 140},
		{"label": _("Item Description"), "fieldname": "item_description", "fieldtype": "Data",     "width": 200},
		{"label": _("Requestor"),        "fieldname": "requestor",        "fieldtype": "Data",     "width": 140},
		{"label": _("Requestor Email"),  "fieldname": "requestor_email",  "fieldtype": "Data",     "width": 180},
		{"label": _("Bank"),             "fieldname": "bank",             "fieldtype": "Data",     "width": 100},
		{"label": _("Bank Account No"),  "fieldname": "bank_account_no",  "fieldtype": "Data",     "width": 150},
		{"label": _("Name of Bank"),     "fieldname": "name_of_bank",     "fieldtype": "Data",     "width": 180},
		{"label": _("GRN Status"),       "fieldname": "grn_status",       "fieldtype": "Data",     "width": 120},
	]


# ─────────────────────────────────────────────────────────────────────────────
# MAIN DATA
# ─────────────────────────────────────────────────────────────────────────────
def get_data(filters):
	report_date = getdate(filters.get("report_date") or today())
	ageing_on   = filters.get("ageing_based_on", "Due Date")
	company     = filters.get("company")

	conditions = ["pi.company = %(company)s", "pi.docstatus = 1", "pi.outstanding_amount != 0"]
	params     = {"company": company}

	if filters.get("from_date"):
		conditions.append("pi.posting_date >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("pi.posting_date <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("supplier"):
		conditions.append("pi.supplier = %(supplier)s")
		params["supplier"] = filters["supplier"]

	where = " AND ".join(conditions)

	invoices = frappe.db.sql(f"""
		SELECT
			pi.name                   AS document_number,
			pi.supplier               AS vendor,
			pi.supplier_name          AS vendor_name,
			pi.custom_is_msme	      AS is_msme,
			pi.bill_no                AS invoice_no,
			pi.bill_date              AS document_date,
			pi.posting_date,
			pi.due_date,
			pi.outstanding_amount,
			pi.currency,
			pi.conversion_rate,
			pi.payment_terms_template AS payment_terms,
			pi.custom_po_type         AS po_type
		FROM `tabPurchase Invoice` pi
		WHERE {where}
		ORDER BY pi.supplier, pi.posting_date
	""", params, as_dict=True)

	if not invoices:
		return []

	inv_names = [i.document_number for i in invoices]
	suppliers = list(set(i.vendor for i in invoices))

	addr_map = get_supplier_address(suppliers)
	po_map   = get_po_details(inv_names)
	item_map = get_item_details(inv_names)
	gst_map  = get_gst_details(inv_names)
	bank_map = get_bank_details(suppliers)
	grn_map  = get_grn_status(inv_names)

	data = []
	for inv in invoices:
		outstanding = flt(inv.outstanding_amount)

		if ageing_on == "Due Date":
			age_date = inv.due_date or inv.posting_date
		elif ageing_on == "Posting Date":
			age_date = inv.posting_date
		else:
			age_date = inv.document_date or inv.posting_date

		overdue_days = date_diff(report_date, getdate(age_date)) if age_date else 0
		buckets      = assign_buckets(outstanding, overdue_days)

		addr = addr_map.get(inv.vendor, {})
		po   = po_map.get(inv.document_number, {})
		itm  = item_map.get(inv.document_number, {})
		gst  = gst_map.get(inv.document_number, {})
		bk   = bank_map.get(inv.vendor, {})
		grn  = grn_map.get(inv.document_number, "No Insp. Lot")

		row = {
			"vendor":             inv.vendor,
			"vendor_name":        inv.vendor_name,
			"city":               addr.get("city", ""),
			"state":              addr.get("state", ""),
			"country":            addr.get("country", "IN"),
			"document_number":    inv.document_number,
			"invoice_no":         inv.invoice_no or "",
			"document_date":      inv.document_date,
			"posting_date":       inv.posting_date,
			"due_date":           inv.due_date,
			"due_days":           overdue_days,
			"payment_terms":      inv.payment_terms or "",
			"purchase_order":     po.get("purchase_order", ""),
			"outstanding_amount": outstanding,
			"due_amount":         outstanding if overdue_days > 0 else 0.0,
			"nondue_amount":      outstanding if overdue_days <= 0 else 0.0,
			**buckets,
			"cgst":               gst.get("cgst", 0.0),
			"sgst":               gst.get("sgst", 0.0),
			"igst":               gst.get("igst", 0.0),
			"po_type":            inv.po_type or po.get("po_type", ""),
			"item_code":          itm.get("item_code", ""),
			"item_type":          itm.get("item_type", ""),
			"material_type":      itm.get("material_type", ""),
			"item_description":   itm.get("description", ""),
			"requestor":          po.get("requestor", ""),
			"requestor_email":    po.get("requestor_email", ""),
			"bank":               bk.get("bank", ""),
			"bank_account_no":    bk.get("bank_account_no", ""),
			"name_of_bank":       bk.get("name_of_bank", ""),
			"grn_status":         grn,
		}
		data.append(row)

	return data


# ─────────────────────────────────────────────────────────────────────────────
# AGING BUCKETS
# ─────────────────────────────────────────────────────────────────────────────
def assign_buckets(outstanding, days):
	b = {k: 0.0 for k in ["bucket_0_30","bucket_31_60","bucket_61_90",
	                        "bucket_91_120","bucket_121_150","bucket_151_180",
	                        "bucket_181_365","bucket_366_720","bucket_720_plus"]}
	if days <= 0:
		return b
	if   days <= 30:  b["bucket_0_30"]     = outstanding
	elif days <= 60:  b["bucket_31_60"]    = outstanding
	elif days <= 90:  b["bucket_61_90"]    = outstanding
	elif days <= 120: b["bucket_91_120"]   = outstanding
	elif days <= 150: b["bucket_121_150"]  = outstanding
	elif days <= 180: b["bucket_151_180"]  = outstanding
	elif days <= 365: b["bucket_181_365"]  = outstanding
	elif days <= 720: b["bucket_366_720"]  = outstanding
	else:             b["bucket_720_plus"] = outstanding
	return b


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: City / State from Supplier Address
# ─────────────────────────────────────────────────────────────────────────────
def get_supplier_address(suppliers):
	if not suppliers:
		return {}

	rows = frappe.db.sql("""
		SELECT
			dl.link_name  AS supplier,
			addr.city,
			addr.state,
			addr.country
		FROM `tabAddress` addr
		JOIN `tabDynamic Link` dl
		  ON dl.parent = addr.name
		 AND dl.link_doctype = 'Supplier'
		 AND dl.link_name IN %(suppliers)s
		WHERE addr.is_primary_address = 1
		  AND addr.disabled = 0
	""", {"suppliers": suppliers}, as_dict=True)

	addr_map = {}
	for r in rows:
		if r.supplier not in addr_map:
			addr_map[r.supplier] = r
	return addr_map


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: PO details
# FIX: Removed direct join on po.material_request (column may not exist on PO header).
#      Material Request is fetched via Purchase Order Item child table instead.
# ─────────────────────────────────────────────────────────────────────────────
def get_po_details(invoice_names):
	if not invoice_names:
		return {}

	# Step 1: get PO + custom fields from PO header
	rows = frappe.db.sql("""
		SELECT
			pii.parent                    AS invoice,
			pii.purchase_order,
			po.custom_purchase_type       AS po_type,
			po.custom_requisitioner       AS po_requestor,
			po.custom_requisitioner_email AS po_requestor_email
		FROM `tabPurchase Invoice Item` pii
		LEFT JOIN `tabPurchase Order` po
		  ON po.name = pii.purchase_order
		WHERE pii.parent IN %(invoices)s
		  AND pii.purchase_order IS NOT NULL
		  AND pii.purchase_order != ''
		GROUP BY pii.parent
	""", {"invoices": invoice_names}, as_dict=True)

	po_map   = {}
	po_names = []

	for r in rows:
		po_map[r.invoice] = {
			"purchase_order":  r.purchase_order or "",
			"po_type":         r.po_type or "",
			"requestor":       r.po_requestor or "",
			"requestor_email": r.po_requestor_email or "",
		}
		if r.purchase_order:
			po_names.append(r.purchase_order)

	# Step 2: fallback requestor via PO Item → material_request column on child row
	if po_names:
		poi_rows = frappe.db.sql("""
			SELECT
				poi.parent           AS po_name,
				poi.material_request AS mr_name
			FROM `tabPurchase Order Item` poi
			WHERE poi.parent IN %(po_names)s
			  AND poi.material_request IS NOT NULL
			  AND poi.material_request != ''
			GROUP BY poi.parent
		""", {"po_names": po_names}, as_dict=True)

		po_to_mr = {r.po_name: r.mr_name for r in poi_rows}

		mr_names = list(set(po_to_mr.values()))
		if mr_names:
			mr_rows = frappe.db.sql("""
				SELECT
					name                    AS mr_name,
					custom_requisitioner    AS requisitioner
				FROM `tabMaterial Request`
				WHERE name IN %(mr_names)s
			""", {"mr_names": mr_names}, as_dict=True)

			mr_req_map = {r.mr_name: r.requisitioner for r in mr_rows}

			# Fill back where requestor is missing
			for inv, pd in po_map.items():
				if not pd["requestor"]:
					mr = po_to_mr.get(pd["purchase_order"])
					if mr:
						pd["requestor"] = mr_req_map.get(mr, "")

	return po_map


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Item details — item_type from Item master, item_group as material_type
# ─────────────────────────────────────────────────────────────────────────────
def get_item_details(invoice_names):
	if not invoice_names:
		return {}

	rows = frappe.db.sql("""
		SELECT
			pii.parent      AS invoice,
			pii.item_code,
			pii.description AS description,
			itm.item_group  AS material_type,
			itm.custom_material_type   AS item_type
		FROM `tabPurchase Invoice Item` pii
		LEFT JOIN `tabItem` itm ON itm.name = pii.item_code
		WHERE pii.parent IN %(invoices)s
		GROUP BY pii.parent
	""", {"invoices": invoice_names}, as_dict=True)

	return {r.invoice: r for r in rows}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: GST from tax lines
# ─────────────────────────────────────────────────────────────────────────────
def get_gst_details(invoice_names):
	if not invoice_names:
		return {}

	rows = frappe.db.sql("""
		SELECT
			parent,
			account_head,
			SUM(base_tax_amount_after_discount_amount) AS tax_amount
		FROM `tabPurchase Taxes and Charges`
		WHERE parent IN %(invoices)s
		GROUP BY parent, account_head
	""", {"invoices": invoice_names}, as_dict=True)

	gst_map = {}
	for r in rows:
		g = gst_map.setdefault(r.parent, {"cgst": 0.0, "sgst": 0.0, "igst": 0.0})
		head = (r.account_head or "").upper()
		if "CGST" in head:
			g["cgst"] += flt(r.tax_amount)
		elif "SGST" in head:
			g["sgst"] += flt(r.tax_amount)
		elif "IGST" in head:
			g["igst"] += flt(r.tax_amount)
	return gst_map


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Bank Account — standard fields only
# ─────────────────────────────────────────────────────────────────────────────
def get_bank_details(suppliers):
	if not suppliers:
		return {}

	rows = frappe.db.sql("""
		SELECT
			ba.party         AS supplier,
			ba.bank          AS bank,
			ba.bank_account_no,
			b.name           AS name_of_bank
		FROM `tabBank Account` ba
		LEFT JOIN `tabBank` b ON b.name = ba.bank
		WHERE ba.party_type = 'Supplier'
		  AND ba.party IN %(suppliers)s
	""", {"suppliers": suppliers}, as_dict=True)

	bank_map = {}
	for r in rows:
		if r.supplier not in bank_map:
			bank_map[r.supplier] = r
	return bank_map


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: GRN Status from Purchase Receipt
# ─────────────────────────────────────────────────────────────────────────────
def get_grn_status(invoice_names):
	if not invoice_names:
		return {}

	rows = frappe.db.sql("""
		SELECT
			pri.purchase_invoice AS invoice,
			pr.status
		FROM `tabPurchase Receipt Item` pri
		JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
		WHERE pri.purchase_invoice IN %(invoices)s
		  AND pr.docstatus = 1
		GROUP BY pri.purchase_invoice
	""", {"invoices": invoice_names}, as_dict=True)

	grn_map = {r.invoice: r.status or "GRN Created" for r in rows}

	for inv in invoice_names:
		grn_map.setdefault(inv, "No Insp. Lot")

	return grn_map