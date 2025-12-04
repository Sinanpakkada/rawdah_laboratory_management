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

    bill_line_ids = fields.One2many(
        'test.result.bill.line',
        'result_id',
        string="Bill Lines",
        copy=True
    )

    total_amount = fields.Float(
        string="Total Amount",
        compute='_compute_total_amount',
        store=True,
        tracking=True
    )

    # --- Compute Methods ---
    @api.depends('bill_line_ids.amount')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.bill_line_ids.mapped('amount')) if rec.bill_line_ids else 0.0

    # --- Constraints ---

    @api.constrains('age')
    def _check_age(self):
        for rec in self:
            if rec.age and (rec.age < 0 or rec.age > 150):
                raise UserError(_("Please enter a valid age between 0 and 150."))

    # --- Onchange Methods (UI Preview Only) ---

    @api.onchange('test_ids')
    def _onchange_test_ids(self):
        """
        UI Preview: Show result lines and bill lines when selecting tests.
        This only affects the form view before saving.
        Actual persistence is handled by create() and write() methods.
        """
        if not self.test_ids:
            self.result_line_ids = [(5, 0, 0)]
            self.bill_line_ids = [(5, 0, 0)]
            return

        # ==================== RESULT LINES (KEEP AS IS - WORKING PERFECTLY) ====================
        all_parameters = self.test_ids.mapped('parameter_ids')
        all_param_ids = set(all_parameters.ids)

        existing_lines = {line.parameter_id.id: line for line in self.result_line_ids}
        existing_param_ids = set(existing_lines.keys())

        result_commands = []

        # Remove lines for deselected parameters
        for param_id, line in existing_lines.items():
            if param_id not in all_param_ids:
                if line.id:
                    result_commands.append((2, line.id, 0))
                else:
                    result_commands.append((3, line.id, 0))

        # Add new parameter lines
        for param_id in all_param_ids:
            if param_id not in existing_param_ids:
                result_commands.append((0, 0, {'parameter_id': param_id}))

        if result_commands:
            self.result_line_ids = result_commands

        # ==================== BILL LINES (FIXED - Only for existing records) ====================
        # Skip bill line preview for new unsaved records to avoid mandatory field error
        if not self.id:
            return

        selected_test_ids = set(self.test_ids.ids)
        existing_bill_lines = {line.test_id.id: line for line in self.bill_line_ids if line.test_id}
        existing_test_ids = set(existing_bill_lines.keys())

        bill_commands = []

        # Remove bill lines for deselected tests
        for test_id, line in existing_bill_lines.items():
            if test_id not in selected_test_ids:
                bill_commands.append((2, line.id, 0))

        # Add bill lines for new tests
        for test in self.test_ids:
            if test.id not in existing_test_ids:
                bill_commands.append((0, 0, {
                    'test_id': test.id,
                }))

        if bill_commands:
            self.bill_line_ids = bill_commands

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
        """Cancel the test - Manager Only"""
        # Check if user belongs to the manager group
        if not self.env.user.has_group('rawdah_laboratory_management.group_lab_manager'):
            raise UserError(_("Only a Laboratory Manager can cancel a test."))

        """Cancel the test"""
        for rec in self:
            if rec.state == 'done':
                raise UserError(_("Cannot cancel a test which is already done."))
        self.write({'state': 'cancel'})

    def action_reset_to_draft(self):
        """Reset test to draft state"""
        for rec in self:
            if rec.state == 'done':
                raise UserError(_("Cannot reset a done or cancelled test to draft."))
        self.write({'state': 'draft'})

    def action_edit_result(self):
        """Allow editing of result by resetting to billed"""
        self.write({'state':'billed'})

    # --- Internal Methods ---

    def _populate_result_lines(self):
        """
        Populate result lines based on selected tests.
        Preserves existing result values and only updates parameters.
        Uses batched One2many commands for optimal performance.
        """
        for rec in self:
            if not rec.test_ids:
                rec.result_line_ids = [(5, 0, 0)]
                continue

            # Get all unique parameters from selected tests
            all_parameters = rec.test_ids.mapped('parameter_ids')
            all_param_ids = set(all_parameters.ids)

            # Get existing parameter IDs
            existing_lines = {line.parameter_id.id: line for line in rec.result_line_ids}
            existing_param_ids = set(existing_lines.keys())

            # Build batched commands
            commands = []

            # Remove lines for parameters not in selected tests
            for param_id, line in existing_lines.items():
                if param_id not in all_param_ids:
                    commands.append((2, line.id, 0))

            # Add new parameters (preserves existing result values)
            for param_id in all_param_ids:
                if param_id not in existing_param_ids:
                    commands.append((0, 0, {'parameter_id': param_id}))

            # Apply all changes in a single write operation
            if commands:
                rec.result_line_ids = commands

    def _update_bill_lines(self):
        """
        Update bill lines based on selected tests.
        Preserves user-modified amounts by only adding/removing lines.
        Uses batched One2many commands for optimal performance.
        """
        for rec in self:
            if not rec.test_ids:
                rec.bill_line_ids = [(5, 0, 0)]
                continue

            # Get selected test IDs
            selected_test_ids = set(rec.test_ids.ids)

            # Get existing bill lines mapped by test_id
            existing_lines = {line.test_id.id: line for line in rec.bill_line_ids}
            existing_test_ids = set(existing_lines.keys())

            # Build batched commands
            commands = []

            # Remove bill lines for deselected tests
            for test_id, line in existing_lines.items():
                if test_id not in selected_test_ids:
                    commands.append((2, line.id, 0))

            # Add bill lines for newly selected tests only
            for test_id in selected_test_ids:
                if test_id not in existing_test_ids:
                    commands.append((0, 0, {'test_id': test_id}))

            # Apply all changes in a single write operation
            if commands:
                rec.bill_line_ids = commands

    # --- CRUD Methods ---

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence number and populate lines"""
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

        # Populate result lines and bill lines based on selected tests
        records._populate_result_lines()
        records._update_bill_lines()

        return records

    def write(self, vals):
        """Override write to handle test changes"""
        res = super().write(vals)

        # Update lines only if test_ids changed
        if 'test_ids' in vals:
            self._populate_result_lines()
            self._update_bill_lines()

        return res
