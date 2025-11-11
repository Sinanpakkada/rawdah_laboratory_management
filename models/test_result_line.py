from odoo import fields,models,api


class TestResultLine(models.Model):
    _name = 'test.result.line'
    _description = 'Test Result Lines'

    result_id = fields.Many2one('test.result',string="Result ID",ondelete='cascade')
    test_id = fields.Many2one('test.type',string="Test ID")
    parameter_id = fields.Many2one('test.parameter',string='Parameter ID')
    result_value = fields.Char(string="Result Value")
    reference_range = fields.Char(string="Reference Range")
    test_unit = fields.Char(string="Unit")

    @api.onchange('parameter_id')
    def _onchange_parameter_id(self):
        for rec in self:
            if rec.parameter_id:
                rec.reference_range = rec.parameter_id.reference_range
                rec.test_unit = rec.parameter_id.test_unit
