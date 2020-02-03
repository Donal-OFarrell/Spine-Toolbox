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
QUndoCommand subclasses for modifying the db.

:authors: M. Marin (KTH)
:date:   31.1.2020
"""

from copy import deepcopy
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QUndoCommand


class AddItemsCommand(QUndoCommand):
    _command_name = {
        "object class": "add object classes",
        "object": "add objects",
        "relationship class": "add relationship classes",
        "relationship": "add relationships",
        "parameter definition": "add parameter definitions",
        "parameter value": "add parameter values",
        "parameter value list": "add parameter value lists",
        "parameter tag": "add parameter tags",
    }
    _method_name = {
        "object class": "add_object_classes",
        "object": "add_objects",
        "relationship class": "add_wide_relationship_classes",
        "relationship": "add_wide_relationships",
        "parameter definition": "add_parameter_definitions",
        "parameter value": "add_parameter_values",
        "parameter value list": "add_wide_parameter_value_lists",
        "parameter tag": "add_parameter_tags",
    }
    _emit_signal_name = {
        "object class": "object_classes_added",
        "object": "objects_added",
        "relationship class": "relationship_classes_added",
        "relationship": "relationships_added",
        "parameter definition": "_parameter_definitions_added",
        "parameter value": "_parameter_values_added",
        "parameter value list": "parameter_value_lists_added",
        "parameter tag": "parameter_tags_added",
    }
    _receive_signal_name = {
        "parameter definition": "parameter_definitions_added",
        "parameter value": "parameter_values_added",
    }

    def __init__(self, db_mngr, db_map_data, item_type):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
            item_type (str): the item type
        """
        super().__init__()
        self.db_mngr = db_mngr
        self.redo_db_map_data = db_map_data
        self.item_type = item_type
        self.method_name = self._method_name[item_type]
        self.emit_signal_name = self._emit_signal_name[item_type]
        receive_signal_name = self._receive_signal_name.get(item_type, self.emit_signal_name)
        self.receive_signal = getattr(db_mngr, receive_signal_name)
        self.setText(self._command_name[item_type])
        self.undo_db_map_data = None
        self._completed = False

    def redo(self):
        self.receive_signal.connect(self.receive_items_added)
        self.db_mngr.add_or_update_items(self.redo_db_map_data, self.method_name, self.emit_signal_name)
        self.receive_signal.disconnect(self.receive_items_added)
        if not self._completed:
            self.setObsolete(True)

    def undo(self):
        self.db_mngr.remove_items(self.undo_db_map_data)

    @Slot(object)
    def receive_items_added(self, db_map_data):
        self.undo_db_map_data = {db_map: {self.item_type: data} for db_map, data in db_map_data.items()}
        self._completed = True


class AddCheckedParameterValuesCommand(AddItemsCommand):
    def __init__(self, db_mngr, db_map_data):
        super().__init__(db_mngr, db_map_data, "parameter value")

    def redo(self):
        self.db_mngr.parameter_values_added.connect(self.receive_items_added)
        self.db_mngr.add_or_update_checked_parameter_values(
            self.redo_db_map_data, "_add_parameter_values", "parameter_values_added"
        )
        self.db_mngr.parameter_values_added.disconnect(self.receive_items_added)
        if not self._completed:
            self.setObsolete(True)


class UpdateItemsCommand(QUndoCommand):
    _command_name = {
        "object class": "update object classes",
        "object": "update objects",
        "relationship class": "update relationship classes",
        "relationship": "update relationships",
        "parameter definition": "update parameter definitions",
        "parameter value": "update parameter values",
        "parameter value list": "update parameter value lists",
        "parameter tag": "update parameter tags",
    }
    _method_name = {
        "object class": "update_object_classes",
        "object": "update_objects",
        "relationship class": "update_wide_relationship_classes",
        "relationship": "update_wide_relationships",
        "parameter definition": "update_parameter_definitions",
        "parameter value": "update_parameter_values",
        "parameter value list": "update_wide_parameter_value_lists",
        "parameter tag": "update_parameter_tags",
    }
    _emit_signal_name = {
        "object class": "object_classes_updated",
        "object": "objects_updated",
        "relationship class": "relationship_classes_updated",
        "relationship": "relationships_updated",
        "parameter definition": "_parameter_definitions_updated",
        "parameter value": "_parameter_values_updated",
        "parameter value list": "parameter_value_lists_updated",
        "parameter tag": "parameter_tags_updated",
    }

    def __init__(self, db_mngr, db_map_data, item_type):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
            item_type (str): the item type
        """
        super().__init__()
        self.db_mngr = db_mngr
        self.redo_db_map_data = db_map_data
        self.item_type = item_type
        self.method_name = self._method_name[item_type]
        self.emit_signal_name = self._emit_signal_name[item_type]
        self.receive_signal = getattr(db_mngr, self.emit_signal_name)
        self.setText(self._command_name[item_type])
        self.undo_db_map_data = {
            db_map: [self._get_undo_item(db_map, item["id"]) for item in data] for db_map, data in db_map_data.items()
        }
        self._completed = False

    def _get_undo_item(self, db_map, id_):
        def _get_undo_relationship_class_from_cache(item):
            item = deepcopy(item)
            item["object_class_id_list"] = [int(id_) for id_ in item["object_class_id_list"].split(",")]
            del item["object_class_name_list"]
            return item

        def _get_undo_relationship_from_cache(item):
            item = deepcopy(item)
            item["object_id_list"] = [int(id_) for id_ in item["object_id_list"].split(",")]
            del item["object_name_list"]
            return item

        def _get_undo_parameter_definition_from_cache(item):
            item = {k: v for k, v in item.items() if k != "formatted_default_value"}
            item = deepcopy(item)
            if "parameter_name" in item:
                item["name"] = item.pop("parameter_name")
            return item

        def _get_undo_parameter_value_list_from_cache(item):
            item = deepcopy(item)
            item["value_list"] = item["value_list"].split(",")
            return item

        item = self.db_mngr.get_item(db_map, self.item_type, id_)
        return {
            "relationship class": _get_undo_relationship_class_from_cache,
            "relationship": _get_undo_relationship_from_cache,
            "parameter definition": _get_undo_parameter_definition_from_cache,
            "parameter value list": _get_undo_parameter_value_list_from_cache,
        }.get(self.item_type, lambda x: x)(item)

    def redo(self):
        self.receive_signal.connect(self.receive_items_updated)
        self.db_mngr.add_or_update_items(self.redo_db_map_data, self.method_name, self.emit_signal_name)
        self.receive_signal.disconnect(self.receive_items_updated)
        if not self._completed:
            self.setObsolete(True)

    def undo(self):
        self.db_mngr.add_or_update_items(self.undo_db_map_data, self.method_name, self.emit_signal_name)

    @Slot(object)
    def receive_items_updated(self, db_map_data):
        self._completed = True


class UpdateCheckedParameterValuesCommand(UpdateItemsCommand):
    def __init__(self, db_mngr, db_map_data):
        super().__init__(db_mngr, db_map_data, "parameter value")

    def redo(self):
        self.db_mngr.parameter_values_updated.connect(self.receive_items_updated)
        self.db_mngr.add_or_update_checked_parameter_values(
            self.redo_db_map_data, "_update_parameter_values", "parameter_values_updated"
        )
        self.db_mngr.parameter_values_updated.disconnect(self.receive_items_updated)
        if not self._completed:
            self.setObsolete(True)