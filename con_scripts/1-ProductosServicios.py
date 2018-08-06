#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xmlrpc.client
import csv

host = 'http://localhost:9001'
db = 'prueba_piloto_productos'
user = 'admin'
password = 'admin'

sock_common = xmlrpc.client.ServerProxy('{0}/xmlrpc/common'.format(host))
uid = sock_common.login(db, user, password)
sock = xmlrpc.client.ServerProxy('{0}/xmlrpc/object'.format(host))

if not uid:
    print("Credenciales incorrectas")
    exit()

PRODUCTOS = 'servicios.csv'
Productos = csv.DictReader(open(PRODUCTOS), delimiter='|')

print("Iniciando Proceso (Productos)...")

c = 1
for row in Productos:
    c += 1

    categ_id = sock.execute_kw(
        db, uid, password, 'product.category', 'search_read', [
            [['name', '=', row['Categoria'].strip()]]], {'fields': ['id']})

    uom_id = sock.execute_kw(
        db, uid, password, 'product.uom', 'search_read', [
            [['name',
              '=', row['Unidad de medida'].strip()]]], {'fields': ['id']})

    if not categ_id:
        categ_id = sock.execute_kw(
            db, uid, password,
            'product.category',
            'create', [{'name': row['Categoria'].strip()}])
    else:
        categ_id = categ_id[0]['id']

    producto_id = sock.execute_kw(
        db, uid, password, 'product.template', 'search_read', [
            [['default_code', '=', row['Referencia interna'].strip()]]],
        {'fields': ['id']})

    if not producto_id:

        ''' Crear producto nuevo '''

        message = "Linea {0} --> Creando producto: {1}".format(
            c, row['Producto'].strip())

        print(message)

        vals = {

            'name': row['Producto'].strip(),
            'standard_price': row['Coste'].strip(),
            'list_price': row['Precio de venta por unidad de medida'].strip(),
            'categ_id': categ_id,
            'sale_uom': uom_id[0]['id'],
            'default_code': row['Referencia interna'].strip(),
            'type': 'service',
            'active': True,
            'sale_ok': True,
            'purchase_ok': True,
        }

        sock.execute_kw(
            db, uid, password, 'product.template', 'create', [vals])

    else:

        ''' Editar producto '''

        message = "Linea {0} --> Editando producto: {1}".format(
            c, row['Producto'].strip())

        print(message)

        vals = {
            'name': row['Producto'].strip(),
            'standard_price': row['Coste'].strip(),
            'list_price': row['Precio de venta por unidad de medida'].strip(),
            'categ_id': categ_id,
            'sale_uom': uom_id[0]['id'],
            'default_code': row['Referencia interna'].strip(),
            'type': 'service',
            'active': True,
            'sale_ok': True,
            'purchase_ok': True,
        }

        sock.execute_kw(
            db, uid, password, 'product.template', 'write', [
                [producto_id[0]['id']], vals])

print("Finaliza Proceso (Productos)...")
