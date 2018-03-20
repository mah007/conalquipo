# -*- coding:utf-8 -*-
import xmlrpclib
import ssl
import csv
import json
import requests


class Importer(object):

    def __init__(self):
        ssl.match_hostname = lambda cert, hostname: True
        self._host = 'http://localhost'
        self._db = "conalequipo_odoo11e"
        self._port = 9073
        self._user = 'admin'
        self._pwd = "admin"

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
                counter += 1
                product = self.search('product.product', [
                    ('default_code', '=', row[0])])
                if product:
                    print "Producto ya existe, omitiendo creacion."
                    continue

                categ_id = self.search('product.category', [
                    ('name', '=', row[3])])
                uom_id = self.search('product.uom', [
                    ('name', '=', row[3])])
                vals = {
                    'name': row[1],
                    'categ_id': categ_id[0] if categ_id else 1,
                    'default_code': row[0],
                    'uom_id': uom_id[0] if uom_id else False,
                    'type': 'product',
                }
                product_id = self.create('product.product', vals)
                print counter
                print "Producto creado, ID# %d" % product_id

        print "\n\nCarga de productos terminada de forma satisfactoria!!!\n\n"

if __name__ == '__main__':
    obj = Importer()
    conn = obj.test_conection()
    if conn:
        obj.load_products()
    else:
        print "Problemas con la conexion, favor de verificar  los parametros!!!"
