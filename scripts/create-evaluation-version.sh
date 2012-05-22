#!/bin/bash
../../bin/python ../roadmap/manage.py syncdb
../../bin/python ../roadmap/manage.py migrate ledger
../../bin/python ../roadmap/manage.py migrate reversion