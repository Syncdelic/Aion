from odoo import fields, models
import logging
from openai import OpenAI
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    openai_api_key = fields.Char(string="OpenAI API Key", required=True)

    def test_openai_connection(self):
        for company in self:
            if not company.openai_api_key:
                raise UserError("Please configure OpenAI API Key.")
            try:
                # Initialize OpenAI client with the company-specific API key
                client = OpenAI(api_key=company.openai_api_key)

                # Make a test request to the OpenAI chat completions endpoint
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hello, OpenAI!"}
                    ],
                    max_tokens=50
                )

                # Access the response content correctly
                response_content = response.choices[0].message.content.strip()

                _logger.info("OpenAI connection successful, response: %s", response_content)
                return True
            except Exception as e:
                _logger.error("OpenAI connection failed: %s", str(e))
                raise UserError("OpenAI connection failed: %s" % str(e))

