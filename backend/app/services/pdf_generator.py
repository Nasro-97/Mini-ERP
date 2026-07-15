from fastapi import HTTPException, status
from jinja2 import Environment, BaseLoader


def render_template(html_template: str, context: dict) -> str:
    if not html_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF template is empty.",
        )

    try:
        env = Environment(loader=BaseLoader())
        template = env.from_string(html_template)
        return template.render(**context)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template rendering failed: {str(e)}",
        )


def html_to_pdf(html: str) -> bytes:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")

            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                margin={
                    "top": "20mm",
                    "right": "20mm",
                    "bottom": "20mm",
                    "left": "20mm",
                },
            )

            browser.close()
            return pdf_bytes

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(e)}",
        )