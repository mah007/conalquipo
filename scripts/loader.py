# -*- coding:utf-8 -*-
import xmlrpclib
import ssl
import csv
import json
import requests


class Importer(object):

    def __init__(self):
        ssl.match_hostname = lambda cert, hostname: True
        self._host = 'https://meycy.atrivia.do'
        self._db = "meycy"
        self._port = 8069
        self._user = 'soporte@atrivia.do'
        self._pwd = "atrivia@123"

        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(self._host))
        self._uid = common.authenticate(self._db, self._user, self._pwd, {})
        self._conn = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(self._host))

    def test_conection(self):
        return True if self._uid else False

    def search(self, model, domain):
        result = self._conn.execute_kw(
            self._db, self._uid, self._pwd, model, 'search', [domain])

        return result

    def search_read(self, model, domain, list_of_fields, limit=False):
        result = self._conn.execute_kw(
            self._db, self._uid, self._pwd, model, 'search_read', [domain],
            {'fields': list_of_fields, 'limit': limit})

        return result

    def create(self, model, vals):
        result = self._conn.execute_kw(
            self._db, self._uid, self._pwd, model, 'create', [vals])

        return result

    def write(self, model, id, vals):
        result = self._conn.execute_kw(
            self._db, self._uid, self._pwd, model, 'write', [id, vals])

        return result

    def load_products(self):
        csv_file = 'productos.csv'

        with open(csv_file, 'r') as f:
            counter = 0
            reader = csv.reader(f)
            reader.next()
            for row in reader:
                product = self.search('product.product', [
                    ('default_code', '=', row[0])])
                if product:
                    print "Producto ya existe, omitiendo creacion."
                    continue

                categ_id = self.search('product.category', [
                    ('name', '=', row[3])])
                brand_id = self.search('product.brand', [
                    ('name', '=', row[3])])
                tax_id = self.search('account.tax', [
                    ('name', '=', 'Exento ITBIS Compras'),
                    ('type_tax_use', '=', 'purchase')])

                if row[3] == 'NACIONAL':
                    taxes = False
                else:
                    taxes = [(6, 0, [tax_id[0]])]

                vals = {
                    'name': row[1],
                    'categ_id': categ_id[0] if categ_id else 1,
                    'default_code': row[0],
                    'alternal_code': row[3],
                    'brand_id': brand_id[0] if brand_id else False,
                    'list_price': float(row[4].replace(',', '.')) if row[4] else 0.0,
                    'default_pricelist_id': row[5],
                    'type': 'product',
                    'supplier_taxes_id': taxes,
                	'purchase_method': 'purchase',
                    'invoice_policy': 'order',
                }
                product_id = self.create('product.product', vals)
                print "Producto creado, ID# %d" % product_id

        print "\n\nCarga de productos terminada de forma satisfactoria!!!\n\n"

if __name__ == '__main__':
    obj = Importer()
    conn = obj.test_conection()
    if conn:
        obj.load_products()
    else:
        print "Problemas con la conexion, favor de verificar  los parametros!!!"
