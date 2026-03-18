import frappe
import os
import requests
import json
import re
import time
from datetime import datetime

def refresh_ocr_token():
	"""
	Login to OCR API and refresh the token in site_config
	Works for both local and Frappe Cloud (credentials from site_config)
	"""
	try:
		login_url = "http://10.10.3.205:5001/login"

		# Get credentials from site_config (works for both local and Frappe Cloud)
		#email = frappe.get_site_config().get("ocr_login_email")
		#password = frappe.get_site_config().get("ocr_login_password")
		email ="pranav@mail.hybrowlabs.com"
		password = "Pranav@99"

		if not email or not password:
			error_msg = "OCR login credentials not configured in site_config. Please add ocr_login_email and ocr_login_password"
			frappe.log_error(error_msg, "OCR Token Refresh Failed")
			return {"status": "error", "message": error_msg}

		# Make login request
		payload = {
			"email": email,
			"password": password
		}

		response = requests.post(login_url, json=payload, timeout=30)
		response.raise_for_status()

		response_data = response.json()

		# Extract token from response (API returns 'token' field)
		token = response_data.get("token") or response_data.get("access_token")
		if not token:
			frappe.log_error("No token in login response", "OCR Token Refresh Failed")
			return {"status": "error", "message": "No token in login response"}

		# Store token in OCR Settings (persists in database, works on Frappe Cloud)
		if not frappe.db.exists("OCR Settings", "OCR Settings"):
			ocr_settings = frappe.new_doc("OCR Settings")
			ocr_settings.name = "OCR Settings"
		else:
			ocr_settings = frappe.get_doc("OCR Settings", "OCR Settings")

		ocr_settings.api_token = token
		ocr_settings.last_token_refresh = datetime.now()
		ocr_settings.save(ignore_permissions=True)
		frappe.db.commit()

		frappe.logger().info(f"OCR token refreshed successfully at {datetime.now()}")
		return {"status": "success", "message": "Token refreshed successfully", "token": token}

	except requests.exceptions.RequestException as e:
		frappe.log_error(f"OCR login request failed: {str(e)}", "OCR Token Refresh Failed")
		return {"status": "error", "message": f"Login request failed: {str(e)}"}
	except Exception as e:
		frappe.log_error(f"OCR token refresh failed: {str(e)}", "OCR Token Refresh Failed")
		return {"status": "error", "message": f"Token refresh failed: {str(e)}"}

@frappe.whitelist(allow_guest=True)
def check_api_status():
	"""
	Check if the OCR API server is available
	"""
	external_api_url = "http://10.10.3.205:5001/health"
	try:
		response = requests.get(external_api_url, timeout=5)
		response.raise_for_status()
		return {"status": "up", "message": "OCR API server is available"}
	except requests.exceptions.RequestException:
		return {"status": "down", "message": "OCR API server is currently unavailable. Please try again later or contact support (Vipul Ramani)."}

@frappe.whitelist(allow_guest=True)
def get_document_data(docname):
	"""
	Fetch the latest document data for polling
	"""
	try:
		if not frappe.db.exists("Supplier Invoice", docname):
			return {"status": "error", "message": f"Document {docname} not found"}

		doc = frappe.get_doc("Supplier Invoice", docname)
		data = {
			"invoice_no": doc.invoice_no,
			"invoice_date": doc.invoice_date,
			"amount": doc.amount,
		}
		return {"status": "success", "data": data}
	except Exception as e:
		return {"status": "error", "message": f"Failed to fetch document data: {str(e)}"}

