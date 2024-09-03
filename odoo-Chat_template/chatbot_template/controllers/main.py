from odoo import http
from odoo.http import request

class WhatsAppChatbotController(http.Controller):

    @http.route('/whatsapp', type='http', auth="public", methods=['POST'], csrf=False)
    def handle_whatsapp(self, **kwargs):
        company = request.env.user.company_id
        incoming_msg = kwargs.get('Body', '').strip()
        user_number = kwargs.get('From', '').strip()
        return company.whatsapp_reply(incoming_msg, user_number)

