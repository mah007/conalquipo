#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xmlrpc.client
import csv

host = 'http://localhost:9002'
db = 'con_odoo12'
user = 'dmpineda@conalquipo.com'
password = 'admin'

sock_common = xmlrpc.client.ServerProxy('{0}/xmlrpc/common'.format(host))
uid = sock_common.login(db, user, password)
sock = xmlrpc.client.ServerProxy('{0}/xmlrpc/object'.format(host))

if not uid:
    print("Credenciales incorrectas")
    exit()

PRODUCTOS = 'unidades.csv'
Productos = csv.DictReader(open(PRODUCTOS), delimiter='|')

print("Iniciando Proceso (Unidades)...")

c = 1
for row in Productos:
    c += 1

    producto_id = sock.execute_kw(
        db, uid, password, 'product.template', 'search_read', [
            [['default_code', '=', row['Producto'].strip()]]],
        {'fields': ['id']})

    uom_id = sock.execute_kw(
        db, uid, password, 'uom.uom', 'search_read', [
            [['name',
              '=', row['Unidad'].strip()]]], {'fields': ['id']})

    ''' Editar producto '''

    message = "Linea {0} --> Editando producto: {1}".format(
        c, row['Producto'].strip())

    print(message)

    vals = {
        'product_id': producto_id[0]['id'],
        'uom_id': uom_id[0]['id'],
        'quantity': row['Cantidad'].strip(),
        'cost_byUom': row['Precio'].strip()
    }

    sock.execute_kw(
        db, uid, password, 'product.multiples.uom', 'create', [vals])

print("Finaliza Proceso (Unidades de productos)...")