@frappe.whitelist(allow_guest=True)
def send_file_to_external_api(docname):
	
	"""
	Sends uploaded file to external OCR API and updates the Supplier Invoice.
	"""
	try:
		if not frappe.db.exists("Supplier Invoice", docname):
			return {"status": "error", "message": f"Document {docname} not found"}

		# Check API status
		api_status = check_api_status()
		if api_status["status"] == "down":
			return {"status": "error", "message": api_status["message"]}

		doc = frappe.get_doc("Supplier Invoice", docname)
		if not doc.upload_file:
			return {"status": "error", "message": "No file uploaded"}

		file_doc = frappe.get_doc("File", {"file_url": doc.upload_file})
		file_path = file_doc.get_full_path()
		if not os.path.exists(file_path):
			return {"status": "error", "message": f"File not found: {file_path}"}

		with open(file_path, "rb") as f:
			f.read(1)  # Verify file is readable

		filename = os.path.basename(file_path)
		external_api_url = "http://10.10.3.205:5001/upload"

		# Get token from OCR Settings (database, works on Frappe Cloud)
		if frappe.db.exists("OCR Settings", "OCR Settings"):
			ocr_settings = frappe.get_doc("OCR Settings", "OCR Settings")
			api_key = ocr_settings.get_password("api_token") if ocr_settings.api_token else None
		else:
			api_key = None

		# If token is not available, try to refresh it automatically
		if not api_key:
			frappe.logger().info("OCR token not found, attempting automatic refresh...")
			refresh_result = refresh_ocr_token()
			if refresh_result.get("status") == "success":
				ocr_settings = frappe.get_doc("OCR Settings", "OCR Settings")
				api_key = ocr_settings.get_password("api_token")
			else:
				return {"status": "error", "message": f"OCR API token not configured. Auto-refresh failed: {refresh_result.get('message')}"}

		headers = {
			"Authorization": f"Bearer {api_key}",
			"User-Agent": "Frappe/1.0"
		}

		frappe.logger().info(f"OCR: Sending file {filename} to OCR API for {docname}")

		# First attempt with existing token
		with open(file_path, "rb") as f:
			files = {"file": (filename, f, "application/pdf")}
			response = requests.post(external_api_url, files=files, headers=headers, timeout=120)

		frappe.logger().info(f"OCR: Response status code: {response.status_code}")

		# If token expired (401 Unauthorized), refresh token and retry
		if response.status_code == 401:
			frappe.logger().info("OCR token expired, refreshing token...")
			refresh_result = refresh_ocr_token()

			if refresh_result.get("status") == "success":
				# Retry with new token from OCR Settings
				ocr_settings = frappe.get_doc("OCR Settings", "OCR Settings")
				new_api_key = ocr_settings.get_password("api_token")
				headers["Authorization"] = f"Bearer {new_api_key}"

				# Reopen file completely for retry (file was consumed in first attempt)
				with open(file_path, "rb") as f:
					files = {"file": (filename, f, "application/pdf")}
					response = requests.post(external_api_url, files=files, headers=headers, timeout=120)
				response.raise_for_status()
			else:
				return {"status": "error", "message": f"Token refresh failed: {refresh_result.get('message')}"}
		else:
			response.raise_for_status()

		content_type = response.headers.get("content-type", "")
		if not content_type.startswith("application/json"):
			frappe.logger().error(f"OCR: Non-JSON response. Content-Type: {content_type}, Body: {response.text[:500]}")
			return {"status": "error", "message": f"Non-JSON response: {content_type}"}

		extracted_json = response.json()
		frappe.logger().info(f"OCR: Received response with {len(extracted_json.get('result', []))} pages")

		# API returns data in 'result' array, with actual data in 'data' key
		if not extracted_json.get("result"):
			frappe.logger().error(f"OCR: Empty result. Full response: {extracted_json}")
			return {"status": "error", "message": f"OCR API returned empty 'result'. Full response: {extracted_json}"}

		# For multi-page PDFs, find the page with the most complete data
		extracted_data = get_best_page_data(extracted_json["result"])
		if not extracted_data:
			frappe.logger().error(f"OCR: get_best_page_data returned empty. Pages: {extracted_json['result']}")
			return {"status": "error", "message": "OCR API returned empty data"}

		frappe.logger().info(f"OCR: Selected data for {docname}: {extracted_data}")
		result = set_extracted_json_internal(docname, extracted_data)
		return result

	except requests.exceptions.RequestException as e:
		frappe.log_error(f"OCR request failed for {docname}: {str(e)}", "OCR Processing Failed")
		return {"status": "error", "message": f"OCR request failed: {str(e)}"}
	except Exception as e:
		frappe.log_error(f"OCR Processing failed for {docname}: {str(e)}", "OCR Processing Failed")
		return {"status": "error", "message": f"OCR Processing failed: {str(e)}"}

