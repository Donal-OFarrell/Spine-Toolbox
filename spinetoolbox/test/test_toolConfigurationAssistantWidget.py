######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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
import logging
import sys
from PySide2.QtWidgets import QApplication, QWidget
from widgets.tool_configuration_assistant_widget import ToolConfigurationAssistantWidget

# noinspection PyUnusedLocal,DuplicatedCode
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
        with mock.patch("widgets.tool_configuration_assistant_widget.SpineModelConfigurationAssistant"):
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
        with mock.patch.object(self.widget, "add_spine_model_error_msg") as mock_method:
            self.widget.configure_spine_model()
        mock_method.assert_called_once()
        self.assertIsNone(self.widget.q_process)

    def test_invalid_julia_version(self):
        """Test that an error message is shown if julia version is below 1.1.0."""
        self.assistant.julia_version.return_value = "1.0.0"
        with mock.patch.object(self.widget, "add_spine_model_error_msg") as mock_method:
            self.widget.configure_spine_model()
        mock_method.assert_called_once()
        self.assertIsNone(self.widget.q_process)

    def test_valid_julia_version(self):
        """Test that the spine model version check is started if julia version is equal to 1.1.0."""
        self.assistant.julia_version.return_value = "1.1.0"
        mock_process = mock.Mock()
        self.assistant.spine_model_version_check.return_value = mock_process
        self.widget.configure_spine_model()
        self.assistant.spine_model_version_check.assert_called_once()
        self.assertEqual(self.widget.q_process, mock_process)

    def test_spine_model_installation_aborted(self):
        """Test that the spine model installation is aborted by the user."""
        with mock.patch.object(self.widget, "q_process") as mock_process, mock.patch.object(
            self.widget, "get_permission"
        ) as mock_get_permission, mock.patch.object(self.widget, "add_spine_model_error_msg") as mock_add_err_msg:
            mock_process.process_failed_to_start = False
            mock_get_permission.side_effect = lambda x, y: False
            self.widget._handle_spine_model_version_check_finished(1)
        mock_get_permission.assert_called_once()
        mock_add_err_msg.assert_called_once()
        self.assertIsNone(self.widget.q_process)

    def test_spine_model_installation_accepted(self):
        """Test that the spine model installation is accepted by the user."""
        mock_install_process = mock.Mock()
        self.assistant.install_spine_model.return_value = mock_install_process
        self.widget.q_process = mock.Mock()
        self.widget.q_process.process_failed_to_start = False
        with mock.patch.object(self.widget, "get_permission") as mock_get_permission, mock.patch.object(
            self.widget, "add_spine_model_msg"
        ) as mock_add_msg:
            mock_get_permission.side_effect = lambda x, y: True
            self.widget._handle_spine_model_version_check_finished(1)
        mock_get_permission.assert_called_once()
        mock_add_msg.assert_called_once()
        self.assertEqual(self.widget.q_process, mock_install_process)


if __name__ == '__main__':
    unittest.main()