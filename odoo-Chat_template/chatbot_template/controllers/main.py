from odoo import http
from odoo.http import request

class WhatsAppChatbotController(http.Controller):

    @http.route('/whatsapp', type='http', auth="public", methods=['POST'], csrf=False)
    def handle_whatsapp(self):
        company = request.env.user.company_id
        return company.whatsapp_reply()

