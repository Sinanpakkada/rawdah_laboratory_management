# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class TestResult(models.Model):
    _name = "test.result"
    _description = "Laboratory Test Result"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # --- Fields Definition ---

    result_no = fields.Char(
        string="Lab. No.",
        readonly=True,
        index=True,
        copy=False
    )
    result_date = fields.Datetime(
        string="Test Date",
        default=fields.Datetime.now,
        readonly=True,
        tracking=True
    )

    patient_id = fields.Many2one(
        'res.partner',
        string='Patient',
        tracking=True,
        domain=[('is_patient', '=', True)]
    )
    age = fields.Integer(related='patient_id.age', string="Age", store=True, readonly=True)
    gender = fields.Selection(related='patient_id.gender', string="Gender", store=True, readonly=True)
    phone = fields.Char(related='patient_id.phone', string="Phone", store=True, readonly=True)
    email = fields.Char(related='patient_id.email', string="Email", store=True, readonly=True)

    referred_by = fields.Char(
        string="Referred By",
        help="Name of the referring doctor/facility",
        tracking=True
    )
    reference_no = fields.Char(
        string="Reference No.",
        help="Reference number from referring doctor",
        tracking=True
    )

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
        tracking=True
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
            if rec.age and (rec.age < 0 or rec.age > 150):
                raise UserError(_("Please enter a valid age between 0 and 150."))

    # --- Business Logic Methods (Actions) ---
    def action_save_and_bill(self):
        """Save basic details and print bill, transition to billed"""
        for rec in self:
            if not rec.test_ids:
                raise UserError(_("Please select at least one test before billing."))
        self.write({'state': 'billed'})
        return self.env.ref('rawdah_laboratory_management.action_test_result_report_bill').report_action(self)

    def action_print_result(self):
        """Enter result details, print result, and mark done"""
        for rec in self:
            if not rec.result_line_ids:
                raise UserError(_("Please enter result lines before printing result."))
        self.write({'state': 'done'})
        return self.env.ref('rawdah_laboratory_management.action_test_result_report_result').report_action(self)

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

    def action_edit_result(self):
        self.write({'state':'draft'})

    # --- Onchange method to populate result lines ---

    @api.onchange('test_ids')
    def _onchange_test_ids(self):
        """Automatically populate result lines based on selected tests"""
        if not self.test_ids:
            self.result_line_ids = [(5, 0, 0)]
            return

        # Get all parameters from selected tests
        all_parameters = self.test_ids.mapped('parameter_ids')
        # Remove duplicates explicitly
        all_parameters = self.env['test.parameter'].browse(list(set(all_parameters.ids)))

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
                if line.id:
                    # Delete from database
                    lines_to_remove.append((2, line.id))
                else:
                    # Remove unsaved record from UI
                    lines_to_remove.append((3, 0))

        # Apply changes
        if lines_to_remove or new_lines:
            self.result_line_ids = lines_to_remove + new_lines

    def _populate_result_lines(self):
        """
        Populate result lines based on selected tests.
        Preserves existing result values and only updates parameters.
        """
        for rec in self:
            if not rec.test_ids:
                rec.result_line_ids = [(5, 0, 0)]
                continue

            all_parameters = rec.test_ids.mapped('parameter_ids')
            all_parameters = self.env['test.parameter'].browse(list(set(all_parameters.ids)))

            existing_param_ids = rec.result_line_ids.mapped('parameter_id').ids

            # Add new parameters without affecting existing result values
            for param in all_parameters:
                if param.id not in existing_param_ids:
                    rec.result_line_ids = [(0, 0, {'parameter_id': param.id})]

            # Remove lines for parameters not in selected tests
            lines_to_remove = []
            for line in rec.result_line_ids:
                if line.parameter_id not in all_parameters:
                    lines_to_remove.append((2, line.id))

            if lines_to_remove:
                rec.result_line_ids = lines_to_remove

    # --- CRUD Methods ---

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence number"""
        for vals in vals_list:
            if not vals.get('result_no'):
                sequence = self.env['ir.sequence'].next_by_code('test.result')
                if not sequence:
                    _logger.error("Sequence 'test.result' not found.")
                    raise UserError(
                        _("Lab sequence not configured. Please contact administrator.")
                    )
                vals['result_no'] = sequence
                _logger.info(f"Generated result_no: {sequence}")

        records = super().create(vals_list)
        records._populate_result_lines()
        return records

    def write(self, vals):
        """Override write to handle updates"""
        res = super().write(vals)

        # Regenerate result lines only if test_ids changed
        if 'test_ids' in vals:
            self._populate_result_lines()

        return res