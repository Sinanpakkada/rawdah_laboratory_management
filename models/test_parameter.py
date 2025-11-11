from odoo import models,fields

class TestParameter(models.Model):
    _name = "test.parameter"
    _description="Lab Test Parameter"

    test_type_id = fields.Many2one('test.type',string="Test Type",ondelete='cascade')
    test_parameter_name = fields.Char(string="Parameter Name",required=True)
    reference_range = fields.Char(string="Reference Range",required=True)
    test_unit = fields.Char(string="Unit")
