#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xmlrpc.client
import csv

host = 'http://localhost:9001'
db = 'prueba_pilotos_productos_limpia'
user = 'dmpineda@conalquipo.com'
password = 'admin'

sock_common = xmlrpc.client.ServerProxy('{0}/xmlrpc/common'.format(host))
uid = sock_common.login(db, user, password)
sock = xmlrpc.client.ServerProxy('{0}/xmlrpc/object'.format(host))

if not uid:
    print("Credenciales incorrectas")
    exit()

FLOTA = 'flota.csv'
Flota = csv.DictReader(open(FLOTA), delimiter='|')

print("Iniciando Proceso (Flota)...")

c = 1
for row in Flota:
    c += 1

    brand_id = sock.execute_kw(
        db, uid, password, 'fleet.vehicle.model.brand', 'search_read', [
            [['name', '=', row['MARCA'].strip()]]],
        {'fields': ['id']})

    model_id = sock.execute_kw(
        db, uid, password, 'fleet.vehicle.model', 'search_read', [
            [['name', '=', row['MODELO'].strip()]]],
        {'fields': ['id']})

    if not brand_id:
        vals = {
            'name': row['MARCA'].strip(),
        }
        sock.execute_kw(
            db, uid, password, 'fleet.vehicle.model.brand', 'create', [vals])

    if not model_id:

        brand_id = sock.execute_kw(
            db, uid, password, 'fleet.vehicle.model.brand', 'search_read', [
                [['name', '=', row['MARCA'].strip()]]],
            {'fields': ['id']})

        # Crear modelo nuevo
        message = "Linea {0} --> Creando modelo: {1}".format(
            c, row['MODELO'].strip())

        print(message)

        vals = {
            'name': row['MODELO'].strip(),
            'brand_id': brand_id[0]['id'],
        }
        model_id = sock.execute_kw(
            db, uid, password, 'fleet.vehicle.model', 'create', [vals])

        vals = {
            'model_id': model_id,
            'license_plate': row['MATRICULA'].strip(),
            'num_motor': row['SERIAL DEL MOTOR'].strip(),
            'model_year': row['ANO MODELO'].strip(),
            'capacity': row['CAPACIDAD'].strip(),
            'seats': row['N ASIENTOS'].strip(),
            'doors': row['N PUERTAS'].strip(),
            'color': row['COLOR'].strip(),
        }

        sock.execute_kw(
            db, uid, password, 'fleet.vehicle', 'create', [vals])

print("Finaliza Proceso finalizado...")
