#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from k8s.models.service import Service, ServicePort, ServiceSpec

LOG = logging.getLogger(__name__)


def deploy_service(app_spec, selector, labels):
    LOG.info("Creating/updating service for %s with labels: %s", app_spec.name, labels)
    ports = [_make_service_port(port_spec) for port_spec in app_spec.ports]
    try:
        svc = Service.get(app_spec.name, app_spec.namespace)
        ports = _merge_ports(svc.spec.ports, ports)
    except NotFound:
        pass
    service_name = app_spec.name
    metadata = ObjectMeta(name=service_name, namespace=app_spec.namespace, labels=labels)
    spec = ServiceSpec(selector=selector, ports=ports, type="NodePort")
    svc = Service.get_or_create(metadata=metadata, spec=spec)
    svc.save()


def _merge_ports(existing_ports, wanted_ports):
    existing = {port.name: port for port in existing_ports}
    for port in wanted_ports:
        existing_port = existing.get(port.name)
        if existing_port:
            port.nodePort = existing_port.nodePort
    return wanted_ports


def _make_service_port(port_spec):
    return ServicePort(
        protocol='TCP',
        name=port_spec.name,
        port=port_spec.port,
        targetPort=port_spec.target_port)
