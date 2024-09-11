from odoo import models, fields, api

class ClientInfo(models.Model):
    _name = 'chatbot.client.info'
    _description = 'Client Information for Chatbot'

    name = fields.Char(string='Full Name', required=True)
    phone = fields.Char(string='Phone Number', required=True)
    age = fields.Integer(string='Age')
    condition = fields.Text(string='Medical Condition')
    is_new_patient = fields.Boolean(string='Is New Patient')
    last_interaction = fields.Datetime(string='Last Interaction')
    chat_history = fields.Text(string='Chat History')