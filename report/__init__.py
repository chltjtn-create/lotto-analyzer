"""Reporting package for chart and Excel exports."""

from lotto_analyzer.report.chart import ChartExportError, export_all_charts
from lotto_analyzer.report.email_html import build_weekly_email_html
from lotto_analyzer.report.excel_export import ExcelExportError, export_excel_report

__all__ = [
    "ChartExportError",
    "ExcelExportError",
    "build_weekly_email_html",
    "export_all_charts",
    "export_excel_report",
]
