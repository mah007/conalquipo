#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xmlrpc.client
import csv
import ast

host = 'http://localhost:9001'
db = 'prueba_piloto_productos_limpia'
user = 'dmpineda@conalquipo.com'
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

    # CATEGORIA
    categ_id = sock.execute_kw(
        db, uid, password, 'product.category', 'search_read', [
            [['name', '=', row['Categoria'].strip()]]], {'fields': ['id']})

    if not categ_id:
        categ_id = sock.execute_kw(
            db, uid, password,
            'product.category',
            'create', [{'name': row['Categoria'].strip()}])
    else:
        categ_id = categ_id[0]['id']

    # SECCIONES
    section_id = sock.execute_kw(
        db, uid, password, 'sale.layout_category', 'search_read', [
            [['name', '=', row['Seccion'].strip()]]], {'fields': ['id']})

    if not section_id:
        section_id = sock.execute_kw(
            db, uid, password,
            'sale.layout_category',
            'create', [{'name': row['Seccion'].strip()}])
    else:
        section_id = section_id[0]['id']

    # UNIDADES DE MEDIDA
    ## COMPRA
    uom_po_id = sock.execute_kw(
        db, uid, password, 'product.uom', 'search_read', [
            [['name',
              '=', row[
                  'Unidad de medida de compra'].strip()]]], {'fields': ['id']})

    if not uom_po_id:
        uom_po_id = sock.execute_kw(
            db, uid, password,
            'product.uom',
            'create', [{'name': row['Unidad de medida de compra'].strip()}])
    else:
        uom_po_id = uom_po_id[0]['id']

    ## VENTA
    sale_uom = sock.execute_kw(
        db, uid, password, 'product.uom', 'search_read', [
            [['name',
              '=', row[
                  'Unidad de medida de venta'].strip()]]], {'fields': ['id']})

    if not sale_uom:
        sale_uom = sock.execute_kw(
            db, uid, password,
            'product.uom',
            'create', [{'name': row['Unidad de medida de venta'].strip()}])
    else:
        sale_uom = sale_uom[0]['id']

    ## UNIDAD
    uom_id = sock.execute_kw(
        db, uid, password, 'product.uom', 'search_read', [
            [['name',
              '=', row['Unidad de medida'].strip()]]], {'fields': ['id']})

    if not uom_id:
        uom_id = sock.execute_kw(
            db, uid, password,
            'product.uom',
            'create', [{'name': row['Unidad de medida'].strip()}])
    else:
        uom_id = uom_id[0]['id']

    # PRODUCTO
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
            'uom_po_id': uom_po_id,
            'sale_uom': sale_uom,
            'uom_id': uom_id,
            'default_code': row['Referencia interna'].strip(),
            'type': 'service',
            'active': True,
            'sale_ok': ast.literal_eval(row['Puede ser vendido'].strip()),
            'purchase_ok': ast.literal_eval(row['Puede ser comprado'].strip()),
            'for_shipping': ast.literal_eval(
                row['Usado para acarreo'].strip()),
            'layout_sec_id': section_id,
            'description_sale': row['Notas'].strip(),
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
            'uom_po_id': uom_po_id,
            'sale_uom': sale_uom,
            'uom_id': uom_id,
            'default_code': row['Referencia interna'].strip(),
            'type': 'service',
            'active': True,
            'sale_ok': ast.literal_eval(row['Puede ser vendido'].strip()),
            'purchase_ok': ast.literal_eval(row['Puede ser comprado'].strip()),
            'for_shipping': ast.literal_eval(
                row['Usado para acarreo'].strip()),
            'layout_sec_id': section_id,
            'description_sale': row['Notas'].strip(),
        }

        sock.execute_kw(
            db, uid, password, 'product.template', 'write', [
                [producto_id[0]['id']], vals])

print("Finaliza Proceso (Productos)...")