def parse_amount(value):
	"""
	Parse amount string to float, handling both American and European number formats.
	American: 1,234.56 (comma as thousands, dot as decimal)
	European: 1.234,56 (dot as thousands, comma as decimal)
	Returns None if parsing fails.
	"""
	if not value or value in ["", "Not clearly visible", "N/A", "NA"]:
		return None
	try:
		str_value = str(value).strip()

		# Check if it's European format (comma as decimal separator)
		# European format: comma followed by 1-2 digits at the end, e.g., "1032,87" or "1.234,56"
		european_pattern = re.match(r'^[\d.]+,(\d{1,2})$', str_value)

		if european_pattern:
			# European format: replace dots (thousands) with nothing, comma (decimal) with dot
			clean_value = str_value.replace(".", "").replace(",", ".")
		else:
			# American format: remove commas (thousands separator)
			clean_value = str_value.replace(",", "")

		return float(clean_value)
	except (ValueError, TypeError):
		return None

def get_best_page_data(result_pages):
	"""
	For multi-page PDFs, select the page with the highest amount (total/final amount).
	This handles invoices where the last page contains the summary/total.
	Falls back to page with most complete data if no valid amounts found.
	"""
	if not result_pages:
		frappe.logger().warning("OCR: No result pages received")
		return {}

	# Invalid values to skip
	invalid_values = ["", "Not clearly visible", "N/A", "NA", "null", "None"]

	# First, collect all valid pages (pages with "data" key and no errors)
	valid_pages = []
	for page in result_pages:
		page_num = page.get("Page", 0)

		# Skip pages with errors
		if page.get("error"):
			frappe.logger().info(f"OCR: Skipping Page {page_num} - has error: {page.get('error')}")
			continue

		data = page.get("data")
		if not data or not isinstance(data, dict):
			frappe.logger().info(f"OCR: Skipping Page {page_num} - no valid data")
			continue

		valid_pages.append({"page_num": page_num, "data": data})
		frappe.logger().info(f"OCR: Page {page_num} has valid data: invoice_no={data.get('invoice_no')}, invoice_date={data.get('invoice_date')}, amount={data.get('amount')}")

	if not valid_pages:
		frappe.logger().error("OCR: No valid pages found in result")
		return {}

	# First strategy: Find the page with the maximum amount (likely the total/summary page)
	best_page_by_amount = None
	max_amount = -1
	selected_page_num = 0

	for page_info in valid_pages:
		data = page_info["data"]
		page_num = page_info["page_num"]

		# Check amount field (prefer amount over basic_amount for domestic invoices)
		amount = parse_amount(data.get("amount")) or parse_amount(data.get("basic_amount"))

		if amount is not None and amount > max_amount:
			# Verify this page has valid essential fields (invoice_no, invoice_date)
			invoice_no = data.get("invoice_no", "")
			invoice_date = data.get("invoice_date", "")

			# Only consider pages with at least invoice_no or invoice_date
			if (invoice_no and invoice_no not in invalid_values) or \
			   (invoice_date and invoice_date not in invalid_values):
				max_amount = amount
				best_page_by_amount = data
				selected_page_num = page_num

	# If we found a valid page with maximum amount, return it
	if best_page_by_amount:
		frappe.logger().info(f"OCR: Selected Page {selected_page_num} (max amount={max_amount})")
		return best_page_by_amount

	# Fallback strategy: Find page with most complete data
	important_fields = ["invoice_no", "invoice_date", "amount", "basic_amount", "tax_amount"]
	best_page = None
	best_score = -1
	best_page_num = 0

	for page_info in valid_pages:
		data = page_info["data"]
		page_num = page_info["page_num"]

		score = 0
		for field in important_fields:
			value = data.get(field, "")
			if value and value not in invalid_values:
				score += 1

		if score > best_score:
			best_score = score
			best_page = data
			best_page_num = page_num

	if best_page:
		frappe.logger().info(f"OCR: Fallback - Selected Page {best_page_num} (score={best_score})")
		return best_page

	# Last resort: return first valid page's data
	frappe.logger().warning(f"OCR: Using first valid page as last resort")
	return valid_pages[0]["data"] if valid_pages else {}

