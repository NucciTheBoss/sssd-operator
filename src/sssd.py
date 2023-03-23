#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provides sssd class to control sssd."""

import base64
import logging
import os
import subprocess

from charms.operator_libs_linux.v0 import apt
from charms.operator_libs_linux.v1 import systemd

logger = logging.getLogger(__name__)


def __getattr__(prop: str):
    if prop == "available":
        try:
            apt.DebianPackage.from_installed_package("sssd-ldap")
            apt.DebianPackage.from_installed_package("ldap-utils")
            return True
        except apt.PackageNotFoundError as e:
            logger.debug(f"{e.message.split()[-1]} is not installed...")
            return False
    elif prop == "running":
        if not systemd.service_running("sssd"):
            return False
        return True
    raise AttributeError(f"Module {__name__!r} has no property {prop!r}")


def _save(data: str, path: str) -> None:
    """Decode base64 string and writes to path.

    Args:
        data: Data to save.
        path: Location to save data to.
    """
    data = base64.b64decode(data.encode("utf-8"))
    with open(path, "wb") as f:
        f.write(data)


def disable() -> None:
    """Disable services."""
    systemd.service_pause("sssd")


def enable() -> None:
    """Enable services."""
    systemd.service_resume("sssd")


def install() -> None:
    """Install using charmlib apt."""
    try:
        apt.update()
        apt.add_package("ldap-utils")
        apt.add_package("sssd-ldap")
    except apt.PackageNotFoundError as e:
        logger.error("a specified package not found in package cache or on system")
        raise e
    except apt.PackageError as e:
        logger.error("Could not install packages.")
        raise e


def remove() -> None:
    """Remove packages."""
    try:
        apt.remove_package("ldap-utils")
        apt.remove_package("sssd-ldap")
    except apt.PackageNotFoundError as e:
        logger.error("a specified package to remove is not found in package cache or on system")
        raise e


def restart() -> None:
    """Restart servers/services."""
    systemd.service_restart("sssd")


def save_ca_cert(ca_cert: str) -> None:
    """Save CA certificate.

    Args:
        ca_cert: CA certificate.
    """
    cacert_path = "/etc/ssl/certs/mycacert.crt"
    _save(ca_cert, cacert_path)

    try:
        subprocess.run(
            ["update-ca-certificates"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"{e} Reason:\n{e.stderr}")


def save_conf(sssd_conf: str) -> None:
    """Save sssd conf.

    Args:
        sssd_conf: SSSD configuration file.
    """
    sssd_conf_path = "/etc/sssd/sssd.conf"
    # Decode base64 string and writes to path
    _save(sssd_conf, sssd_conf_path)
    # Change file ownership and permissions
    os.chown(sssd_conf_path, 0, 0)
    os.chmod(sssd_conf_path, 0o600)
    systemd.service_restart("sssd")


def start() -> None:
    """Start services."""
    systemd.service_start("sssd")


def stop() -> None:
    """Stop services."""
    systemd.service_stop("sssd")
