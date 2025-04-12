import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PlatFormServiceInventoryHosts(models.Model):
    _name = 'ps.inventory.hosts'  # The name of the model (i.e., the table name in the database)
    _description = 'Platform Service Team- Hosts'
    _inherit = ['mail.thread']  # Inherit from mail.thread to enable chatter

    _track = {
        'name': {'ps_inventory.track_name': 'name'},
        'drive_info': {'ps_inventory.track_drive_info': 'drive_info'},
        'user_id': {'ps_inventory.track_userid' : 'user_id'},
        'drive_id': {'ps_inventory.track_drive_id' : 'drive_id'}
    }

    name = fields.Char(string='Hostname', required=True, unique=True, size=50, tracking=True, index=True)
    ip_address = fields.Char(string='IP Address', help='Enter the IP address of the device', index=True)
    drive_info = fields.Text(string='Drive Information', tracking=True, index=True)
    location = fields.Selection([
        ('9.20', 'lab 9.20'),
        ('9.21', 'lab 9.21')
    ], string='Lab Location', default='9.20', help='Select the location of the lab')
    shelf_location = fields.Char(string='Shelf', size=50)

    user_id = fields.Many2one('res.users', string='Assignee', help='User associated with this host', tracking=True, index=True)


    pdu_chewy = fields.Char(string='Chewy PDU', help='Enter the URL for the Power Distribution Unit')
    pdu_chewy_outlet = fields.Selection([
        ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), 
        ('6', '6'), ('7', '7'), ('8', '8')
    ], string='Chewy PDU Outlet', help='Select the Outlet')

    pdu_dstream = fields.Char(string='DSTREAM PDU', help='Enter the URL for the Power Distribution Unit')
    pdu_dstream_outlet = fields.Selection([
        ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
        ('6', '6'), ('7', '7'), ('8', '8')
    ], string='DSTREAM PDU Outlet', help='Select the Outlet')

    has_dap = fields.Boolean(string='DAP', default=True, help='Indicates whether the DAP is connected or not')
    has_uart = fields.Boolean(string='UART', default=True, help='Indicates whether the UART is connected or not')
    has_pita = fields.Boolean(string='PITA', default=True, help='Indicates whether the PITA card is connected or not')
    has_dstream = fields.Boolean(string='DSTREAM', default=True, help='Indicates whether the DSTREAM is connected or not')
    has_arm = fields.Boolean(string='ARM', default=True, help='Indicates whether the ARM is connected or not')
    has_dediprog = fields.Boolean(string='Dediprog', default=True, help='Indicates whether the Dediprog is connected or not')
    has_Flyswatter2 = fields.Boolean(string='Flyswatter2', default=True, help='Indicates whether the Flyswatter2 is connected or not')
    has_cooling_fan = fields.Boolean(string='Cooling Fan', default=True, help='Indicates whether the Cooling Fan is connected or not')
    image = fields.Binary(string="Image", help="Upload an image", attachment=True)


    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Active', default=True)

    drive_id = fields.Many2one('ps.inventory.drives', string='SSD Drive', tracking=True)  # regular field


    _sql_constraints = [
    ('unique_drive_id', 'unique(drive_id)', 'This drive is already assigned to another host.')
    ]


    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if name:
            args = args or []
            # Search in the 'name' field (hostname)
            args += [('name', operator, name)]
            # Search in the 'ip_address' field
            args += [('ip_address', operator, name)]

            # Search for users that match the search criteria
            user_domain = [
                '|', 
                ('name', operator, name),  # Match user name
                '|',
                ('login', operator, name),  # Match user login
                ('email', operator, name)   # Match user email
            ]
            # Search users and get their ids
            user_ids = self.env['res.users'].search(user_domain).ids

            # Add condition to filter by user_id (the user_ids returned from the search above)
            if user_ids:
                args += [('user_id', 'in', user_ids)]
        
        return super(PlatFormServiceInventoryHosts, self).name_search(name, args, operator, limit)


    @api.constrains('pdu_chewy', 'pdu_dstream')
    def _check_url_format(self):
        for record in self:
            # Validate the PDU URLs
            url_regex = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
            if record.pdu_chewy and not re.match(url_regex, record.pdu_chewy):
                raise ValidationError('Invalid Chewy PDU URL format.')
            if record.pdu_dstream and not re.match(url_regex, record.pdu_dstream):
                raise ValidationError('Invalid DSTREAM PDU URL format.')

    @api.constrains('ip_address')
    def _check_ip_address_format(self):
        for record in self:
            if record.ip_address:
                # Regular expression to validate the IP address format
                ip_regex = r'^(\d{1,3}\.){3}\d{1,3}$'
                if not re.match(ip_regex, record.ip_address):
                    raise ValidationError('Invalid IP address format.')
                

class PlatFormServiceInventoryHostsUsers(models.Model):
    _inherit = 'res.users'

    # Add a One2many field to show related hosts
    host_ids = fields.One2many('ps.inventory.hosts', 'user_id', string='Hosts')