def convert_date_format(date_str):
	"""
	Converts various date formats to datetime.date object.
	Supports multiple Indian and international date formats including:
	- DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY (4-digit year)
	- D/M/YY, DD/MM/YY (2-digit year)
	- DD-Mon-YYYY, D-Mon-YY (month as text like Nov, Jan)
	- YYYY-MM-DD, YYYY/MM/DD (ISO format)
	- Date with time: "26-Nov-2025 10:14 AM" (time will be stripped)
	"""
	if not date_str:
		return None

	# Clean the date string
	date_str = str(date_str).strip()

	# Remove time component if present (e.g., "26-Nov-2025 10:14 AM" -> "26-Nov-2025")
	# Pattern: date followed by time like "HH:MM" or "HH:MM:SS" with optional AM/PM
	time_patterns = [
		r'\s+\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM|am|pm)?',  # 10:14 AM, 10:14:30 PM
		r'\s+\d{1,2}\.\d{2}(.\d{2})?\s*(AM|PM|am|pm)?',  # 10.14 AM
	]
	for pattern in time_patterns:
		date_str = re.sub(pattern, '', date_str).strip()

	# Date formats to try (order matters - more specific first)
	date_formats = [
		# 4-digit year formats with month name
		"%d-%b-%Y",  # 20-Nov-2025
		"%d/%b/%Y",  # 20/Nov/2025
		"%d %b %Y",  # 20 Nov 2025
		"%d-%B-%Y",  # 20-November-2025
		"%d/%B/%Y",  # 20/November/2025
		"%d %B %Y",  # 20 November 2025
		# 4-digit year numeric formats
		"%d.%m.%Y",  # 01.11.2025
		"%d/%m/%Y",  # 03/09/2025
		"%d-%m-%Y",  # 03-09-2025
		"%Y-%m-%d",  # 2025-09-03
		"%Y/%m/%d",  # 2025/09/03
		# 2-digit year formats (Indian domestic invoices)
		"%d-%b-%y",  # 20-Nov-25
		"%d/%b/%y",  # 20/Nov/25
		"%d %b %y",  # 20 Nov 25
		"%d/%m/%y",  # 5/10/25, 30/9/25
		"%d-%m-%y",  # 5-10-25
		"%d.%m.%y",  # 5.10.25
	]

	for date_format in date_formats:
		try:
			return datetime.strptime(date_str, date_format).date()
		except ValueError:
			continue

	# Log if date couldn't be parsed
	frappe.logger().warning(f"Could not parse date: {date_str}")

	return None

def set_extracted_json_internal(docname, data):
	"""
	Update document with extracted OCR data
	"""
	try:
		if not frappe.db.exists("Supplier Invoice", docname):
			return {"status": "error", "message": f"Document {docname} not found"}

		# Invalid values to skip
		invalid_values = ["", "Not clearly visible", "N/A", "NA", "null", "None", None]

		meta = frappe.get_meta("Supplier Invoice")

		# Parse invoice_date
		date_updates = {}
		raw_date = data.get("invoice_date")
		if raw_date and raw_date not in invalid_values:
			converted_date = convert_date_format(raw_date)
			if converted_date:
				date_updates["invoice_date"] = converted_date

		field_mapping = {
			"invoice_no": "invoice_no",
			"invoice_date": "invoice_date",
			"amount": "amount",
		}

		updates = {}
		for api_field, doctype_field in field_mapping.items():
			raw_value = data.get(api_field)

			# Skip invalid/empty values
			if raw_value is None or raw_value in invalid_values:
				continue

			if not meta.has_field(doctype_field):
				continue

			if api_field == "invoice_date":
				if api_field in date_updates:
					updates[doctype_field] = date_updates[api_field]
			elif api_field == "amount":
				parsed_value = parse_amount(raw_value)
				if parsed_value is not None:
					updates[doctype_field] = parsed_value
			else:
				updates[doctype_field] = str(raw_value).strip()

		# Log what we're updating for debugging
		frappe.logger().info(f"OCR Update for {docname}: {updates}")

		if updates:
			doc = frappe.get_doc("Supplier Invoice", docname)
			for field, value in updates.items():
				doc.set(field, value)
			doc.save(ignore_permissions=True)
			frappe.db.commit()

		return {"status": "success", "message": f"Document {docname} updated successfully", "updates": updates}

	except Exception as e:
		return {"status": "error", "message": f"Failed to update document: {str(e)}"}

