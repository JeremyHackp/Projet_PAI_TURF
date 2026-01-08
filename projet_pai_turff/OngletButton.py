from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QPushButton, QToolTip


def load_icon_pair(icon_path: Path) -> tuple[QIcon | None, QIcon | None]:
    """Load an icon and return (normal_icon, dark_icon).

    If the file does not exist or cannot be loaded, returns (None, None).
    """
    p = Path(icon_path)
    if not p.is_file():
        # try relative to this file
        p = Path(__file__).resolve().parent / p
        if not p.is_file():
            return None, None

    pix = QPixmap(str(p))
    if pix.isNull():
        return None, None

    normal = QIcon(pix)

    # Create a darkened version (semi-transparent black overlay)
    dark_pix = QPixmap(pix.size())
    dark_pix.fill(Qt.transparent)
    painter = QPainter(dark_pix)
    painter.drawPixmap(0, 0, pix)
    painter.fillRect(dark_pix.rect(), QColor(0, 0, 0, 140))
    painter.end()
    dark = QIcon(dark_pix)
    return normal, dark


class OngletButton(QPushButton):
    """A QPushButton that wraps an icon (normal + dark) and tooltip behavior.

    Usage:
        btn = OngletButton('assets/courses.png', 'Courses récentes', icon_size=QSize(64,64))
        btn.set_active(True)  # switch to dark icon
    """

    def __init__(
        self,
        icon_path: str | Path,
        label: str = "",
        parent=None,
        icon_size: QSize = QSize(64, 64),
        tooltip: str | None = None,
    ):
        super().__init__(parent)
        self._icon_size = icon_size
        self._label = label

        normal, dark = load_icon_pair(Path(icon_path))
        self._normal_icon = normal
        self._dark_icon = dark

        if normal:
            self.setIcon(normal)
            self.setIconSize(self._icon_size)
            self.setToolTip(tooltip or label)
            self.setFixedSize(
                self._icon_size.width() + 20, self._icon_size.height() + 20
            )
        else:
            # fallback to text if no icon
            self.setText(label)

        # keep flat look by default (no button border)
        self.setFlat(True)

    def set_active(self, active: bool) -> None:
        """Toggle between normal and dark icon for active state."""
        if active and self._dark_icon:
            self.setIcon(self._dark_icon)
        elif self._normal_icon:
            self.setIcon(self._normal_icon)

    def enterEvent(self, event):
        tip = self.toolTip()
        if tip:
            QToolTip.showText(self.mapToGlobal(self.rect().center()), tip, self)
        super().enterEvent(event)
