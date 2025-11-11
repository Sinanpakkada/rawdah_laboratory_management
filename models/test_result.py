from odoo import fields,models,api


class TestResult(models.Model):
    _name = "test.result"
    _description = "Test Result"
    _inherit = ['mail.thread','mail.activity.mixin']

    result_no = fields.Char(string="Lab. No.",readonly=True,copy=False)
    result_date = fields.Datetime(string="Test Date", default=fields.Datetime.now, readonly=True)
    patient_name = fields.Char(string="Patient Name", required=True,)
    age=fields.Integer(string="Age",required=True)
    gender=fields.Selection([
        ("male","Male"),
        ("female","Female")
    ],string="Gender",required=True)
    phone=fields.Char(string="Mobile")
    email=fields.Char(string="Email")
    state=fields.Selection([
        ('draft','Draft'),
        ('bill','Bill'),
        ('result','Result')
    ],default='draft',string="State")
    test_ids = fields.Many2many('test.type',string="Tests")
    result_line_ids = fields.One2many('test.result.line','result_id',string="Result Line")
    def action_generate_bill(self):
        for rec in self:
            self.write({'state':'bill'})

    def action_generate_result(self):
        for rec in self:
            self.write({'state':'result'})

    # def create(self, vals):
    #     if not vals.get('result_no'):
    #         vals['result_no']=self.env['ir.sequence'].next_by_code('test_result')
    #     return super(TestResult,self).create(vals)

    @api.model
    def create(self, vals):
        """Generate lab number only once at creation."""
        if not vals.get('result_no') or vals.get('result_no') == 'New':
            vals['result_no'] = self.env['ir.sequence'].next_by_code('test.result')
        return super(TestResult, self).create(vals)

