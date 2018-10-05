#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xmlrpc.client
import csv
import ast
import codecs

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

PRODUCTOS = 'almacenables.csv'
Productos = csv.DictReader(codecs.open(PRODUCTOS), delimiter='|')

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
    # COMPRA
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

    # VENTA
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

    # UNIDAD
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

    # UBICACIONES
    origin_location_id = sock.execute_kw(
        db, uid, password, 'stock.location', 'search_read', [
            [['complete_name',
              '=', row['Ubicacion origen'].strip()]]], {
                  'fields': ['id', 'name', 'complete_name']})

    location_id = sock.execute_kw(
        db, uid, password, 'stock.location', 'search_read', [
            [['complete_name',
              '=', row[
                  'Ubicacion origen'].strip()]]], {'fields': ['id']})

    # PRODUCTOS
    producto_id = sock.execute_kw(
        db, uid, password, 'product.template', 'search_read', [
            [['default_code', '=', row['Referencia interna'].strip()]]],
        {'fields': ['id']})

    # REPOSICIONES
    rep_producto_id = False
    if row['fact-cargo por reabastecimiento']:
        rep_producto_id = sock.execute_kw(
            db, uid, password, 'product.template', 'search_read', [
                [['name', '=', row[
                    'fact-cargo por reabastecimiento'].strip()]]],
            {'fields': ['id']})
        if rep_producto_id:
            rep_producto_id = rep_producto_id[0]['id']

    if not producto_id:

        ''' Crear producto nuevo '''

        message = "Linea {0} --> Creando producto: {1}".format(
            c, row['Producto'].strip())

        print(message)
        vals = {}

        if row['No Mecanico'].strip() != "True":
            vals = {
                'name': row['Producto'].strip(),
                'standard_price': row['Coste'].strip(),
                'list_price': row[
                    'Precio de venta por unidad de medida'].strip(),
                'categ_id': categ_id,
                'uom_po_id': uom_po_id,
                'sale_uom': sale_uom,
                'uom_id': uom_id,
                'default_code': row['Referencia interna'].strip(),
                'type': 'product',
                'active': True,
                'sale_ok': ast.literal_eval(
                    row['Puede ser vendido'].strip()),
                'purchase_ok': ast.literal_eval(
                    row['Puede ser comprado'].strip()),
                'rental': ast.literal_eval(row[
                    'Puede ser alquilado'].strip()),
                'components': ast.literal_eval(
                    row['Tiene componentes'].strip()),
                'non_mech': ast.literal_eval(
                    row['No Mecanico'].strip()),
                'multiples_uom': ast.literal_eval(
                    row['Tiene multiples unidades'].strip()),
                'is_operated': ast.literal_eval(
                    row['inv-es operado'].strip()),
                'product_origin': origin_location_id[0]['id'],
                'location_id': location_id[0]['id'],
                'color': row['Estado'].strip(),
                'replenishment_charge': rep_producto_id,
                'description_pickingout': row[
                    'Notas para pedidos de entrega'].strip(),
                'layout_sec_id': section_id,
                'min_qty_rental': row['cantidad por defecto']
            }
        else:
            vals = {
                'name': row['Producto'].strip(),
                'standard_price': row['Coste'].strip(),
                'list_price': row[
                    'Precio de venta por unidad de medida'].strip(),
                'categ_id': categ_id,
                'uom_po_id': uom_po_id,
                'sale_uom': sale_uom,
                'uom_id': uom_id,
                'default_code': row['Referencia interna'].strip(),
                'type': 'product',
                'active': True,
                'sale_ok': ast.literal_eval(
                    row['Puede ser vendido'].strip()),
                'purchase_ok': ast.literal_eval(
                    row['Puede ser comprado'].strip()),
                'rental': ast.literal_eval(row[
                    'Puede ser alquilado'].strip()),
                'components': ast.literal_eval(
                    row['Tiene componentes'].strip()),
                'non_mech': ast.literal_eval(
                    row['No Mecanico'].strip()),
                'multiples_uom': ast.literal_eval(
                    row['Tiene multiples unidades'].strip()),
                'is_operated': ast.literal_eval(
                    row['inv-es operado'].strip()),
                'product_origin': origin_location_id[0]['id'],
                'replenishment_charge': rep_producto_id,
                'description_pickingout': row[
                    'Notas para pedidos de entrega'].strip(),
                'layout_sec_id': section_id,
                'min_qty_rental': row['cantidad por defecto'],
                'location_id': False,
                'color': False,
                'state_id': False
            }

        product_id = sock.execute_kw(
            db, uid, password, 'product.template', 'create', [vals])

        # AÑADIR CANTIDAAD A MANO
        pro_id = sock.execute_kw(
            db, uid, password, 'product.product', 'search_read', [
                [['product_tmpl_id', '=', product_id]]],
            {'fields': ['id']})

        vals_qty = {
            'product_id': pro_id[0]['id'],
            'location_id': origin_location_id[0]['id'],
            'new_quantity': row['cantidad a mano']
        }

        wizard = sock.execute_kw(
            db, uid, password, 'stock.change.product.qty', 'create', [
                vals_qty])

        sock.execute_kw(
            db, uid, password,
            'stock.change.product.qty', 'change_product_qty', [
                wizard])

        # Add to public pricelist ###################################

        pricelist_id = sock.execute_kw(
            db, uid, password, 'product.pricelist', 'search_read', [
                [['name', '=', 'Pricelist - Commercial']]],
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
    else:

        ''' Editar producto '''

        message = "Linea {0} --> Editando producto: {1}".format(
            c, row['Producto'].strip())

        print(message)
        vals = {}
        # RUTAS
        warehouse = sock.execute_kw(
            db, uid, password, 'stock.warehouse', 'search_read', [
                [['lot_stock_id', '=', origin_location_id[0]['id']]]],
            {'fields': ['id']})

        routes = []

        routes1 = sock.execute_kw(
            db, uid, password, 'stock.location.route', 'search', [
                [['supplied_wh_id', '=', warehouse[0]['id']]]])

        routes2 = sock.execute_kw(
            db, uid, password, 'stock.location.route', 'search', [
                [['supplier_wh_id', '=', warehouse[0]['id']]]])

        routes3 = sock.execute_kw(
            db, uid, password, 'stock.location.route', 'search', [
                [['name', '=', 'Make To Order + Make To Stock']]])

        routes4 = sock.execute_kw(
            db, uid, password, 'stock.location.route', 'search', [
                [['name', '=', 'Make To Order']]])

        routes = routes1 + routes2 + routes3 + routes4

        if routes:
            routes_all = [(6, 0, routes)]

        if row['No Mecanico'].strip() != "True":
            vals = {
                'name': row['Producto'].strip(),
                'standard_price': row['Coste'].strip(),
                'list_price': row[
                    'Precio de venta por unidad de medida'].strip(),
                'categ_id': categ_id,
                'uom_po_id': uom_po_id,
                'sale_uom': sale_uom,
                'uom_id': uom_id,
                'default_code': row['Referencia interna'].strip(),
                'type': 'product',
                'active': True,
                'sale_ok': ast.literal_eval(
                    row['Puede ser vendido'].strip()),
                'purchase_ok': ast.literal_eval(
                    row['Puede ser comprado'].strip()),
                'rental': ast.literal_eval(row[
                    'Puede ser alquilado'].strip()),
                'components': ast.literal_eval(
                    row['Tiene componentes'].strip()),
                'non_mech': ast.literal_eval(
                    row['No Mecanico'].strip()),
                'multiples_uom': ast.literal_eval(
                    row['Tiene multiples unidades'].strip()),
                'is_operated': ast.literal_eval(
                    row['inv-es operado'].strip()),
                'product_origin': origin_location_id[0]['id'],
                'location_id': location_id[0]['id'],
                'color': row['Estado'].strip(),
                'replenishment_charge': rep_producto_id,
                'description_pickingout': row[
                    'Notas para pedidos de entrega'].strip(),
                'layout_sec_id': section_id,
                'min_qty_rental': row['cantidad por defecto'],
                'route_ids': routes_all
            }
        else:
            vals = {
                'name': row['Producto'].strip(),
                'standard_price': row['Coste'].strip(),
                'list_price': row[
                    'Precio de venta por unidad de medida'].strip(),
                'categ_id': categ_id,
                'uom_po_id': uom_po_id,
                'sale_uom': sale_uom,
                'uom_id': uom_id,
                'default_code': row['Referencia interna'].strip(),
                'type': 'product',
                'active': True,
                'sale_ok': ast.literal_eval(
                    row['Puede ser vendido'].strip()),
                'purchase_ok': ast.literal_eval(
                    row['Puede ser comprado'].strip()),
                'rental': ast.literal_eval(row[
                    'Puede ser alquilado'].strip()),
                'components': ast.literal_eval(
                    row['Tiene componentes'].strip()),
                'non_mech': ast.literal_eval(
                    row['No Mecanico'].strip()),
                'multiples_uom': ast.literal_eval(
                    row['Tiene multiples unidades'].strip()),
                'is_operated': ast.literal_eval(
                    row['inv-es operado'].strip()),
                'product_origin': origin_location_id[0]['id'],
                'replenishment_charge': rep_producto_id,
                'description_pickingout': row[
                    'Notas para pedidos de entrega'].strip(),
                'layout_sec_id': section_id,
                'min_qty_rental': row['cantidad por defecto'],
                'location_id': False,
                'color': False,
                'state_id': False,
                'route_ids': routes_all
            }

        sock.execute_kw(
            db, uid, password, 'product.template', 'write', [
                [producto_id[0]['id']], vals])

        # AÑADIR CANTIDAD A MANO
        # pro_id = sock.execute_kw(
        #     db, uid, password, 'product.product', 'search_read', [
        #         [['product_tmpl_id', '=', producto_id[0]['id']]]],
        #     {'fields': ['id']})

        # vals_qty = {
        #     'product_id': pro_id[0]['id'],
        #     'location_id': origin_location_id[0]['id'],
        #     'new_quantity': row['cantidad a mano']
        # }

        # wizard = sock.execute_kw(
        #     db, uid, password, 'stock.change.product.qty', 'create', [
        #         vals_qty])

        # sock.execute_kw(
        #     db, uid, password,
        #     'stock.change.product.qty', 'change_product_qty', [
        #         wizard])

print("Finaliza Proceso (Productos)...")
