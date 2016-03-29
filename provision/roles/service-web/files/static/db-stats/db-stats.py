#!/usr/bin/env python

import os
import socket
import psycopg2


if os.path.exists("./db-stats.conf"):
    CFG = open('./db-stats.conf', 'r').read().split(":")
else:
    CFG = open('/etc/db-stats.conf', 'r').read().split(":")


def get_stats():
    output = "DATABASE: {}\n".format(CFG[0])
    conn = psycopg2.connect(
                dbname=CFG[0],
                user=CFG[1],
                password=CFG[2],
                host=CFG[3]
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT
            nspname || '.' || relname,
            pg_size_pretty(pg_relation_size(C.oid))
        FROM pg_class C
        LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
        WHERE nspname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY pg_relation_size(C.oid) DESC
        LIMIT 20;
    """)
    recs = cur.fetchall()
    for rec in recs:
        output += " * {0} - {1}\n".format(*rec)

    output += "\nResponse from: {}\n".format(socket.gethostname())
    conn.close()

    return str(output)


def application(environ, start_response):
    response = get_stats()
    response_headers = [
        ('Content-type', 'text/plain'),
        ('Content-Length', str(len(response)))
    ]

    status = '200 OK'
    start_response(status, response_headers)
    return [response]


if __name__ == "__main__":
    print get_stats()


# vim: set ts=8 sts=4 sw=4 et:
