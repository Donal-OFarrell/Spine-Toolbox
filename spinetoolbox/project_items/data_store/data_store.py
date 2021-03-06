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
Module for data store class.

:authors: P. Savolainen (VTT), M. Marin (KTH)
:date:   18.12.2017
"""

import os
import logging
from PySide2.QtCore import Slot, Qt
from PySide2.QtWidgets import QFileDialog, QApplication
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import spinedb_api
from spinetoolbox.project_item import ProjectItem, ProjectItemResource
from spinetoolbox.widgets.data_store_widget import DataStoreForm
from spinetoolbox.helpers import create_dir, busy_effect, serialize_path, deserialize_path
from .widgets.custom_menus import DataStoreContextMenu


class DataStore(ProjectItem):
    def __init__(self, name, description, x, y, toolbox, project, logger, url=None):
        """Data Store class.

        Args:
            name (str): Object name
            description (str): Object description
            x (float): Initial X coordinate of item icon
            y (float): Initial Y coordinate of item icon
            toolbox (ToolboxUI): QMainWindow instance
            project (SpineToolboxProject): the project this item belongs to
            logger (LoggerInterface): a logger instance
            url (str or dict): SQLAlchemy url
        """
        super().__init__(name, description, x, y, project, logger)
        if url is None:
            url = dict()
        if url and not isinstance(url["database"], str):
            url["database"] = deserialize_path(url["database"], self._project.project_dir)
        self._toolbox = toolbox
        self._url = self.parse_url(url)
        self._sa_url = None
        self.ds_view = None
        self._for_spine_model_checkbox_state = Qt.Unchecked
        # Make logs directory for this Data Store
        self.logs_dir = os.path.join(self.data_dir, "logs")
        try:
            create_dir(self.logs_dir)
        except OSError:
            self._logger.msg_error.emit(f"[OSError] Creating directory {self.logs_dir} failed. Check permissions.")

    @staticmethod
    def item_type():
        """See base class."""
        return "Data Store"

    @staticmethod
    def category():
        """See base class."""
        return "Data Stores"

    def parse_url(self, url):
        """Return a complete url dictionary from the given dict or string"""
        base_url = dict(dialect=None, username=None, password=None, host=None, port=None, database=None)
        if isinstance(url, dict):
            if "database" in url and url["database"] is not None:
                if url["database"].lower().endswith(".sqlite"):
                    # Convert relative database path back to absolute
                    abs_path = os.path.abspath(os.path.join(self._project.project_dir, url["database"]))
                    url["database"] = abs_path
            base_url.update(url)
        return base_url

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = super().make_signal_handler_dict()
        s[self._properties_ui.toolButton_ds_open_dir.clicked] = lambda checked=False: self.open_directory()
        s[self._properties_ui.pushButton_ds_view.clicked] = self.open_ds_view
        s[self._properties_ui.toolButton_open_sqlite_file.clicked] = self.open_sqlite_file
        s[self._properties_ui.pushButton_create_new_spine_db.clicked] = self.create_new_spine_database
        s[self._properties_ui.toolButton_copy_url.clicked] = self.copy_url
        s[self._properties_ui.comboBox_dialect.activated[str]] = self.refresh_dialect
        s[self._properties_ui.lineEdit_database.file_dropped] = self.set_path_to_sqlite_file
        s[self._properties_ui.lineEdit_username.editingFinished] = self.refresh_username
        s[self._properties_ui.lineEdit_password.editingFinished] = self.refresh_password
        s[self._properties_ui.lineEdit_host.editingFinished] = self.refresh_host
        s[self._properties_ui.lineEdit_port.editingFinished] = self.refresh_port
        s[self._properties_ui.lineEdit_database.editingFinished] = self.refresh_database
        return s

    def activate(self):
        """Load url into selections and connect signals."""
        self._properties_ui.label_ds_name.setText(self.name)
        self._properties_ui.checkBox_for_spine_model.setCheckState(self._for_spine_model_checkbox_state)
        self.load_url_into_selections()  # Do this before connecting signals or funny things happen
        super().connect_signals()

    def deactivate(self):
        """Disconnect signals."""
        self._for_spine_model_checkbox_state = self._properties_ui.checkBox_for_spine_model.checkState()
        if not super().disconnect_signals():
            logging.error("Item %s deactivation failed", self.name)
            return False
        return True

    def url(self):
        """Return the url attribute, for saving the project."""
        return self._url

    def _update_sa_url(self, log_errors=True):
        self._sa_url = self._make_url(log_errors=log_errors)

    @busy_effect
    def _make_url(self, log_errors=True):
        """Returns a sqlalchemy url from the current url attribute or None if not valid."""
        if not self._url:
            if log_errors:
                self._logger.msg_error.emit(
                    f"No URL specified for <b>{self.name}</b>. Please specify one and try again"
                )
            return None
        try:
            url_copy = dict(self._url)
            dialect = url_copy.pop("dialect")
            if not dialect:
                if log_errors:
                    self._logger.msg_error.emit(
                        f"Unable to generate URL from <b>{self.name}</b> selections: invalid dialect {dialect}. "
                        "<br>Please select a new dialect and try again."
                    )
                return None
            if dialect == 'sqlite':
                url = URL('sqlite', **url_copy)  # pylint: disable=unexpected-keyword-arg
            else:
                db_api = spinedb_api.SUPPORTED_DIALECTS[dialect]
                drivername = f"{dialect}+{db_api}"
                url = URL(drivername, **url_copy)  # pylint: disable=unexpected-keyword-arg
        except Exception as e:  # pylint: disable=broad-except
            # This is in case one of the keys has invalid format
            if log_errors:
                self._logger.msg_error.emit(
                    f"Unable to generate URL from <b>{self.name}</b> selections: {e} "
                    "<br>Please make new selections and try again."
                )
            return None
        if not url.database:
            if log_errors:
                self._logger.msg_error.emit(
                    f"Unable to generate URL from <b>{self.name}</b> selections: database missing. "
                    "<br>Please select a database and try again."
                )
            return None
        # Small hack to make sqlite file paths relative to this DS directory
        # TODO: Check if this is still needed
        if dialect == "sqlite" and not os.path.isabs(url.database):
            url.database = os.path.join(self.data_dir, url.database)
            self._properties_ui.lineEdit_database.setText(url.database)
        # Final check
        try:
            engine = create_engine(url)
            with engine.connect():
                pass
        except Exception as e:  # pylint: disable=broad-except
            if log_errors:
                self._logger.msg_error.emit(
                    f"Unable to generate URL from <b>{self.name}</b> selections: {e} "
                    "<br>Please make new selections and try again."
                )
            return None
        return url

    def project(self):
        """Returns current project or None if no project open."""
        return self._project

    @Slot("QString", name="set_path_to_sqlite_file")
    def set_path_to_sqlite_file(self, file_path):
        """Set path to SQLite file."""
        abs_path = os.path.abspath(file_path)
        self._properties_ui.lineEdit_database.setText(abs_path)
        self.set_url_key("database", abs_path)

    @Slot(bool, name='open_sqlite_file')
    def open_sqlite_file(self, checked=False):
        """Open file browser where user can select the path to an SQLite
        file that they want to use."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(self._toolbox, 'Select SQLite file', self.data_dir)
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        # Update UI
        self.set_path_to_sqlite_file(file_path)

    def load_url_into_selections(self):
        """Load url attribute into shared widget selections.
        Used when activating the item, and creating a new Spine db."""
        # TODO: Test what happens when Tool item calls this and this item is selected.
        self._properties_ui.comboBox_dialect.setCurrentIndex(-1)
        self._properties_ui.comboBox_dsn.setCurrentIndex(-1)
        self._properties_ui.lineEdit_host.clear()
        self._properties_ui.lineEdit_port.clear()
        self._properties_ui.lineEdit_database.clear()
        self._properties_ui.lineEdit_username.clear()
        self._properties_ui.lineEdit_password.clear()
        if not self._url:
            return
        dialect = self._url["dialect"]
        self.enable_dialect(dialect)
        self._properties_ui.comboBox_dialect.setCurrentText(dialect)
        if self._url["host"]:
            self._properties_ui.lineEdit_host.setText(self._url["host"])
        if self._url["port"]:
            self._properties_ui.lineEdit_port.setText(str(self._url["port"]))
        if self._url["database"]:
            abs_db_path = os.path.abspath(self._url["database"])
            self._properties_ui.lineEdit_database.setText(abs_db_path)
        if self._url["username"]:
            self._properties_ui.lineEdit_username.setText(self._url["username"])
        if self._url["password"]:
            self._properties_ui.lineEdit_password.setText(self._url["password"])

    def set_url_key(self, key, value):
        """Set url key to value."""
        self._url[key] = value
        self.item_changed.emit()

    @Slot(name="refresh_host")
    def refresh_host(self):
        """Refresh host from selections."""
        host = self._properties_ui.lineEdit_host.text()
        self.set_url_key("host", host)

    @Slot(name="refresh_port")
    def refresh_port(self):
        """Refresh port from selections."""
        port = self._properties_ui.lineEdit_port.text()
        self.set_url_key("port", port)

    @Slot(name="refresh_database")
    def refresh_database(self):
        """Refresh database from selections."""
        database = self._properties_ui.lineEdit_database.text()
        self.set_url_key("database", database)

    @Slot(name="refresh_username")
    def refresh_username(self):
        """Refresh username from selections."""
        username = self._properties_ui.lineEdit_username.text()
        self.set_url_key("username", username)

    @Slot(name="refresh_password")
    def refresh_password(self):
        """Refresh password from selections."""
        password = self._properties_ui.lineEdit_password.text()
        self.set_url_key("password", password)

    @Slot("QString", name="refresh_dialect")
    def refresh_dialect(self, dialect):
        self.set_url_key("dialect", dialect)
        self.enable_dialect(dialect)

    def enable_dialect(self, dialect):
        """Enable the given dialect in the item controls."""
        if dialect == 'sqlite':
            self.enable_sqlite()
        elif dialect == 'mssql':
            import pyodbc  # pylint: disable=import-outside-toplevel

            dsns = pyodbc.dataSources()
            # Collect dsns which use the msodbcsql driver
            mssql_dsns = list()
            for key, value in dsns.items():
                if 'msodbcsql' in value.lower():
                    mssql_dsns.append(key)
            if mssql_dsns:
                self._properties_ui.comboBox_dsn.clear()
                self._properties_ui.comboBox_dsn.addItems(mssql_dsns)
                self._properties_ui.comboBox_dsn.setCurrentIndex(-1)
                self.enable_mssql()
            else:
                msg = "Please create a SQL Server ODBC Data Source first."
                self._logger.msg_warning.emit(msg)
        else:
            self.enable_common()

    def enable_no_dialect(self):
        """Adjust widget enabled status to default when no dialect is selected."""
        self._properties_ui.comboBox_dialect.setEnabled(True)
        self._properties_ui.comboBox_dsn.setEnabled(False)
        self._properties_ui.toolButton_open_sqlite_file.setEnabled(False)
        self._properties_ui.lineEdit_host.setEnabled(False)
        self._properties_ui.lineEdit_port.setEnabled(False)
        self._properties_ui.lineEdit_database.setEnabled(False)
        self._properties_ui.lineEdit_username.setEnabled(False)
        self._properties_ui.lineEdit_password.setEnabled(False)

    def enable_mssql(self):
        """Adjust controls to mssql connection specification."""
        self._properties_ui.comboBox_dsn.setEnabled(True)
        self._properties_ui.toolButton_open_sqlite_file.setEnabled(False)
        self._properties_ui.lineEdit_host.setEnabled(False)
        self._properties_ui.lineEdit_port.setEnabled(False)
        self._properties_ui.lineEdit_database.setEnabled(False)
        self._properties_ui.lineEdit_username.setEnabled(True)
        self._properties_ui.lineEdit_password.setEnabled(True)
        self._properties_ui.lineEdit_host.clear()
        self._properties_ui.lineEdit_port.clear()
        self._properties_ui.lineEdit_database.clear()

    def enable_sqlite(self):
        """Adjust controls to sqlite connection specification."""
        self._properties_ui.comboBox_dsn.setEnabled(False)
        self._properties_ui.comboBox_dsn.setCurrentIndex(-1)
        self._properties_ui.toolButton_open_sqlite_file.setEnabled(True)
        self._properties_ui.lineEdit_host.setEnabled(False)
        self._properties_ui.lineEdit_port.setEnabled(False)
        self._properties_ui.lineEdit_database.setEnabled(True)
        self._properties_ui.lineEdit_username.setEnabled(False)
        self._properties_ui.lineEdit_password.setEnabled(False)
        self._properties_ui.lineEdit_host.clear()
        self._properties_ui.lineEdit_port.clear()
        self._properties_ui.lineEdit_username.clear()
        self._properties_ui.lineEdit_password.clear()

    def enable_common(self):
        """Adjust controls to 'common' connection specification."""
        self._properties_ui.comboBox_dsn.setEnabled(False)
        self._properties_ui.comboBox_dsn.setCurrentIndex(-1)
        self._properties_ui.toolButton_open_sqlite_file.setEnabled(False)
        self._properties_ui.lineEdit_host.setEnabled(True)
        self._properties_ui.lineEdit_port.setEnabled(True)
        self._properties_ui.lineEdit_database.setEnabled(True)
        self._properties_ui.lineEdit_username.setEnabled(True)
        self._properties_ui.lineEdit_password.setEnabled(True)

    @Slot(bool)
    def open_ds_view(self, checked=False):
        """Opens current url in the data store view."""
        self._update_sa_url()
        if not self._sa_url:
            return
        if self.ds_view:
            # If the db_url is the same, just raise the current form
            if self.ds_view.db_url == (self._sa_url, self.name):
                if self.ds_view.windowState() & Qt.WindowMinimized:
                    # Remove minimized status and restore window with the previous state (maximized/normal state)
                    self.ds_view.setWindowState(self.ds_view.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.ds_view.activateWindow()
                else:
                    self.ds_view.raise_()
                return
            self.ds_view.close()
        self.do_open_ds_view()

    @busy_effect
    def do_open_ds_view(self):
        """Opens current url in the data store view."""
        try:
            self.ds_view = DataStoreForm(self._project.db_mngr, (self._sa_url, self.name))
        except spinedb_api.SpineDBAPIError as e:
            self._logger.msg_error.emit(e.msg)
            return
        self.ds_view.destroyed.connect(self._handle_ds_view_destroyed)
        self.ds_view.show()

    @Slot()
    def _handle_ds_view_destroyed(self):
        self.ds_view = None

    def data_files(self):
        """Return a list of files that are in this items data directory."""
        if not os.path.isdir(self.data_dir):
            return None
        return os.listdir(self.data_dir)

    @Slot(bool)
    def copy_url(self, checked=False):
        """Copy db url to clipboard."""
        self._update_sa_url()
        if not self._sa_url:
            return
        self._sa_url.password = None
        QApplication.clipboard().setText(str(self._sa_url))
        self._logger.msg.emit(f"Database url <b>{self._sa_url}</b> copied to clipboard")

    @Slot(bool, name="create_new_spine_database")
    def create_new_spine_database(self, checked=False):
        """Create new (empty) Spine database."""
        for_spine_model = self._properties_ui.checkBox_for_spine_model.isChecked()
        # Try to make an url from the current status
        self._update_sa_url(log_errors=False)
        if not self._sa_url:
            self._logger.msg_warning.emit(
                f"Unable to generate URL from <b>{self.name}</b> selections. Defaults will be used..."
            )
            dialect = "sqlite"
            database = os.path.abspath(os.path.join(self.data_dir, self.name + ".sqlite"))
            self._properties_ui.comboBox_dialect.setCurrentText(dialect)
            self._properties_ui.lineEdit_database.setText(database)
            self._url["dialect"] = dialect
            self._url["database"] = database
            self.item_changed.emit()
        self._project.db_mngr.create_new_spine_database(self._sa_url, for_spine_model)

    def update_name_label(self):
        """Update Data Store tab name label. Used only when renaming project items."""
        self._properties_ui.label_ds_name.setText(self.name)

    def _do_handle_dag_changed(self, resources):
        """See base class."""
        self._update_sa_url(log_errors=False)
        if not self._sa_url:
            self.add_notification(
                "The URL for this Data Store is not correctly set. Set it in the Data Store Properties panel."
            )

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        d = super().item_dict()
        d["url"] = dict(self.url())
        db = d["url"]["database"]
        # If database key is a file, change the path to relative
        if d["url"]["dialect"] == "sqlite" and db is not None:
            d["url"]["database"] = serialize_path(db, self._project.project_dir)
        return d

    @staticmethod
    def upgrade_from_no_version_to_version_1(item_name, old_item_dict, old_project_dir):
        """See base class."""
        new_data_store = dict(old_item_dict)
        if "reference" in new_data_store:
            url_path = new_data_store["reference"]
            url = {"dialect": "sqlite", "username": None, "host": None, "port": None}
        else:
            url = new_data_store["url"]
            url_path = url["database"]
        if not url_path:
            url["database"] = None
        else:
            serialized_url_path = serialize_path(url_path, old_project_dir)
            if serialized_url_path["relative"]:
                serialized_url_path["path"] = os.path.join(".spinetoolbox", "items", serialized_url_path["path"])
            url["database"] = serialized_url_path
        new_data_store["url"] = url
        return new_data_store

    @staticmethod
    def custom_context_menu(parent, pos):
        """Returns the context menu for this item.

        Args:
            parent (QWidget): The widget that is controlling the menu
            pos (QPoint): Position on screen
        """
        return DataStoreContextMenu(parent, pos)

    def apply_context_menu_action(self, parent, action):
        """Applies given action from context menu. Implement in subclasses as needed.

        Args:
            parent (QWidget): The widget that is controlling the menu
            action (str): The selected action
        """
        super().apply_context_menu_action(parent, action)
        if action == "Open view...":
            self.open_ds_view()

    def rename(self, new_name):
        """Rename this item.

        Args:
            new_name (str): New name
        Returns:
            bool: True if renaming succeeded, False otherwise
        """
        old_data_dir = os.path.abspath(self.data_dir)  # Old data_dir before rename
        success = super().rename(new_name)
        if not success:
            return False
        # For a Data Store, logs_dir must be updated and the database line edit may need to be updated
        db_dir, db_filename = os.path.split(os.path.abspath(self._properties_ui.lineEdit_database.text().strip()))
        # If dialect is sqlite and db line edit refers to a file in the old data_dir, db line edit needs updating
        if self._properties_ui.comboBox_dialect.currentText() == "sqlite" and db_dir == old_data_dir:
            new_db_path = os.path.join(self.data_dir, db_filename)  # Note. data_dir has been updated at this point
            # Check that the db was moved successfully to the new data_dir
            if os.path.exists(new_db_path):
                self.set_path_to_sqlite_file(new_db_path)
        # Update logs dir
        self.logs_dir = os.path.join(self.data_dir, "logs")
        return True

    def tear_down(self):
        """Tears down this item. Called by toolbox just before closing.
        Closes the DataStoreForm instance opened by this item.
        """
        if self.ds_view:
            self.ds_view.close()

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type() == "Importer":
            self._logger.msg.emit(
                f"Link established. Mappings generated by <b>{source_item.name}</b> will be "
                f"imported in <b>{self.name}</b> when executing."
            )
        elif source_item.item_type() in ["Data Connection", "Tool"]:
            # Does this type of link do anything?
            self._logger.msg.emit("Link established.")
        else:
            super().notify_destination(source_item)

    @staticmethod
    def default_name_prefix():
        """see base class"""
        return "Data Store"

    def output_resources_backward(self):
        """See base class."""
        return self.output_resources_forward()

    def output_resources_forward(self):
        """See base class."""
        self._update_sa_url(log_errors=False)
        if self._sa_url:
            resource = ProjectItemResource(self, "database", url=str(self._sa_url))
            return [resource]
        self.add_notification(
            "The URL for this Data Store is not correctly set. Set it in the Data Store Properties panel."
        )
        return list()
