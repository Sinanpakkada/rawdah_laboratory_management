# -*- coding: utf-8 -*-
from odoo import api, fields, models, _  # Added _ for translations


class TestResult(models.Model):
    _name = "test.result"
    _description = "Laboratory Test Result"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # It's good practice to set a default order. This will show the newest records first.
    _order = "result_date desc"

    # --- Fields Definition ---

    # Sequence field, correctly implemented
    result_no = fields.Char(
        string="Lab. No.", readonly=True, copy=False, default=_("New")
    )
    result_date = fields.Datetime(
        string="Test Date", default=fields.Datetime.now, readonly=True
    )

    # Patient Information
    patient_name = fields.Char(
        string="Patient Name", required=True, tracking=True
    )
    age = fields.Integer(
        string="Age", required=True, tracking=True
    )
    gender = fields.Selection([
        ("male", "Male"),
        ("female", "Female")
    ], string="Gender", required=True)
    phone = fields.Char(
        string="Mobile", help="Patient's contact mobile number."
    )
    email = fields.Char(
        string="Email", help="Patient's contact email address."
    )

    # State field with a clearer, more descriptive workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('billed', 'Billed'),
        ('cancel', 'Cancelled')
    ], default='draft', string="Status", tracking=True)

    # Relational Fields
    test_ids = fields.Many2many(
        'test.type', string="Tests",
        help="Select the tests requested for the patient."
    )
    result_line_ids = fields.One2many(
        'test.result.line', 'result_id', string="Result Lines"
    )

    # --- Business Logic Methods (Actions) ---

    def action_start_test(self):
        """Changes the state to 'In Progress'."""
        self.write({'state': 'in_progress'})

    def action_mark_done(self):
        """Changes the state to 'Done' after results are entered."""
        self.write({'state': 'done'})

    def action_generate_bill(self):
        """
        This method will eventually create an invoice.
        For now, it just changes the state to 'Billed'.
        """
        self.write({'state': 'billed'})
        # Future enhancement: Create customer invoice logic here
        # self.env['account.move'].create({...})

    def action_cancel(self):
        """Changes the state to 'Cancelled'."""
        self.write({'state': 'cancel'})

    def action_reset_to_draft(self):
        """Resets the record to the 'Draft' state."""
        self.write({'state': 'draft'})

    # --- Core Logic: Onchange method to populate result lines ---

    @api.onchange('test_ids')
    def _onchange_test_ids(self):
        """
        When tests are added/removed, this method updates the result lines.
        It creates new lines for newly added tests.
        Old lines are not removed automatically to prevent data loss,
        but you could add logic for that if needed.
        """
        # First, clear existing lines if you want to fully sync.
        # Be careful, this can cause data loss if results are already entered.
        # A safer approach is to only add, not remove.
        self.result_line_ids = [(5, 0, 0)]  # Command to clear all existing One2many lines

        lines_to_create = []
        for test in self.test_ids:
            for param in test.parameter_ids:
                lines_to_create.append({
                    'parameter_id': param.id,
                    'normal_range': param.normal_range,
                    'unit_id': param.unit_id.id,
                })

        # Odoo's special command (0, 0, {values}) creates a new record in the One2many
        self.result_line_ids = [(0, 0, vals) for vals in lines_to_create]

    # --- CRUD Methods (Create, Read, Update, Delete) ---

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to generate the lab number using a sequence.
        Using @api.model_create_multi is the modern Odoo 17 approach.
        """
        for vals in vals_list:
            if not vals.get('result_no') or vals.get('result_no') == _('New'):
                vals['result_no'] = self.env['ir.sequence'].next_by_code('test.result')
        return super().create(vals_list)