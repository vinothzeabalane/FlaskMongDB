from odoo import models, fields

class PlatFormServiceInventory(models.Model):
    _name = 'ps.inventory'  # The name of the model (i.e., the table name in the database)
    _description = 'Platform Service Team- Inventory details'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
