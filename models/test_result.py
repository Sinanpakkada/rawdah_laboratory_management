# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class TestResult(models.Model):
    _name = "test.result"
    _description = "Laboratory Test Result"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "result_date desc, id desc"

    # --- Fields Definition ---

    result_no = fields.Char(
        string="Lab. No.", readonly=True, copy=False, default=_("New")
    )
    result_date = fields.Datetime(
        string="Test Date", default=fields.Datetime.now, readonly=True
    )

    patient_name = fields.Char(string="Patient Name", required=True, tracking=True)
    age = fields.Integer(string="Age", required=True, tracking=True)
    gender = fields.Selection([
        ("male", "Male"),
        ("female", "Female")
    ], string="Gender", required=True)
    phone = fields.Char(string="Mobile", help="Patient's contact mobile number.")
    email = fields.Char(string="Email", help="Patient's contact email address.")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('billed', 'Billed'),
        ('cancel', 'Cancelled')
    ], default='draft', string="Status", tracking=True)

    test_ids = fields.Many2many(
        'test.type', string="Tests", help="Select the tests requested for the patient."
    )
    result_line_ids = fields.One2many(
        'test.result.line', 'result_id', string="Result Lines"
    )

    # --- Business Logic Methods (Actions) ---

    def action_start_test(self):
        self.write({'state': 'in_progress'})

    def action_mark_done(self):
        self.write({'state': 'done'})

    def action_generate_bill(self):
        self.write({'state': 'billed'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    # --- Onchange method to populate result lines ---

    @api.onchange('test_ids')
    def _onchange_test_ids(self):
        if not self.test_ids:
            self.result_line_ids = [(5, 0, 0)]
            return

        # Use commands to avoid issues with already saved records
        self.result_line_ids = [(5, 0, 0)]  # Clear existing lines

        lines_to_create = []
        for test in self.test_ids:
            for param in test.parameter_ids:
                lines_to_create.append((0, 0, {
                    'parameter_id': param.id,
                }))

        self.result_line_ids = lines_to_create

    # --- CRUD Methods ---

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('result_no') or vals.get('result_no') == _('New'):
                vals['result_no'] = self.env['ir.sequence'].next_by_code('test.result') or _('New')
        return super().create(vals_list)