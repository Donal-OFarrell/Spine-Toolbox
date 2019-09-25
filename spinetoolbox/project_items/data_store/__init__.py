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
Data store plugin.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from project_items.data_store.ui.data_store_properties import Ui_Form
from project_items.data_store.data_store import DataStore
from project_items.data_store.data_store_icon import DataStoreIcon
from project_items.data_store.widgets.data_store_properties_widget import DataStorePropertiesWidget
from project_items.data_store.widgets.add_data_store_widget import AddDataStoreWidget

item_rank = 0
item_category = "Data Stores"
item_type = "Data Store"
item_icon = ":/icons/project_item_icons/database.svg"
item_maker = DataStore
icon_maker = DataStoreIcon
properties_widget_maker = DataStorePropertiesWidget
add_form_maker = AddDataStoreWidget