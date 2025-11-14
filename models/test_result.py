# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TestResult(models.Model):
    _name = "test.result"
    _description = "Laboratory Test Result"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # --- Fields Definition ---

    result_no = fields.Char(
        string="Lab. No.",
        readonly=True,
        default=lambda self: _("New"),
        index=True  # Added for better search performance
    )
    result_date = fields.Datetime(
        string="Test Date",
        default=fields.Datetime.now,
        readonly=True,
        tracking=True  # Added tracking for audit trail
    )

    patient_id = fields.Many2one(
        'res.partner',
        string='Patient',
        required=True,
        tracking=True,
        domain=[('is_patient', '=', True)]  # Optional: you can add a filter if you distinguish patients
    )
    age = fields.Integer(related='patient_id.age', string="Age", store=True, readonly=True)
    gender = fields.Selection(related='patient_id.gender', string="Gender", store=True, readonly=True)
    phone = fields.Char(related='patient_id.phone', string="Phone", store=True, readonly=True)
    email = fields.Char(related='patient_id.email', string="Email", store=True, readonly=True)

    # phone = fields.Char(
    #     string="Mobile",
    #     help="Patient's contact mobile number."
    # )
    # email = fields.Char(
    #     string="Email",
    #     help="Patient's contact email address."
    # )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('billed', 'Billed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='draft', string="Status", tracking=True)

    test_ids = fields.Many2many(
        'test.type',
        string="Tests",
        help="Select the tests requested for the patient.",
        tracking=True  # Added tracking
    )
    result_line_ids = fields.One2many(
        'test.result.line',
        'result_id',
        string="Result Lines"
    )

    # --- Constraints ---

    @api.constrains('age')
    def _check_age(self):
        for rec in self:
            if rec.age < 0 or rec.age > 150:
                raise UserError(_("Please enter a valid age between 0 and 150."))

    # --- Business Logic Methods (Actions) ---
    def action_save_and_bill(self):
        """Save basic details and print bill, transition to billed"""
        for rec in self:
            if not rec.test_ids:
                raise UserError(_("Please select at least one test before billing."))
        self.write({'state': 'billed'})
        #email,whatsapp,bill printing

    def action_print_result(self):
        """Enter result details, print result, and mark done"""
        for rec in self:
            if not rec.result_line_ids:
                raise UserError(_("Please enter result lines before printing result."))
        self.write({'state': 'done'})
        # email,whatsapp,result printing

    def action_cancel_test(self):
        """Cancel the test"""
        for rec in self:
            if rec.state == 'done':
                raise UserError(_("Cannot cancel a test which is already done."))
        self.write({'state': 'cancel'})

    def action_reset_to_draft(self):
        """Reset test to draft state"""
        for rec in self:
            if rec.state == 'done':
                raise UserError(_("Cannot reset a done test to draft."))
        self.write({'state': 'draft'})

    # --- Onchange method to populate result lines ---

    @api.onchange('test_ids')
    def _onchange_test_ids(self):
        """Automatically populate result lines based on selected tests"""
        if not self.test_ids:
            self.result_line_ids = [(5, 0, 0)]  # Clear all lines
            return

        # Get all parameters from selected tests
        all_parameters = self.test_ids.mapped('parameter_ids')

        # Get existing parameter IDs to avoid duplicates
        existing_param_ids = self.result_line_ids.mapped('parameter_id').ids

        # Create lines only for new parameters
        new_lines = []
        for param in all_parameters:
            if param.id not in existing_param_ids:
                new_lines.append((0, 0, {
                    'parameter_id': param.id,
                }))

        # Remove lines for parameters not in selected tests
        lines_to_remove = []
        for line in self.result_line_ids:
            if line.parameter_id not in all_parameters:
                if line.id:  # If it's a saved record
                    lines_to_remove.append((2, line.id, 0))  # Delete it
                else:  # If it's a new record in the form
                    lines_to_remove.append((3, line.id, 0))  # Remove from list

        # Apply changes
        if lines_to_remove or new_lines:
            self.result_line_ids = lines_to_remove + new_lines

    # --- CRUD Methods ---

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence number"""
        for vals in vals_list:
            if not vals.get('result_no') or vals.get('result_no') == _('New'):
                vals['result_no'] = self.env['ir.sequence'].next_by_code('test.result') or _('New')
        records = super().create(vals_list)
        return records

    # --- Helper Methods ---

    # def name_get(self):
    #     """Custom display name for the model"""
    #     result = []
    #     for rec in self:
    #         name = f"{rec.result_no} - {rec.patient_name}"
    #         result.append((rec.id, name))
    #     return result
    #
    # @api.model
    # def _name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
    #     """Custom search by result_no or patient_name"""
    #     args = args or []
    #     if name:
    #         args = ['|', ('result_no', operator, name), ('patient_name', operator, name)] + args
    #     return self._search(args, limit=limit, order=order)