@frappe.whitelist()
def bulk_send_files_to_ocr(docnames):
	"""
	Process multiple Supplier Invoices through OCR asynchronously using background jobs.
	Args:
		docnames: JSON string of document names to process
	Returns:
		Status message with job information
	"""
	if isinstance(docnames, str):
		docnames = json.loads(docnames)

	if not docnames:
		return {"status": "error", "message": "No documents selected"}

	# Validate all documents exist and have files
	valid_docs = []
	errors = []

	for docname in docnames:
		if not frappe.db.exists("Supplier Invoice", docname):
			errors.append(f"{docname}: Document not found")
			continue

		doc = frappe.get_doc("Supplier Invoice", docname)
		if not doc.upload_file:
			errors.append(f"{docname}: No file uploaded")
			continue

		if doc.workflow_state != "Open":
			errors.append(f"{docname}: Not in Open state")
			continue

		valid_docs.append(docname)

	if not valid_docs:
		return {
			"status": "error",
			"message": "No valid documents to process",
			"errors": errors
		}

	# Check API status before starting
	api_status = check_api_status()
	if api_status["status"] == "down":
		return {"status": "error", "message": api_status["message"]}

	# Create Bulk OCR Log entry
	ocr_log = frappe.new_doc("Bulk OCR Log")
	ocr_log.status = "Processing"
	ocr_log.started_by = frappe.session.user
	ocr_log.started_at = datetime.now()
	ocr_log.total_invoices = len(valid_docs)
	ocr_log.success_count = 0
	ocr_log.failed_count = 0
	ocr_log.insert(ignore_permissions=True)
	frappe.db.commit()

	# Enqueue background job for processing
	frappe.enqueue(
		"purchase_booking.api.purchase_booking_request_api.process_bulk_ocr",
		queue="long",
		timeout=1800,  # 30 minutes timeout
		docnames=valid_docs,
		user=frappe.session.user,
		log_name=ocr_log.name
	)

	return {
		"status": "success",
		"message": f"OCR processing started for {len(valid_docs)} document(s)",
		"valid_count": len(valid_docs),
		"error_count": len(errors),
		"errors": errors if errors else None,
		"log_name": ocr_log.name
	}

def process_bulk_ocr(docnames, user, log_name=None):
	"""
	Background job to process multiple documents through OCR sequentially.
	Each document is processed one at a time to avoid overwhelming the OCR server.
	"""
	frappe.set_user(user)

	results = {
		"success": [],
		"failed": []
	}

	total = len(docnames)

	for idx, docname in enumerate(docnames, 1):
		try:
			frappe.publish_realtime(
				"bulk_ocr_progress",
				{
					"current": idx,
					"total": total,
					"docname": docname,
					"status": "processing",
					"log_name": log_name
				},
				user=user
			)

			# Call the existing OCR function
			result = send_file_to_external_api(docname)

			if result.get("status") == "success":
				results["success"].append(docname)
			else:
				results["failed"].append({
					"docname": docname,
					"error": result.get("message", "Unknown error")
				})

			# Add delay between requests to prevent overwhelming OCR server
			# This makes bulk behave more like single requests
			if idx < total:
				time.sleep(2)

		except Exception as e:
			results["failed"].append({
				"docname": docname,
				"error": str(e)
			})

	# Update Bulk OCR Log with results
	if log_name and frappe.db.exists("Bulk OCR Log", log_name):
		ocr_log = frappe.get_doc("Bulk OCR Log", log_name)
		ocr_log.status = "Completed" if not results["failed"] else "Completed with Errors"
		ocr_log.completed_at = datetime.now()
		ocr_log.success_count = len(results["success"])
		ocr_log.failed_count = len(results["failed"])
		ocr_log.success_invoices = "\n".join(results["success"]) if results["success"] else ""
		ocr_log.failed_invoices = "\n".join([f"{item['docname']}: {item['error']}" for item in results["failed"]]) if results["failed"] else ""
		ocr_log.details = json.dumps(results, indent=2)
		ocr_log.save(ignore_permissions=True)
		frappe.db.commit()

	# Send completion notification
	frappe.publish_realtime(
		"bulk_ocr_complete",
		{
			"success_count": len(results["success"]),
			"failed_count": len(results["failed"]),
			"success": results["success"],
			"failed": results["failed"],
			"log_name": log_name
		},
		user=user
	)

	# Log the results
	frappe.logger().info(f"Bulk OCR completed: {len(results['success'])} success, {len(results['failed'])} failed")

	
