from odoo import fields, models
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client
except ImportError:
    _logger.error('Cannot import Twilio dependencies', exc_info=True)

class ResCompany(models.Model):
    _inherit = 'res.company'

    twilio_account_sid = fields.Char(string="Twilio Account SID", required=True)
    twilio_auth_token = fields.Char(string="Twilio Auth Token", required=True)
    twilio_whatsapp_number = fields.Char(string="Twilio WhatsApp Number", required=True)

    def test_twilio_connection(self):
        for company in self:
            if not company.twilio_account_sid or not company.twilio_auth_token:
                raise UserError("Please configure Twilio SID and Auth Token.")
            try:
                client = Client(company.twilio_account_sid, company.twilio_auth_token)
                client.api.accounts(company.twilio_account_sid).fetch()
                _logger.info("Twilio connection successful for SID: %s", company.twilio_account_sid)
                return True
            except Exception as e:
                _logger.error("Twilio connection failed: %s", str(e))
                raise UserError("Twilio connection failed: %s" % str(e))

