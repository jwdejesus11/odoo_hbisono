import base64
import logging
import os
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Starting post-migration script for Hnos Bisono configuration update.")

    # 1. Update company Hnos Bisono configuration and load logo
    c = env['res.company'].browse(1)
    if c.exists():
        c.write({
            'name': 'Hnos Bisonó',
            'vat': '130836345',
            'country_id': env.ref('base.do').id,
            'currency_id': env.ref('base.DOP').id
        })
        _logger.info("Updated company ID 1 config.")

        # Try to read and load the logo from extra-addons
        logo_paths = [
            '/mnt/extra-addons/hbisono.jpeg',
            '/mnt/extra-addons/l10n-dominicana/hbisono.jpeg',
            'hbisono.jpeg'
        ]
        logo_loaded = False
        for path in logo_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        c.write({'logo': base64.b64encode(f.read())})
                        _logger.info("Successfully loaded logo from %s", path)
                        logo_loaded = True
                        break
                except Exception as e:
                    _logger.error("Error reading logo from %s: %s", path, e)
        if not logo_loaded:
            _logger.error("Logo file hbisono.jpeg not found in standard paths.")

    # 2. Archive all other companies
    other_companies = env['res.company'].search([('id', '!=', 1)])
    if other_companies:
        other_companies.write({'active': False})
        _logger.info("Archived %s secondary companies.", len(other_companies))

    # 3. Limit all users allowed companies to only Hnos Bisono (ID 1)
    # This prevents anyone from seeing invoices/records from other companies
    users = env['res.users'].search([])
    if users:
        users.write({
            'company_id': 1,
            'company_ids': [(6, 0, [1])]
        })
        _logger.info("Restricted %s users to only Hnos Bisono (ID 1).", len(users))

    # 4. Point of Sale (POS) configurations
    # Set POS config named 'Hnos Bisono'
    pos = env['pos.config'].search([('company_id', '=', 1)], limit=1)
    if pos:
        pos.write({'name': 'Hnos Bisonó', 'active': True})
        _logger.info("Renamed main POS config to 'Hnos Bisonó'.")
    else:
        env['pos.config'].create({'name': 'Hnos Bisonó', 'company_id': 1})
        _logger.info("Created main POS config 'Hnos Bisonó'.")

    # Archive POS configs named 'Shop', 'Restaurant', 'shop', 'restaurant'
    other_pos = env['pos.config'].search([('name', 'in', ('Shop', 'Restaurant', 'shop', 'restaurant'))])
    if other_pos:
        other_pos.write({'active': False})
        _logger.info("Archived secondary POS configs: %s", other_pos.mapped('name'))

    # 5. Enable LATAM documents on sales/purchases journals for company ID 1
    journals = env['account.journal'].search([
        ('company_id', '=', 1),
        ('type', 'in', ('sale', 'purchase'))
    ])
    if journals:
        journals.write({'l10n_latam_use_documents': True})
        _logger.info("Enabled LATAM use_documents on sales/purchases journals.")

    # 6. Force es_DO language settings
    try:
        env['res.lang']._activate_lang('es_DO')
        _logger.info("Activated language es_DO.")
    except Exception as e:
        _logger.error("Error activating es_DO language: %s", e)

    # Set all users and partners to Spanish (es_DO)
    env['res.users'].search([]).write({'lang': 'es_DO'})
    env['res.partner'].search([]).write({'lang': 'es_DO'})
    _logger.info("Set all users/partners language to es_DO.")
    _logger.info("Finished post-migration script for Hnos Bisono configuration update.")
