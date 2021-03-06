######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for ToolConfigurationAssistantWidget class.

:author: M. Marin (KTH)
:date:   3.9.2019
"""

import unittest
from unittest import mock
from unittest.mock import patch
import logging
import sys
from PySide2.QtWidgets import QApplication, QWidget
from PySide2.QtCore import Qt
from PySide2.QtGui import QCursor
from spinetoolbox.widgets.tool_configuration_assistant_widget import ToolConfigurationAssistantWidget


class TestToolConfigurationAssistantWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    def setUp(self):
        """Overridden method. Runs before each test."""
        with patch("spinetoolbox.widgets.tool_configuration_assistant_widget.SpineModelConfigurationAssistant"):
            self.widget = ToolConfigurationAssistantWidget(QWidget(), autorun=False)
            self.assistant = self.widget.spine_model_config_asst

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.widget.deleteLater()
        self.widget = None

    def test_unknown_julia_version(self):
        """Test that an error message is shown if julia version is unknown."""
        self.assistant.julia_version.return_value = None
        with patch.object(self.widget, "add_spine_model_error_msg") as mock_method:
            self.widget.configure_spine_model()
        mock_method.assert_called_once()
        self.assertIsNone(self.widget.prox_exec_mngr)

    def test_invalid_julia_version(self):
        """Test that an error message is shown if julia version is below 1.1.0."""
        self.assistant.julia_version.return_value = "1.0.0"
        with patch.object(self.widget, "add_spine_model_error_msg") as mock_method:
            self.widget.configure_spine_model()
        mock_method.assert_called_once()
        self.assertIsNone(self.widget.prox_exec_mngr)

    def test_valid_julia_version(self):
        """Test that the spine model version check is started if julia version is equal to 1.1.0."""
        self.assistant.julia_version.return_value = "1.1.0"
        mock_process = mock.Mock()
        self.assistant.spine_model_version_check.return_value = mock_process
        self.widget.configure_spine_model()
        self.assistant.spine_model_version_check.assert_called_once()
        self.assertEqual(self.widget.prox_exec_mngr, mock_process)

    def test_spine_model_installation_is_cancelled(self):
        """Test that the spine model installation is cancelled by the user."""
        with patch.object(self.widget, "prox_exec_mngr") as mock_process, patch.object(
            self.widget, "get_permission"
        ) as mock_get_permission, patch.object(self.widget, "add_spine_model_error_msg") as mock_add_err_msg:
            mock_process.process_failed_to_start = False
            mock_get_permission.side_effect = lambda x, y: False
            self.widget._handle_spine_model_version_check_finished(1)
        mock_get_permission.assert_called_once()
        mock_add_err_msg.assert_called_once()
        self.assertIsNone(self.widget.prox_exec_mngr)

    def test_spine_model_installation_is_accepted(self):
        """Test that the spine model installation is accepted by the user."""
        mock_process = mock.Mock()
        self.assistant.install_spine_model.return_value = mock_process
        self.widget.prox_exec_mngr = mock.Mock()
        self.widget.prox_exec_mngr.process_failed_to_start = False
        with patch.object(self.widget, "get_permission") as mock_get_permission, patch.object(
            self.widget, "add_spine_model_msg"
        ) as mock_add_msg:
            mock_get_permission.side_effect = lambda x, y: True
            self.widget._handle_spine_model_version_check_finished(1)
        mock_get_permission.assert_called_once()
        mock_add_msg.assert_called_once()
        self.assertEqual(self.widget.prox_exec_mngr, mock_process)

    def test_py_call_program_check_starts_if_spine_model_was_installed(self):
        """Test that the PyCall program check is started if Spine Model was installed."""
        mock_process = mock.Mock()
        self.assistant.py_call_program_check.return_value = mock_process
        self.widget.prox_exec_mngr = mock.Mock()
        self.widget.prox_exec_mngr.process_failed_to_start = False
        with patch.object(self.widget, "add_spine_model_msg") as mock_add_msg:
            self.widget._handle_spine_model_version_check_finished(0)
        mock_add_msg.assert_called_once()
        self.assertEqual(self.widget.prox_exec_mngr, mock_process)

    def test_spine_model_installation_fails(self):
        """Test that the spine model installation fails."""
        with patch.object(self.widget, "prox_exec_mngr") as mock_process, patch.object(
            self.widget, "add_spine_model_error_msg"
        ) as mock_add_err_msg:
            mock_process.process_failed_to_start = False
            self.widget._handle_spine_model_installation_finished(1)
        mock_add_err_msg.assert_called_once()
        self.assertIsNone(self.widget.prox_exec_mngr)

    def test_py_call_program_check_starts_after_installing_spine_model(self):
        """Test that the PyCall program check is started after installing Spine Model."""
        mock_process = mock.Mock()
        self.assistant.py_call_program_check.return_value = mock_process
        self.widget.prox_exec_mngr = mock.Mock()
        self.widget.prox_exec_mngr.process_failed_to_start = False
        with patch.object(self.widget, "add_spine_model_success_msg") as mock_add_succ_msg:
            self.widget._handle_spine_model_installation_finished(0)
        mock_add_succ_msg.assert_called_once()
        self.assertEqual(self.widget.prox_exec_mngr, mock_process)

    def test_py_call_installation_is_cancelled(self):
        """Test that PyCall installation is cancelled by the user."""
        with patch.object(self.widget, "prox_exec_mngr") as mock_process, patch.object(
            self.widget, "get_permission"
        ) as mock_get_permission, patch.object(self.widget, "add_spine_model_error_msg") as mock_add_err_msg:
            mock_process.process_failed_to_start = False
            mock_get_permission.side_effect = lambda x, y: False
            self.widget._handle_py_call_program_check_finished(1)
        mock_get_permission.assert_called_once()
        mock_add_err_msg.assert_called_once()
        self.assertIsNone(self.widget.prox_exec_mngr)

    def test_py_call_installation_is_accepted(self):
        """Test that PyCall installation is accepted by the user."""
        mock_process = mock.Mock()
        self.assistant.install_py_call.return_value = mock_process
        self.widget.prox_exec_mngr = mock.Mock()
        self.widget.prox_exec_mngr.process_failed_to_start = False
        with patch.object(self.widget, "get_permission") as mock_get_permission, patch.object(
            self.widget, "add_spine_model_msg"
        ) as mock_add_msg:
            mock_get_permission.side_effect = lambda x, y: True
            self.widget._handle_py_call_program_check_finished(1)
        mock_get_permission.assert_called_once()
        mock_add_msg.assert_called_once()
        self.assertEqual(self.widget.prox_exec_mngr, mock_process)

    def test_py_call_reconfiguration_is_cancelled(self):
        """Test that PyCall reconfiguration is cancelled by the user."""
        with patch.object(self.widget, "prox_exec_mngr") as mock_process, patch.object(
            self.widget, "get_permission"
        ) as mock_get_permission, patch.object(self.widget, "add_spine_model_msg") as mock_add_msg, patch.object(
            self.widget, "add_spine_model_error_msg"
        ) as mock_add_err_msg:
            mock_process.process_failed_to_start = False
            mock_process.output = "badpython"
            mock_get_permission.side_effect = lambda x, y: False
            self.widget._handle_py_call_program_check_finished(0)
        mock_get_permission.assert_called_once()
        mock_add_msg.assert_called_once()
        mock_add_err_msg.assert_called_once()
        self.assertIsNone(self.widget.prox_exec_mngr)

    def test_py_call_reconfiguration_is_accepted(self):
        """Test that PyCall reconfiguration is accepted by the user."""
        mock_process = mock.Mock()
        self.assistant.reconfigure_py_call.return_value = mock_process
        self.widget.prox_exec_mngr = mock.Mock()
        self.widget.prox_exec_mngr.process_failed_to_start = False
        self.widget.prox_exec_mngr.output = "badpython"
        with patch.object(self.widget, "get_permission") as mock_get_permission, patch.object(
            self.widget, "add_spine_model_msg"
        ) as mock_add_msg:
            mock_get_permission.side_effect = lambda x, y: True
            self.widget._handle_py_call_program_check_finished(0)
        mock_get_permission.assert_called_once()
        mock_add_msg.assert_called()
        self.assertEqual(self.widget.prox_exec_mngr, mock_process)

    def test_correct_py_call_configuration(self):
        """Test that process finishes successfully if PyCall configuration is correct."""
        with patch.object(self.widget, "prox_exec_mngr") as mock_process, patch.object(
            self.widget, "add_spine_model_success_msg"
        ) as mock_add_succ_msg:
            mock_process.process_failed_to_start = False
            mock_process.output = sys.executable
            self.widget._handle_py_call_program_check_finished(0)
        mock_add_succ_msg.assert_called_once()
        self.assertIsNone(self.widget.prox_exec_mngr)

    def test_py_call_installation_fails(self):
        """Test that PyCall installation fails."""
        with patch.object(self.widget, "prox_exec_mngr") as mock_process, patch.object(
            self.widget, "add_spine_model_error_msg"
        ) as mock_add_err_msg:
            mock_process.process_failed_to_start = False
            self.widget._handle_py_call_installation_finished(1)
        mock_add_err_msg.assert_called_once()
        self.assertIsNone(self.widget.prox_exec_mngr)

    def test_py_call_program_check_starts_after_installing_py_call(self):
        """Test that the PyCall program check is started after installing PyCall."""
        mock_process = mock.Mock()
        self.assistant.py_call_program_check.return_value = mock_process
        self.widget.prox_exec_mngr = mock.Mock()
        self.widget.prox_exec_mngr.process_failed_to_start = False
        with patch.object(self.widget, "add_spine_model_success_msg") as mock_add_succ_msg:
            self.widget._handle_py_call_installation_finished(0)
        mock_add_succ_msg.assert_called_once()
        self.assertEqual(self.widget.prox_exec_mngr, mock_process)

    def test_py_call_reconfiguration_fails(self):
        """Test that PyCall reconfiguration fails."""
        with patch.object(self.widget, "prox_exec_mngr") as mock_process, patch.object(
            self.widget, "add_spine_model_error_msg"
        ) as mock_add_err_msg:
            mock_process.process_failed_to_start = False
            self.widget._handle_py_call_reconfiguration_finished(1)
        mock_add_err_msg.assert_called_once()
        self.assertIsNone(self.widget.prox_exec_mngr)

    def test_py_call_reconfiguration_succeeds(self):
        """Test that process finishes successfully if PyCall reconfiguration succeeds."""
        with patch.object(self.widget, "prox_exec_mngr") as mock_process, patch.object(
            self.widget, "add_spine_model_success_msg"
        ) as mock_add_succ_msg:
            mock_process.process_failed_to_start = False
            self.widget._handle_py_call_reconfiguration_finished(0)
        mock_add_succ_msg.assert_called()
        self.assertIsNone(self.widget.prox_exec_mngr)

    def test_restore_override_cursor_at_close(self):
        """Test that no override cursor is set after closing the widget."""
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))
        self.widget.close()
        self.assertIsNone(QApplication.overrideCursor())


if __name__ == '__main__':
    unittest.main()
