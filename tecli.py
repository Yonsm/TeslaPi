#!/usr/bin/env python3
import json
import sys

from teslapi import TeslaPi

TESLAPI_VERSION = '1.0.1'


def usage():
    print("TeslaPi %s - Tesla API Service\n" % TESLAPI_VERSION)
    print("Usage: %s [email] [password]" % sys.argv[0])


if __name__ == '__main__':
    argc = len(sys.argv)
    api = TeslaPi(sys.argv[1] if argc > 1 else None, sys.argv[2] if argc > 2 else None)
    if not api.access_token:
        if argc < 3:
            usage()
        else:
            print('Login failed')
        exit(-1)

    if not api.vehicle_ids:
        print('No vehicles')
        exit(-2)

    data = api.vehicle_data(api.vehicle_ids[0])
    print(json.dumps(data, indent=2))
