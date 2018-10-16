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

PRODUCTOS = 'complementos.csv'
Productos = csv.DictReader(open(PRODUCTOS), delimiter='|')

print("Iniciando Proceso (Complementos)...")

c = 1
for row in Productos:
    c += 1

    producto_id = sock.execute_kw(
        db, uid, password, 'product.template', 'search_read', [
            [['default_code', '=', row['Producto'].strip()]]],
        {'fields': ['id']})

    ''' Editar producto '''

    message = "Linea {0} --> Editando producto: {1}".format(
        c, row['Producto'].strip())

    print(message)

    myList = row['Complementos']
    myString = list(myList.split(","))

    for data in myString:
        print(data.replace(" ", ""))

        comp_id = sock.execute_kw(
            db, uid, password, 'product.product', 'search_read', [
                [['default_code', 'in', data.replace(" ", "").split()]]],
            {'fields': ['id']})

        if comp_id:
            vals = {
                'product_id': producto_id[0]['id'],
                'product_child_id': comp_id[0]['id'],
                'quantity': 1,
                'child': True
            }

            sock.execute_kw(
                db, uid, password, 'product.components', 'create', [vals])

print("Finaliza Proceso (Productos)...")
