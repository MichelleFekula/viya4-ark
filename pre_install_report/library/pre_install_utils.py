#!/usr/bin/env python3
####################################################################
# ### pre_install_check permissions.py                                 ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

from subprocess import CalledProcessError
import os

from pre_install_report.library.utils import viya_constants
from viya_arkcd_library.k8s.sas_kubectl_interface import KubectlInterface, KubernetesApiResources
from viya_arkcd_library.logging import ViyaARKCDLogger


class PreCheckUtils(object):
    """
    A PreCheckUtils encapslates the functions that use KubectlInterface to retrive information
    from a cluster

    """
    def __init__(self, params):
        """
                Constructor for PrecheckUtils object.
        """
        self.data = None
        self._kubectl: KubectlInterface = params.get(viya_constants.KUBECTL)
        self.sas_logger: ViyaARKCDLogger = params.get("logger")
        self.logger = self.sas_logger.get_logger()
        self.logger.info("PreCheckUtils ")

    def deploy_manifest_file(self, action, file_name):
        """
        Apply/delete specified manifest in a namespace and return the return code.
        action: indicate apply or delete of file
        file_name: yaml file to apply/delete with kubectl
        return:  kubectl rc
        """
        rc = 0
        data = ''
        error_msg = ''
        file_path = self._get_filepath(file_name)
        try:
            data = self._kubectl.manage_resource(action, file_path, False)
        except CalledProcessError as cpe:
            rc = cpe.returncode
            error_msg = str(cpe.output)
            self.logger.error("deploy_manifest_file rc {} action {} filepath error_msg {}".format(str(rc), action,
                              file_path, error_msg))
            return rc

        self.logger.info("deploy_manifest_file {} rc {} action {} filepath {} data{}".format(rc, str(rc), action,
                         file_path, str(data)))
        return rc

    def do_cmd(self, test_cmd):
        """
        Run the specified kubectl command and return the output. Used to execute commands such as
        rollout status <deployment.v1.apps/hello-world
        scale --replicas=2 deployment/hello-world
        wait --for=delete pod -l app=hello-world-pod

        cmd: kubectl command to be executed
        return:  kubectl rc,  output
        """
        try:
            data = self._kubectl.do(test_cmd, False)

            self.logger.info("do_cmd " + ' rc = 0' + test_cmd +
                             ' data = ' + str(data))
            return 0
        except CalledProcessError as e:
            data = e.output
            self.logger.error("do_cmd " + ' rc = ' + str(e.returncode) + test_cmd +
                              ' data = ' + str(data))
            return e.returncode

    def get_rbac_group_cmd(self):
        """
        Check if for Role and Rolebinding api groups.

        cmd: kubectl command to retrieve api_resources
        return:  True if both Role and RoleBinding kinds have an api_group
        """
        role = None
        rolebinding = None
        try:
            data: KubernetesApiResources = self._kubectl.api_resources(False)
            role = data.get_api_group("Role")
            rolebinding = data.get_api_group("RoleBinding")
        except CalledProcessError as e:
            self.logger.exception("get_rbac_group_cmd  rc {}" + e.returncode)
            return False
        if role is None:
            return False
        if rolebinding is None:
            return False

        self.logger.info("found Role and RoleBinding api groups")

        return True

    def can_i(self, test_cmd):
        """
        Run the specified can-i command in designated namespace

        cmd: kubectl can-icommand to be executed
        return:  True if action is permitted. If not, return false
        """
        try:
            allowed = self._kubectl.can_i(test_cmd, False, False)
            self.logger.info('can -i ' + str(allowed) + "  can-i " + test_cmd)
            return allowed
        except CalledProcessError as cpe:
            self.logger.info('can -i return False' + "  can-i " + 'return code = ' +
                             cpe.returncode + " " + test_cmd)
            return False

    def _get_filepath(self, file_name):
        """
        Assemble and return path for specied file in project library

        file_name: name of file in project library/utils
        return:  relative path to specified file.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "utils" + os.sep + file_name)
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        # file_path = os.path.join(current_dir, file_name)
        return file_path
