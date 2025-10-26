#!/bin/sh
set -e

make mig

exec "$@"
