#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xmlrpc.client
import csv

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

ZONAS = 'zonas.csv'
Zonas = csv.DictReader(open(ZONAS), delimiter='|')

print("Iniciando Proceso (Zonas)...")

c = 1
for row in Zonas:
    c += 1

    print(c)
    zones_id = sock.execute_kw(
        db, uid, password, 'delivery.carrier', 'search_read', [
            [['name', '=', row['NOMBRE'].strip()]]],
        {'fields': ['id']})

    product_id = sock.execute_kw(
        db, uid, password, 'product.product', 'search_read', [
            [['default_code', '=', row['PRODUCTO DE ENVÍO']]]],
        {'fields': ['id']})

    vehicle_id = sock.execute_kw(
        db, uid, password, 'fleet.vehicle', 'search_read', [
            [['license_plate', '=', row['MATRICULA'][-6:].strip()]]],
        {'fields': ['id']})

    if vehicle_id:
        if not zones_id:

            # Crear modelo nuevo
            message = "Linea {0} --> Creando zona: {1}".format(
                c, row['NOMBRE'].strip())

            print(message)

            vals = {
                'name': row['NOMBRE'].strip(),
                'delivery_type': row['DELIVERY_TYPE'].strip(),
                'price_type': row['PRICE_TYPE'].strip(),
                'product_id': product_id[0]['id'],
                'free_over': False,
            }

            new_zones = sock.execute_kw(
                db, uid, password, 'delivery.carrier', 'create', [vals])
                
            vals2 = {
                'delivery_carrier_id': new_zones,
                'cost': row['PRECIOS'],
                'product_id': product_id[0]['id'],
                'vehicle': vehicle_id[0]['id']
            }
            sock.execute_kw(
                db, uid, password, 'delivery.carrier.cost', 'create', [vals2])
        else:
            vals2 = {
                'delivery_carrier_id': zones_id[0]['id'],
                'cost': row['PRECIOS'],
                'product_id': product_id[0]['id'],
                'vehicle': vehicle_id[0]['id']
            }
            sock.execute_kw(
                db, uid, password, 'delivery.carrier.cost', 'create', [vals2])

print("Finaliza Proceso finalizado...")
