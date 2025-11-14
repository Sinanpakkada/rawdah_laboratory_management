from odoo import models,fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_patient = fields.Boolean(string="Is a Patient")
    age = fields.Integer(string="Age")
    gender = fields.Selection([('male','Male'),('female','Female'),],string="Gender")