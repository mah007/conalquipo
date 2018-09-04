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

EMPLEADOS = 'empleados.csv'
Empleados = csv.DictReader(open(EMPLEADOS), delimiter='|')

print("Iniciando Proceso (Empleados)...")

c = 1
for row in Empleados:
    c += 1

    employee_id = sock.execute_kw(
        db, uid, password, 'hr.employee', 'search_read', [
            [['name', '=', row['Employee'].strip()]]],
        {'fields': ['id']})

    if not employee_id:

        # Crear empleado nuevo

        message = "Linea {0} --> Creando empleado: {1}".format(
            c, row['Employee'].strip())

        print(message)

        vals = {
            'name': row['Employee'].strip(),
            'employee_code': row['Code'].strip(),
        }

        employee = sock.execute_kw(
            db, uid, password, 'hr.employee', 'create', [vals])

        user_id = sock.execute_kw(
            db, uid, password, 'res.users', 'search_read', [
                [['login', '=', row['User'].strip()]]],
            {'fields': ['id']})

        if user_id:
            vals_employee = {
                'employee_ids': [(4, employee)]
            }

            sock.execute_kw(
                db, uid, password, 'res.users', 'write', [
                    [user_id[0]['id']], vals_employee])
        else:
            vals = {
                'login': row['User'].strip(),
                'lastname': row['User'].strip(),
            }

            user = sock.execute_kw(
                db, uid, password, 'res.users', 'create', [vals])

            vals_employee = {
                'employee_ids': [(4, employee)]
            }

            sock.execute_kw(
                db, uid, password, 'res.users', 'write', [
                    [user], vals_employee])
    else:

        # Editar empleado

        message = "Linea {0} --> Editando empleados: {1}".format(
            c, row['Employee'].strip())

        print(message)

        vals = {
            'name': row['Employee'].strip(),
            'employee_code': row['Code'].strip(),
        }

        sock.execute_kw(
            db, uid, password, 'hr.employee', 'write', [
                [employee_id[0]['id']], vals])

        user_id = sock.execute_kw(
            db, uid, password, 'res.users', 'search_read', [
                [['login', '=', row['User'].strip()]]],
            {'fields': ['id']})

        if user_id:
            vals_employee = {
                'employee_ids': [(4, employee_id[0]['id'])]
            }

            sock.execute_kw(
                db, uid, password, 'res.users', 'write', [
                    [user_id[0]['id']], vals_employee])
        else:
            vals = {
                'login': row['User'].strip(),
                'lastname': row['User'].strip(),
            }

            user = sock.execute_kw(
                db, uid, password, 'res.users', 'create', [vals])

            vals_employee = {
                'employee_ids': [(4, employee_id[0]['id'])]
            }

            sock.execute_kw(
                db, uid, password, 'res.users', 'write', [
                    [user], vals_employee])

print("Finaliza Proceso (Empleados)...")
