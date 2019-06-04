"""Build pods into static deployments."""

import os
import click
from grow.commands import result
from grow.commands import shared
from grow.common import base_config
from grow.common import rc_config
from grow.pod import pod as grow_pod
from grow.sdk import installer
from grow.sdk import installers


CFG = rc_config.RC_CONFIG.prefixed('grow.install')


# pylint: disable=too-many-locals
@click.command()
@shared.pod_path_argument
def install(pod_path):
    """Installs local dependencies for such as extensions, npm, yarn, etc."""
    cmd_result = result.CommandResult()

    root_path = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = grow_pod.Pod(root_path)

    config = base_config.BaseConfig()
    built_in_installers = []
    for installer_class in installers.BUILT_IN_INSTALLERS:
        built_in_installers.append(installer_class(pod, config))
    grow_installer = installer.Installer(built_in_installers, pod)
    grow_installer.run_installers()

    return cmd_result