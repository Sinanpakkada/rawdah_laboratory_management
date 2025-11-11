from odoo import fields,models

class TestType(models.Model):
    _name = "test.type"
    _description = "Lab Test Type"
    _inherit = ['mail.thread','mail.activity.mixin']

    test_type_name=fields.Char(string="Test Name",required=True)
    parameter_ids= fields.One2many('test.parameter','test_type_id',string="Parameters")
    test_amount = fields.Float(string="Price",required=True)

