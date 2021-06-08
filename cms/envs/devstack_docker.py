""" Overrides for Docker-based devstack. """

from .devstack import *  # pylint: disable=wildcard-import, unused-wildcard-import
LMS_ROOT_URL = "http://192.168.0.149:18000"
DISCOVERY_ROOT_URL = 'http://192.168.0.149:18381'
TEST_VAL = 'devstack_docker'
