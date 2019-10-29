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
The SpineDBManager class

:author: P. Vennström (VTT) and M. Marin (KTH)
:date:   2.10.2019
"""

from PySide2.QtCore import QObject, Signal, Slot
from PySide2.QtWidgets import QMessageBox
from spinedb_api import SpineDBAPIError, SpineDBVersionError, DiffDatabaseMapping
from .helpers import IconManager, busy_effect


class SpineDBManager(QObject):
    """Class to manage DBs within a project.

    TODO: Expand description, how it works, the cache, the signals, etc.
    """

    msg_error = Signal("QVariant", name="msg_error")
    # Added
    object_classes_added = Signal("QVariant", name="object_classes_added")
    objects_added = Signal("QVariant", name="objects_added")
    relationship_classes_added = Signal("QVariant", name="relationship_classes_added")
    relationships_added = Signal("QVariant", name="relationships_added")
    parameter_definitions_added = Signal("QVariant", name="parameter_definitions_added")
    parameter_values_added = Signal("QVariant", name="parameter_values_added")
    parameter_value_lists_added = Signal("QVariant", name="parameter_value_lists_added")
    parameter_tags_added = Signal("QVariant", name="parameter_tags_added")
    # Removed
    object_classes_removed = Signal("QVariant", name="object_classes_removed")
    objects_removed = Signal("QVariant", name="objects_removed")
    relationship_classes_removed = Signal("QVariant", name="relationship_classes_removed")
    relationships_removed = Signal("QVariant", name="relationships_removed")
    parameter_definitions_removed = Signal("QVariant", name="parameter_definitions_removed")
    parameter_values_removed = Signal("QVariant", name="parameter_values_removed")
    parameter_value_lists_removed = Signal("QVariant", name="parameter_value_lists_removed")
    parameter_tags_removed = Signal("QVariant", name="parameter_tags_removed")
    # Updated
    object_classes_updated = Signal("QVariant", name="object_classes_updated")
    objects_updated = Signal("QVariant", name="objects_updated")
    relationship_classes_updated = Signal("QVariant", name="relationship_classes_updated")
    relationships_updated = Signal("QVariant", name="relationships_updated")
    parameter_definitions_updated = Signal("QVariant", name="parameter_definitions_updated")
    parameter_values_updated = Signal("QVariant", name="parameter_values_updated")
    parameter_value_lists_updated = Signal("QVariant", name="parameter_value_lists_updated")
    parameter_tags_updated = Signal("QVariant", name="parameter_tags_updated")
    parameter_definition_tags_set = Signal("QVariant", name="parameter_definition_tags_set")

    def __init__(self, parent=None):
        """Initializes the instance.

        Args:
            parent (QObject, NoneType)
        """
        super().__init__(parent)
        self._db_maps = {}
        self._cache = {}
        self.icon_mngr = IconManager()
        self.connect_signals()

    @property
    def db_maps(self):
        return set(self._db_maps.values())

    def get_db_map(self, url, upgrade=False, codename=None):
        """Returns a DiffDatabaseMapping instance from url if possible, None otherwise.
        If needed, asks the user to upgrade to the latest db version.

        Returns:
            DiffDatabaseMapping, NoneType
        """
        try:
            return self.do_get_db_map(url, upgrade, codename)
        except SpineDBVersionError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Incompatible database version")
            msg.setText(
                "The database at <b>{}</b> is from an older version of Spine "
                "and needs to be upgraded in order to be used with the current version.".format(url)
            )
            msg.setInformativeText(
                "Do you want to upgrade it now?"
                "<p><b>WARNING</b>: After the upgrade, "
                "the database may no longer be used "
                "with previous versions of Spine."
            )
            msg.addButton(QMessageBox.Cancel)
            msg.addButton("Upgrade", QMessageBox.YesRole)
            ret = msg.exec_()  # Show message box
            if ret == QMessageBox.Cancel:
                return None
            return self.get_db_map(url, upgrade=True, codename=codename)

    @busy_effect
    def do_get_db_map(self, url, upgrade, codename):
        """Returns a memoized DiffDatabaseMapping instance from url.
        Called by `get_db_map`.

        Returns:
            DiffDatabaseMapping
        """
        if url not in self._db_maps:
            self._db_maps[url] = DiffDatabaseMapping(url, upgrade=upgrade, codename=codename)
        self._db_maps[url].reconnect()
        return self._db_maps[url]

    def connect_signals(self):
        """Connects signals."""
        # Cache
        self.object_classes_added.connect(lambda db_map_data: self.cache_items("object class", db_map_data))
        self.objects_added.connect(lambda db_map_data: self.cache_items("object", db_map_data))
        self.relationship_classes_added.connect(lambda db_map_data: self.cache_items("relationship class", db_map_data))
        self.relationships_added.connect(lambda db_map_data: self.cache_items("relationship", db_map_data))
        # Discard
        self.object_classes_removed.connect(lambda db_map_data: self.uncache_items("object class", db_map_data))
        self.objects_removed.connect(lambda db_map_data: self.uncache_items("object", db_map_data))
        self.relationship_classes_removed.connect(
            lambda db_map_data: self.uncache_items("relationship class", db_map_data)
        )
        self.relationships_removed.connect(lambda db_map_data: self.uncache_items("relationship", db_map_data))
        self.parameter_definitions_removed.connect(
            lambda db_map_data: self.uncache_items("parameter definition", db_map_data)
        )
        self.parameter_values_removed.connect(lambda db_map_data: self.uncache_items("parameter value", db_map_data))
        # Update cache
        self.object_classes_updated.connect(lambda db_map_data: self.cache_items("object class", db_map_data))
        self.objects_updated.connect(lambda db_map_data: self.cache_items("object", db_map_data))
        self.relationship_classes_updated.connect(
            lambda db_map_data: self.cache_items("relationship class", db_map_data)
        )
        self.relationships_updated.connect(lambda db_map_data: self.cache_items("relationship", db_map_data))
        self.parameter_definition_tags_set.connect(self.cache_parameter_definition_tags)
        # Auto refresh
        self.parameter_definitions_updated.connect(self.auto_refresh_parameter_definitions)
        self.parameter_values_updated.connect(self.auto_refresh_parameter_values)
        # Icons
        self.object_classes_added.connect(self.update_icons)
        self.object_classes_updated.connect(self.update_icons)
        # On cascade remove
        self.object_classes_removed.connect(self.cascade_remove_objects)
        self.object_classes_removed.connect(self.cascade_remove_relationship_classes)
        self.object_classes_removed.connect(self.cascade_remove_parameter_definitions)
        self.object_classes_removed.connect(self.cascade_remove_parameter_values_by_entity_class)
        self.relationship_classes_removed.connect(self.cascade_remove_relationships_by_class)
        self.relationship_classes_removed.connect(self.cascade_remove_parameter_definitions)
        self.relationship_classes_removed.connect(self.cascade_remove_parameter_values_by_entity_class)
        self.relationship_classes_removed.connect(self.cascade_remove_relationships_by_class)
        self.objects_removed.connect(self.cascade_remove_relationships_by_object)
        self.objects_removed.connect(self.cascade_remove_parameter_values_by_entity)
        self.relationships_removed.connect(self.cascade_remove_parameter_values_by_entity)
        self.parameter_definitions_removed.connect(self.cascade_remove_parameter_values_by_definition)
        # On cascade refresh
        self.object_classes_updated.connect(self.cascade_refresh_relationship_classes)
        self.object_classes_updated.connect(self.cascade_refresh_parameter_definitions)
        self.object_classes_updated.connect(self.cascade_refresh_parameter_values_by_entity_class)
        self.relationship_classes_updated.connect(self.cascade_refresh_parameter_definitions)
        self.relationship_classes_updated.connect(self.cascade_refresh_parameter_values_by_entity_class)
        self.objects_updated.connect(self.cascade_refresh_relationships_by_object)
        self.objects_updated.connect(self.cascade_refresh_parameter_values_by_entity)
        self.relationships_updated.connect(self.cascade_refresh_parameter_values_by_entity)
        self.parameter_definitions_updated.connect(self.cascade_refresh_parameter_values_by_definition)
        self.parameter_value_lists_updated.connect(self.cascade_refresh_parameter_definitions_by_value_list)
        self.parameter_value_lists_removed.connect(self.cascade_refresh_parameter_definitions_by_value_list)
        self.parameter_tags_updated.connect(self.cascade_refresh_parameter_definitions_by_tag)
        self.parameter_tags_removed.connect(self.cascade_refresh_parameter_definitions_by_tag)

    def cache_items(self, item_type, db_map_data):
        """Caches data for a given type.
        It works for both insert and update operations.

        Args:
            item_type (str)
            db_map_data (dict): lists of dictionary items keyed by DiffDatabaseMapping
        """
        for db_map, items in db_map_data.items():
            for item in items:
                self._cache.setdefault(db_map, {}).setdefault(item_type, {}).setdefault(item["id"], {}).update(item)

    def uncache_items(self, item_type, db_map_data):
        """Removes data from cache.

        Args:
            item_type (str)
            db_map_data (dict): lists of dictionary items keyed by DiffDatabaseMapping
        """
        for db_map, items in db_map_data.items():
            for item in items:
                self._cache.setdefault(db_map, {}).setdefault(item_type, {}).pop(item["id"])

    def update_icons(self, db_map_data):
        """Runs when object classes are added or updated. Setups icons for those classes.
        Args:
            item_type (str)
            db_map_data (dict): lists of dictionary items keyed by DiffDatabaseMapping
        """
        object_classes = [item for db_map, data in db_map_data.items() for item in data]
        self.icon_mngr.setup_object_pixmaps(object_classes)

    def entity_class_icon(self, db_map, entity_type, entity_class_id):
        """Returns an appropriate icon for a given entity class.

        Args:
            db_map (DiffDatabaseMapping)
            entity_type (str): either 'object class' or 'relationship class'
            entity_class_id (int)

        Returns:
            QIcon
        """
        entity_class = self.get_item(db_map, entity_type, entity_class_id)
        if not entity_class:
            return None
        if entity_type == "object class":
            return self.icon_mngr.object_icon(entity_class["name"])
        if entity_type == "relationship class":
            return self.icon_mngr.relationship_icon(entity_class["object_class_name_list"])

    def get_item(self, db_map, item_type, id_):
        """Returns the item of the given type  in the given db map that has the given id.
        If not found, an empty dictionary is returned.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)
            id_ (int)

        Returns:
            dict
        """
        item = self._cache.get(db_map, {}).get(item_type, {}).get(id_)
        if item:
            return item
        _ = self._get_items_from_db(db_map, item_type)
        return self._cache.get(db_map, {}).get(item_type, {}).get(id_, {})

    def get_item_by_field(self, db_map, item_type, field, value):
        """Returns the first item of the given type in the given db map
        that has the given value for the given field
        Returns an empty dictionary if none found.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)
            field (str)
            value

        Returns:
            dict
        """
        return next(iter(self.get_items_by_field(db_map, item_type, field, value)), {})

    def get_items_by_field(self, db_map, item_type, field, value):
        """Returns all items of the given type in the given db map that have the given value
        for the given field. Returns an empty list if none found.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)
            field (str)
            value

        Returns:
            list
        """
        items = [x for x in self.get_items(db_map, item_type) if x[field] == value]
        if items:
            return items
        return [x for x in self._get_items_from_db(db_map, item_type) if x[field] == value]

    def get_items(self, db_map, item_type):
        """Returns all the items of the given type in the given db map,
        or an empty list if none found.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)

        Returns:
            list
        """
        items = self._cache.get(db_map, {}).get(item_type, {})
        if items:
            return items.values()
        return self._get_items_from_db(db_map, item_type)

    def _get_items_from_db(self, db_map, item_type):
        """Returns all items of the given type in the given db map.
        Called by the above methods whenever they don't find what they're looking for the cache.
        """
        method_name_dict = {
            "object class": "get_object_classes",
            "object": "get_objects",
            "relationship class": "get_relationship_classes",
            "relationship": "get_relationships",
            "parameter definition": "get_parameter_definitions",
            "parameter value": "get_parameter_values",
            "parameter value list": "get_parameter_value_lists",
            "parameter tag": "get_parameter_tags",
        }
        method_name = method_name_dict.get(item_type)
        if not method_name:
            return []
        return getattr(self, method_name)(db_map)

    def get_object_classes(self, db_map):
        """Returns object classes from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.object_class_sq)
        items = [x._asdict() for x in qry]
        self.cache_items("object class", {db_map: items})
        self.update_icons({db_map: items})
        return items

    def get_objects(self, db_map, class_id=None):
        """Returns objects from database.

        Args:
            db_map (DiffDatabaseMapping)
            class_id (int, optional)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.object_sq)
        if class_id:
            qry = qry.filter_by(class_id=class_id)
        items = [x._asdict() for x in qry]
        self.cache_items("object", {db_map: items})
        return items

    def get_relationship_classes(self, db_map, ids=None, object_class_id=None):
        """Returns relationship classes from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            object_class_id (int, optional)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.wide_relationship_class_sq)
        if ids:
            qry = qry.filter(db_map.wide_relationship_class_sq.c.id.in_(ids))
        if object_class_id:
            ids = {x.id for x in db_map.query(db_map.relationship_class_sq).filter_by(object_class_id=object_class_id)}
            qry = qry.filter(db_map.wide_relationship_class_sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.cache_items("relationship class", {db_map: items})
        return items

    def get_relationships(self, db_map, ids=None, class_id=None, object_id=None):
        """Returns relationships from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            class_id (int, optional)
            object_id (int, optional)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.wide_relationship_sq)
        if ids:
            qry = qry.filter(db_map.wide_relationship_sq.c.id.in_(ids))
        if object_id:
            ids = {x.id for x in db_map.query(db_map.relationship_sq).filter_by(object_id=object_id)}
            qry = qry.filter(db_map.wide_relationship_sq.c.id.in_(ids))
        if class_id:
            qry = qry.filter_by(class_id=class_id)
        items = [x._asdict() for x in qry]
        self.cache_items("relationship", {db_map: items})
        return items

    def get_object_parameter_definitions(self, db_map, ids=None, object_class_id=None):
        """Returns object parameter definitions from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            object_class_id (int, optional)

        Returns:
            list: dictionary items
        """
        sq = db_map.object_parameter_definition_sq
        qry = db_map.query(sq)
        if object_class_id:
            qry = qry.filter_by(object_class_id=object_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.cache_items("parameter definition", {db_map: items})
        return items

    def get_relationship_parameter_definitions(self, db_map, ids=None, relationship_class_id=None):
        """Returns relationship parameter definitions from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            relationship_class_id (int, optional)

        Returns:
            list: dictionary items
        """
        sq = db_map.relationship_parameter_definition_sq
        qry = db_map.query(sq)
        if relationship_class_id:
            qry = qry.filter_by(relationship_class_id=relationship_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.cache_items("parameter definition", {db_map: items})
        return items

    def get_object_parameter_values(self, db_map, ids=None, object_class_id=None):
        """Returns object parameter values from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set)
            object_class_id (int)

        Returns:
            list: dictionary items
        """
        sq = db_map.object_parameter_value_sq
        qry = db_map.query(sq)
        if object_class_id:
            qry = qry.filter_by(object_class_id=object_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.cache_items("parameter value", {db_map: items})
        return items

    def get_relationship_parameter_values(self, db_map, ids=None, relationship_class_id=None):
        """Returns relationship parameter values from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set)
            relationship_class_id (int)

        Returns:
            list: dictionary items
        """
        sq = db_map.relationship_parameter_value_sq
        qry = db_map.query(sq)
        if relationship_class_id:
            qry = qry.filter_by(relationship_class_id=relationship_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.cache_items("parameter value", {db_map: items})
        return items

    def get_parameter_definitions(self, db_map, ids=None, entity_class_id=None):
        """Returns both object and relationship parameter definitions.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            entity_class_id (int, optional)

        Returns:
            list: dictionary items
        """
        return self.get_object_parameter_definitions(
            db_map, ids=ids, object_class_id=entity_class_id
        ) + self.get_relationship_parameter_definitions(db_map, ids=ids, relationship_class_id=entity_class_id)

    def get_parameter_values(self, db_map, ids=None, entity_class_id=None):
        """Returns both object and relationship parameter values.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            entity_class_id (int, optional)

        Returns:
            list: dictionary items
        """
        return self.get_object_parameter_values(
            db_map, ids=ids, object_class_id=entity_class_id
        ) + self.get_relationship_parameter_values(db_map, ids=ids, relationship_class_id=entity_class_id)

    def get_parameter_value_lists(self, db_map):
        """Returns parameter value lists from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.wide_parameter_value_list_sq)
        items = [x._asdict() for x in qry]
        self.cache_items("parameter value list", {db_map: items})
        return items

    def get_parameter_tags(self, db_map):
        """Get parameter tags from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.parameter_tag_sq)
        items = [x._asdict() for x in qry]
        self.cache_items("parameter tag", {db_map: items})
        return items

    def add_or_update_items(self, db_map_data, method_name, signal_name):
        """Adds or updates items in db.

        Args:
            db_map_data (dict): lists of items to add or update keyed by DiffDatabaseMapping
            method_name (str): attribute of DiffDatabaseMapping to call for performing the operation
            signal_name (str) : signal attribute of SpineDBManager to emit if successful
        """
        db_map_data_out = dict()
        error_log = dict()
        for db_map, items in db_map_data.items():
            items, error_log[db_map] = getattr(db_map, method_name)(*items)
            if not items.count():
                continue
            db_map_data_out[db_map] = [x._asdict() for x in items]
        if any(error_log.values()):
            self.msg_error.emit(error_log)
        if any(db_map_data_out.values()):
            getattr(self, signal_name).emit(db_map_data_out)

    def add_object_classes(self, db_map_data):
        """Adds object classes to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "add_object_classes", "object_classes_added")

    def add_objects(self, db_map_data):
        """Adds objects to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "add_objects", "objects_added")

    def add_relationship_classes(self, db_map_data):
        """Adds relationship classes to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "add_wide_relationship_classes", "relationship_classes_added")

    def add_relationships(self, db_map_data):
        """Adds relationships to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "add_wide_relationships", "relationships_added")

    def add_parameter_definitions(self, db_map_data):
        """Adds parameter definitions to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "add_parameter_definitions", "parameter_definitions_added")

    def add_parameter_values(self, db_map_data):
        """Adds parameter values to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "add_parameter_values", "parameter_values_added")

    def add_parameter_value_lists(self, db_map_data):
        """Adds parameter value lists to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "add_wide_parameter_value_lists", "parameter_value_lists_added")

    def add_parameter_tags(self, db_map_data):
        """Adds parameter tags to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "add_parameter_tags", "parameter_tags_added")

    def update_object_classes(self, db_map_data):
        """Updates object classes in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "update_object_classes", "object_classes_updated")

    def update_objects(self, db_map_data):
        """Updates objects in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "update_objects", "objects_updated")

    def update_relationship_classes(self, db_map_data):
        """Updates relationship classes in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "update_wide_relationship_classes", "relationship_classes_updated")

    def update_relationships(self, db_map_data):
        """Updates relationships in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "update_wide_relationships", "relationships_updated")

    def update_parameter_definitions(self, db_map_data):
        """Updates parameter definitions in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "update_parameter_definitions", "parameter_definitions_updated")

    def update_parameter_values(self, db_map_data):
        """Updates parameter values in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "update_parameter_values", "parameter_values_updated")

    def update_parameter_value_lists(self, db_map_data):
        """Updates parameter value lists in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "update_wide_parameter_value_lists", "parameter_value_lists_updated")

    def update_parameter_tags(self, db_map_data):
        """Updates parameter tags in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "update_parameter_tags", "parameter_tags_updated")

    def set_parameter_definition_tags(self, db_map_data):
        """Sets parameter definition tags in db.

        Args:
            db_map_data (dict): lists of items to set keyed by DiffDatabaseMapping
        """
        self.add_or_update_items(db_map_data, "set_parameter_definition_tags", "parameter_definition_tags_set")

    def remove_items(self, db_map_typed_data):
        """Removes items from database.

        Args:
            db_map_typed_data (dict): lists of items to remove, keyed by item type, keyed by DiffDatabaseMapping
        """
        # Removing works this way in spinedb_api, all at once, probably because of cascading?
        db_map_object_classes = dict()
        db_map_objects = dict()
        db_map_relationship_classes = dict()
        db_map_relationships = dict()
        db_map_parameter_definitions = dict()
        db_map_parameter_values = dict()
        db_map_parameter_value_lists = dict()
        db_map_parameter_tags = dict()
        error_log = dict()
        for db_map, items_per_type in db_map_typed_data.items():
            object_classes = items_per_type.get("object class", ())
            objects = items_per_type.get("object", ())
            relationship_classes = items_per_type.get("relationship class", ())
            relationships = items_per_type.get("relationship", ())
            parameter_definitions = items_per_type.get("parameter definition", ())
            parameter_values = items_per_type.get("parameter value", ())
            parameter_value_lists = items_per_type.get("parameter value list", ())
            parameter_tags = items_per_type.get("parameter tag", ())
            try:
                db_map.remove_items(
                    object_class_ids={x['id'] for x in object_classes},
                    object_ids={x['id'] for x in objects},
                    relationship_class_ids={x['id'] for x in relationship_classes},
                    relationship_ids={x['id'] for x in relationships},
                    parameter_definition_ids={x['id'] for x in parameter_definitions},
                    parameter_value_ids={x['id'] for x in parameter_values},
                    parameter_value_list_ids={x['id'] for x in parameter_value_lists},
                    parameter_tag_ids={x['id'] for x in parameter_tags},
                )
            except SpineDBAPIError as err:
                error_log[db_map] = err
                continue
            db_map_object_classes[db_map] = object_classes
            db_map_objects[db_map] = objects
            db_map_relationship_classes[db_map] = relationship_classes
            db_map_relationships[db_map] = relationships
            db_map_parameter_definitions[db_map] = parameter_definitions
            db_map_parameter_values[db_map] = parameter_values
            db_map_parameter_value_lists[db_map] = parameter_value_lists
            db_map_parameter_tags[db_map] = parameter_tags
        if any(error_log.values()):
            self.msg_error.emit(error_log)
        if any(db_map_object_classes.values()):
            self.object_classes_removed.emit(db_map_object_classes)
        if any(db_map_objects.values()):
            self.objects_removed.emit(db_map_objects)
        if any(db_map_relationship_classes.values()):
            self.relationship_classes_removed.emit(db_map_relationship_classes)
        if any(db_map_relationships.values()):
            self.relationships_removed.emit(db_map_relationships)
        if any(db_map_parameter_definitions.values()):
            self.parameter_definitions_removed.emit(db_map_parameter_definitions)
        if any(db_map_parameter_values.values()):
            self.parameter_values_removed.emit(db_map_parameter_values)
        if any(db_map_parameter_value_lists.values()):
            self.parameter_value_lists_removed.emit(db_map_parameter_value_lists)
        if any(db_map_parameter_tags.values()):
            self.parameter_tags_removed.emit(db_map_parameter_tags)

    @staticmethod
    def _to_ids(db_map_data):
        return {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}

    @Slot("QVariant", name="cascade_remove_objects")
    def cascade_remove_objects(self, db_map_data):
        """Removes objects in cascade when removing object classes.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_entities(self._to_ids(db_map_data), "object")
        if any(db_map_cascading_data.values()):
            self.objects_removed.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_remove_relationship_classes")
    def cascade_remove_relationship_classes(self, db_map_data):
        """Removes relationship classes in cascade when removing object classes.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_relationship_classes(self._to_ids(db_map_data))
        self.relationship_classes_removed.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_remove_relationships_by_class")
    def cascade_remove_relationships_by_class(self, db_map_data):
        """Removes relationships in cascade when removing objects.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_entities(self._to_ids(db_map_data), "relationship")
        if any(db_map_cascading_data.values()):
            self.relationships_removed.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_remove_relationships_by_object")
    def cascade_remove_relationships_by_object(self, db_map_data):
        """Removes relationships in cascade when removing relationship classes.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_relationships(self._to_ids(db_map_data))
        if any(db_map_cascading_data.values()):
            self.relationships_removed.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_remove_parameter_definitions")
    def cascade_remove_parameter_definitions(self, db_map_data):
        """Removes parameter definitions in cascade when removing entity classes.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_data(self._to_ids(db_map_data), "parameter definition")
        if any(db_map_cascading_data.values()):
            self.parameter_definitions_removed.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_remove_parameter_values_by_entity_class")
    def cascade_remove_parameter_values_by_entity_class(self, db_map_data):
        """Removes parameter values in cascade when removing entity classes.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_data(self._to_ids(db_map_data), "parameter value")
        if any(db_map_cascading_data.values()):
            self.parameter_values_removed.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_remove_parameter_values_by_entity")
    def cascade_remove_parameter_values_by_entity(self, db_map_data):
        """Removes parameter values in cascade when removing entity classes when removing entities.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_values_by_entity(self._to_ids(db_map_data))
        if any(db_map_cascading_data.values()):
            self.parameter_values_removed.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_remove_parameter_values_by_definition")
    def cascade_remove_parameter_values_by_definition(self, db_map_data):
        """Removes parameter values in cascade when when removing parameter definitions.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_values_by_definition(self._to_ids(db_map_data))
        if any(db_map_cascading_data.values()):
            self.parameter_values_removed.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_refresh_relationship_classes")
    def cascade_refresh_relationship_classes(self, db_map_data):
        """Refreshes cached relationship classes when updating object classes.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_relationship_classes(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_relationship_classes(db_map, ids=ids)
        self.relationship_classes_updated.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_refresh_relationships_by_object")
    def cascade_refresh_relationships_by_object(self, db_map_data):
        """Refreshed cached relationships in cascade when updating objects.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_relationships(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_relationships(db_map, ids=ids)
        self.relationships_updated.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_refresh_parameter_definitions")
    def cascade_refresh_parameter_definitions(self, db_map_data):
        """Refreshes cached parameter definitions in cascade when updating entity classes.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_data(self._to_ids(db_map_data), "parameter definition")
        if not any(db_map_cascading_data.values()):
            return
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_parameter_definitions(db_map, ids=ids)
        self.auto_refresh_parameter_definitions(db_map_cascading_data)

    @Slot("QVariant", name="cascade_refresh_parameter_definitions_by_value_list")
    def cascade_refresh_parameter_definitions_by_value_list(self, db_map_data):
        """Refreshes cached parameter definitions when updating parameter value lists.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_definitions_by_value_list(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_parameter_definitions(db_map, ids=ids)
        self.auto_refresh_parameter_definitions(db_map_cascading_data)

    @Slot("QVariant", name="cascade_refresh_parameter_definitions_by_tag")
    def cascade_refresh_parameter_definitions_by_tag(self, db_map_data):
        """Refreshes cached parameter definitions when updating parameter tags.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_definitions_by_tag(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_parameter_definitions(db_map, ids=ids)
        self.auto_refresh_parameter_definitions(db_map_cascading_data)

    @Slot("QVariant", name="cascade_refresh_parameter_values_by_entity_class")
    def cascade_refresh_parameter_values_by_entity_class(self, db_map_data):
        """Refreshes cached parameter values in cascade when updating entity classes.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_data(self._to_ids(db_map_data), "parameter value")
        if not any(db_map_cascading_data.values()):
            return
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_parameter_values(db_map, ids=ids)
        self.parameter_values_updated.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_refresh_parameter_values_by_entity")
    def cascade_refresh_parameter_values_by_entity(self, db_map_data):
        """Refreshes cached parameter values in cascade when updating entities.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_values_by_entity(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_parameter_values(db_map, ids=ids)
        self.parameter_values_updated.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_refresh_parameter_values_by_definition")
    def cascade_refresh_parameter_values_by_definition(self, db_map_data):
        """Refreshes cached parameter values in cascade when updating parameter definitions.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_values_by_definition(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_parameter_values(db_map, ids=ids)
        self.parameter_values_updated.emit(db_map_cascading_data)

    def find_cascading_relationship_classes(self, db_map_ids):
        """Finds and returns cascading relationship classes for the given object class ids."""
        db_map_cascading_data = dict()
        for db_map, object_class_ids in db_map_ids.items():
            object_class_ids = {str(id_) for id_ in object_class_ids}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "relationship class")
                if object_class_ids.intersection(item["object_class_id_list"].split(","))
            ]
        return db_map_cascading_data

    def find_cascading_entities(self, db_map_ids, item_type):
        """Finds and returns cascading entities for the given entity class ids."""
        db_map_cascading_data = dict()
        for db_map, class_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, item_type) if item["class_id"] in class_ids
            ]
        return db_map_cascading_data

    def find_cascading_relationships(self, db_map_ids):
        """Finds and returns cascading relationships for the given object ids."""
        db_map_cascading_data = dict()
        for db_map, object_ids in db_map_ids.items():
            object_ids = {str(id_) for id_ in object_ids}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "relationship")
                if object_ids.intersection(item["object_id_list"].split(","))
            ]
        return db_map_cascading_data

    def find_cascading_parameter_data(self, db_map_ids, item_type):
        """Finds and returns cascading parameter definitions or values for the given entity class ids."""
        db_map_cascading_data = dict()
        for db_map, entity_class_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, item_type)
                if entity_class_ids.intersection([item.get("object_class_id"), item.get("relationship_class_id")])
            ]
        return db_map_cascading_data

    def find_cascading_parameter_definitions_by_value_list(self, db_map_ids):
        """Finds and returns cascading parameter definitions for the given parameter value list ids."""
        db_map_cascading_data = dict()
        for db_map, value_list_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "parameter definition")
                if item["value_list_id"] in value_list_ids
            ]
        return db_map_cascading_data

    def find_cascading_parameter_definitions_by_tag(self, db_map_ids):
        """Finds and returns cascading parameter definitions for the given parameter tag ids."""
        db_map_cascading_data = dict()
        for db_map, tag_ids in db_map_ids.items():
            tag_ids = {str(id_) for id_ in tag_ids}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "parameter definition")
                if tag_ids.intersection((item["parameter_tag_id_list"] or "0").split(","))
            ]  # NOTE: 0 is 'untagged'
        return db_map_cascading_data

    def find_cascading_parameter_values_by_entity(self, db_map_ids):
        """Finds and returns cascading parameter values for the given entity ids."""
        db_map_cascading_data = dict()
        for db_map, entity_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "parameter value")
                if entity_ids.intersection([item.get("object_id"), item.get("relationship_id")])
            ]
        return db_map_cascading_data

    def find_cascading_parameter_values_by_definition(self, db_map_ids):
        """Finds and returns cascading parameter values for the given parameter definition ids."""
        db_map_cascading_data = dict()
        for db_map, definition_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, "parameter value") if item["parameter_id"] in definition_ids
            ]
        return db_map_cascading_data

    @Slot("QVariant", name="refresh_parameter_definitions")
    def auto_refresh_parameter_definitions(self, db_map_data):
        """Refreshes cached parameter definitions when updating parameter definitions in the db.
        This is needed because parameter definitions are cached in a 'extended' format
        that includes information about the entity, tags, value lists

        Args:
            db_map_data (dict): lists of parameter definition items keyed by DiffDatabaseMapping
        """
        for db_map, items in db_map_data.items():
            self.get_parameter_definitions(db_map, ids={x["id"] for x in items})

    @Slot("QVariant", name="auto_refresh_parameter_values")
    def auto_refresh_parameter_values(self, db_map_data):
        """Refreshes cached parameter values when updating parameter definitions in the db.
        This is needed because parameter values are cached in a 'extended' format
        that includes information about the entity, etc.

        Args:
            db_map_data (dict): lists of parameter value items keyed by DiffDatabaseMapping
        """
        for db_map, items in db_map_data.items():
            self.get_parameter_values(db_map, ids={x["id"] for x in items})

    @Slot("QVariant", name="cache_parameter_definition_tags")
    def cache_parameter_definition_tags(self, db_map_data):
        """Caches parameter definition tags in the parameter definition dictionary.

        Args:
            db_map_data (dict): lists of parameter definition items keyed by DiffDatabaseMapping
        """
        for items in db_map_data.values():
            for item in items:
                item["id"] = item.pop("parameter_definition_id")
        self.cache_items("parameter definition", db_map_data)
