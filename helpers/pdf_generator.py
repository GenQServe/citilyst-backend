import os
import logging
from pathlib import Path
from jinja2 import FileSystemLoader, Environment, select_autoescape
from weasyprint import HTML
from schemas.reports import ReportGenerateRequest
from typing import Optional


async def generate_pdf_report(
    report_data: dict,
    template_name: str,
    output_file_path: str,
) -> Optional[str]:
    """
    Generate a PDF report using Jinja2 and WeasyPrint.
    """
    try:
        templates_path = Path(__file__).parent.parent / "templates"
        env = Environment(
            loader=FileSystemLoader(templates_path),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template(template_name)

        html_content = template.render(report_data=report_data)

        # Convert HTML to PDF
        HTML(string=html_content, base_url=str(templates_path)).write_pdf(
            output_file_path
        )

        if os.path.exists(output_file_path):
            logging.info(f"PDF report generated: {output_file_path}")
            return output_file_path
        else:
            logging.error("PDF generation failed, file not created.")
            return None

    except Exception as e:
        logging.error(f"Error generating PDF: {e}", exc_info=True)
        return None
