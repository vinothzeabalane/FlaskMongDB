
from odoo import models, fields

class PlatFormServiceInventoryDrives(models.Model):
    _name = 'ps.inventory.drives'  # The name of the model (i.e., the table name in the database)
    _description = 'Platform Service Team- SSD Drives'
    _inherit = ['mail.thread']  # Inherit from mail.thread to enable chatter

    _track = {
        'name': {'ps_inventory_drives.track_name': 'name'},
        'ssd_info': {'ps_inventory.track_ssd_info': 'ssd_info'},
        'user_id': {'ps_inventory_drives.track_userid' : 'user_id'}
    }

    name = fields.Char(string='SSN', required=True, unique=True, size=50, tracking=True, index=True)
    density = fields.Char(string='Density', required=True,  size=10, help='SKU Size', index=True)
    ssd_info = fields.Text(string='Other Information', tracking=True)
    program = fields.Char(string='Program', required=True,  size=25, help='Program ex: HDC/ HDR', index=True)
    media_type = fields.Char(string='Nand/Media', size=50)
    source = fields.Selection([
        ('primary', 'PRIMARY SOURCE'),
        ('secondary', 'SECONDARY SOURCE')
    ], string='Material Source', default='primary', help='Select the source type')

    user_id = fields.Many2one('res.users', string='Assignee', help='User associated with this host', tracking=True, index=True)
    product_code_id = fields.Many2one('ps.inventory.product.code', string='Product Code', help='Link to the Product Code')
    notes = fields.Text(string='Notes')
    image = fields.Binary(string="Image", help="Upload an image", attachment=True)
    active = fields.Boolean(string='Active', default=True)
                

class PlatFormServiceInventoryProductCode(models.Model):
    _name = 'ps.inventory.product.code'  # The name of the model (i.e., the table name in the database)
    _description = 'Platform Service Team- Product Code'

    # Add a One2many field to show related hosts
    product_code_ids = fields.One2many('ps.inventory.drives', 'product_code_id', string='Product Code')
    name = fields.Char(string='Name', required=True, unique=True, size=50)
    notes = fields.Char(string='Notes')


class PlatFormServiceInventoryDrivesUsers(models.Model):
    _inherit = 'res.users'

    # Add a One2many field to show related hosts
    drive_ids = fields.One2many('ps.inventory.drives', 'user_id', string='SSD')