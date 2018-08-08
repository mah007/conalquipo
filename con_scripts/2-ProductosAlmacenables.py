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

PRODUCTOS = 'almacenables.csv'
Productos = csv.DictReader(open(PRODUCTOS), delimiter='|')

print("Iniciando Proceso (Productos)...")

c = 1
for row in Productos:
    c += 1

    # Product category ##############################################
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
    #################################################################

    uom_id = sock.execute_kw(
        db, uid, password, 'product.uom', 'search_read', [
            [['name',
              '=', row['Unidad de medida'].strip()]]], {'fields': ['id']})

    origin_location_id = sock.execute_kw(
        db, uid, password, 'stock.location', 'search_read', [
            [['complete_name',
              '=', row['Ubicacion origen'].strip()]]], {'fields': ['id']})

    location_id = sock.execute_kw(
        db, uid, password, 'stock.location', 'search_read', [
            [['complete_name',
              '=', row[
                  'Ubicacion del producto'].strip()]]], {'fields': ['id']})

    producto_id = sock.execute_kw(
        db, uid, password, 'product.template', 'search_read', [
            [['default_code', '=', row['Referencia interna'].strip()]]],
        {'fields': ['id']})

    rep_producto_id = sock.execute_kw(
        db, uid, password, 'product.template', 'search_read', [
            [['name', '=', row['fact-cargo por reabastecimiento'].strip()]]],
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
            'type': 'product',
            'active': True,
            'sale_ok': row['Puede ser vendido'],
            'purchase_ok': row['Puede ser comprado'],
            'rental': row['Puede ser alquilado'],
            'components': row['Tiene componentes'],
            'multiples_uom': row['Tiene multiples unidades'],
            'is_operated': row['inv-es operado'],
            'product_origin': origin_location_id[0]['id'],
            'location_id': location_id[0]['id'],
            'color': row['Estado'],
            'replenishment_charge': rep_producto_id[0]['id'],
        }

        product_id = sock.execute_kw(
            db, uid, password, 'product.template', 'create', [vals])


        # Add to public pricelist ###################################

        pricelist_id = sock.execute_kw(
            db, uid, password, 'product.pricelist', 'search_read', [
                [['sequence', '=', 2]]],
            {'fields': ['id']})

        sock.execute_kw(
            db, uid, password, 'product.pricelist.item', 'create', [
                {'product_tmpl_id': product_id,
                 'applied_on': '1_product',
                 'compute_price': 'percentage',
                 'percent_price': 0.0,
                 'pricelist_id': pricelist_id[0]['id']}])

        #############################################################

        if row['prov-vendedor']:

            # Create suppliers ######################################
            supplier_id = sock.execute_kw(
                db, uid, password, 'res.partner', 'search_read', [
                    [['name', '=', row['prov-vendedor'].strip()]]],
                {'fields': ['id']})

            if not supplier_id:
                vals_supplier = {
                    'name': row['prov-vendedor'].strip(),
                    'supplier': True,
                    'customer': False,
                    'company_type': 'company'
                }
                supplier_id = sock.execute_kw(
                    db, uid, password,
                    'res.partner',
                    'create', [vals_supplier])
            else:
                supplier_id = supplier_id[0]['id']
            #################################################################

            sock.execute_kw(
                db, uid, password, 'product.supplierinfo', 'create', [
                    {'name': supplier_id,
                     'product_name': row['Producto'].strip(),
                     'product_code': row['Referencia interna'].strip(),
                     'product_tmpl_id': product_id}])

        if row['mum-unidad']:

            uoms_id = sock.execute_kw(
                db, uid, password, 'product.uom', 'search_read', [
                    [['name',
                      '=', row['mum-unidad'].strip()]]],
                {'fields': ['id']})

            sock.execute_kw(
                db, uid, password, 'product.multiples.uom', 'create', [
                    {'uom_id': uoms_id[0]['id'],
                     'cost_byUom': row['mum-costo por unidad'].strip(),
                     'quantity': row['mum-cant.min'].strip(),
                     'product_id': product_id}])
        else:
            product_id

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
            'type': 'product',
            'active': True,
            'sale_ok': row['Puede ser vendido'],
            'purchase_ok': row['Puede ser comprado'],
            'rental': row['Puede ser alquilado'],
            'components': row['Tiene componentes'],
            'multiples_uom': row['Tiene multiples unidades'],
            'is_operated': row['inv-es operado'],
            'product_origin': origin_location_id[0]['id'],
            'location_id': location_id[0]['id'],
            'color': row['Estado'],
            'replenishment_charge': rep_producto_id[0]['id'],
        }

        sock.execute_kw(
            db, uid, password, 'product.template', 'write', [
                [producto_id[0]['id']], vals])

print("Finaliza Proceso (Productos)...")
