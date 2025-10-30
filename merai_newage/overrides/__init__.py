def apply_all_overrides():
    _apply_job_card_overrides()


def apply_job_card_overrides(doc, method=None):
    _apply_job_card_overrides()


def _apply_job_card_overrides():
    import frappe

    if "erpnext" not in frappe.get_installed_apps():
        return

    try:
        from erpnext.manufacturing.doctype.job_card.job_card import JobCard
        from merai_newage.overrides.job_card import custom_get_time_logs

        JobCard.get_time_logs = custom_get_time_logs
    except ImportError:
        pass
