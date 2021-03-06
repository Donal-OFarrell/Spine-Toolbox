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
Classes for custom QListView.

:author: M. Marin (KTH)
:date:   14.11.2018
"""

from PySide2.QtWidgets import QListView, QApplication
from PySide2.QtGui import QDrag
from PySide2.QtCore import Qt, QMimeData, Slot, QItemSelectionModel


class AutoFilterMenuView(QListView):
    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        # self.horizontalHeader().hide()
        self.setMouseTracking(True)
        self.entered.connect(self._handle_entered)
        self.clicked.connect(self._handle_clicked)

    def keyPressEvent(self, event):
        """Toggle checked state of current index if the user presses the Space key."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Space:
            index = self.currentIndex()
            self.model().toggle_checked_state(index)

    def leaveEvent(self, event):
        """Clear selection."""
        self.selectionModel().clearSelection()
        event.accept()

    @Slot("QModelIndex", name="_handle_entered")
    def _handle_entered(self, index):
        """Highlight current row."""
        self.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)

    @Slot("QModelIndex", name="_handle_clicked")
    def _handle_clicked(self, index):
        """Toggle checked state of clicked index."""
        self.model().toggle_checked_state(index)


class DragListView(QListView):
    """Custom QListView class with dragging support.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None

    def mousePressEvent(self, event):
        """Register drag start position"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.pos())
            if not index.isValid() or index == index.model().new_index:
                self.drag_start_pos = None
                self.pixmap = None
                self.mime_data = None
                return
            self.drag_start_pos = event.pos()
            self.pixmap = index.data(Qt.DecorationRole).pixmap(self.iconSize())
            entity_class_id = index.data(Qt.UserRole + 1)
            self.mime_data = QMimeData()
            self.mime_data.setText(str(entity_class_id))

    def mouseMoveEvent(self, event):
        """Start dragging action if needed"""
        if not event.buttons() & Qt.LeftButton:
            return
        if not self.drag_start_pos:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        drag.setPixmap(self.pixmap)
        drag.setMimeData(self.mime_data)
        drag.setHotSpot(self.pixmap.rect().center())
        drag.exec_()
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        super().mouseReleaseEvent(event)
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None
