#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xmlrpc.client
import csv

host = 'http://localhost:9001'
db = 'prueba_piloto_productos'
user = 'dmpineda@conalquipo.com'
password = 'admin'

sock_common = xmlrpc.client.ServerProxy('{0}/xmlrpc/common'.format(host))
uid = sock_common.login(db, user, password)
sock = xmlrpc.client.ServerProxy('{0}/xmlrpc/object'.format(host))

if not uid:
    print("Credenciales incorrectas")
    exit()

PRODUCTOS = 'complementos_cantidades.csv'
Productos = csv.DictReader(open(PRODUCTOS), delimiter='|')

print("Iniciando Proceso (Cambio de cantidades de componentes)...")

c = 1
for row in Productos:
    c += 1

    producto_id = sock.execute_kw(
        db, uid, password, 'product.template', 'search_read', [
            [['default_code', '=', row['Producto'].strip()]]],
        {'fields': ['id']})

    product_comp_id = sock.execute_kw(
        db, uid, password, 'product.template', 'search_read', [
            [['default_code', '=', row['Componente'].strip()]]],
        {'fields': ['id']})

    comp_id = sock.execute_kw(
        db, uid, password, 'product.components', 'search_read',
        [[['product_id', '=', producto_id[0]['id']],
          ['product_child_id', '=',  product_comp_id[0]['id']]]],
          {'fields': ['id']})

    ''' Editar producto '''

    if comp_id:
        message = "Linea {0} --> Editando componente de: {1}".format(
            c, row['Producto'].strip())

        print(message)

        vals = {
            'quantity': row['Cantidad'].strip(),
        }

        sock.execute_kw(
            db, uid, password, 'product.components', 'write', [
                [comp_id[0]['id']], vals])

print("Finaliza actualizacion de cantidades de componentes")
