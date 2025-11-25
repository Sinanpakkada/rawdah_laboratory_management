from odoo import api,fields,models

class TestCategory(models.Model):
    _name = "test.category"
    _description = "Test Category"
    _order = "name asc"

    name = fields.Char(string="Category Name",required=True)
    description = fields.Text(string="Description")
    test_type_ids = fields.One2many(
        'test.type','category_id',string="Tests"
    )

