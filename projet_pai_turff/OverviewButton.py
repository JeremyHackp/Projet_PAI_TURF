from typing import Any, Callable, Optional, Dict

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QDialog,
    QScrollArea,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QTextDocument, QColor


class OverviewButton(QPushButton):
    """Un bouton affichant un aperçu d'une course ou d un participant avec ses caractéristiques principales.

    Clique sur ce bouton ouvre une fenêtre détaillée avec plus d'informations.
    """

    def __init__(
        self,
        id: Any,
        get_data: Callable[[Any], dict],
        donnees_a_afficher=None,
        detail_window_class=None,
        parent=None,
        bg_color: str = "#D0DEEA",
        shadow: bool = True,
        shadow_color: str = "#888888",
        shadow_blur: int = 24,
        shadow_offset: tuple[int, int] = (0, 6),
        # Font control
        font_size: int = 12,
        auto_scale: bool = False,
        min_font_size: int = 8,
        max_font_size: int = 20,
    ):
        """Initialise le bouton.

        Args:
            id: Identifiant unique de la course ou du participant (clé primaire).
            get_data: Fonction qui accepte id et retourne un dictionnaire
                           avec les caractéristiques de la course ou du participant.


            donnees_a_afficher: Dictionnaire optionnel spécifiant les champs à afficher
                              au format {cle_donnee: "Label à afficher"}
                              Ex: {'name': 'Nom', 'date': 'Date', 'place': 'Lieu'}
                              Si None, affiche tous les champs du dictionnaire retourné par get_data.
            parent: Parent Qt (optionnel).

            detail_window_class=None: Classe pour la fenêtre de détails.
        """
        super().__init__(parent)
        self.id = id
        self.get_data = get_data
        self.donnees_a_afficher = donnees_a_afficher
        self.data = None
        self.detail_window_class = detail_window_class
        self._detail_window = None
        # Styling options
        self.bg_color = bg_color
        self.shadow = shadow
        self.shadow_color = shadow_color
        self.shadow_blur = shadow_blur
        self.shadow_offset = shadow_offset
        # Font sizing options
        self.font_size = font_size
        self.auto_scale = auto_scale
        self.min_font_size = min_font_size
        self.max_font_size = max_font_size

        # Charger les données de la course/ du participant
        try:
            self.data = self.get_data(id)
        except Exception as e:
            self.data = {"error": str(e)}

        # Configurer l'apparence du bouton
        self._setup_ui()

        # Connecter le clic pour ouvrir la fenêtre détaillée
        self.clicked.connect(self._open_detail_window)

    def _setup_ui(self):
        """Configure l'interface du bouton avec les info de la course/ du participant."""
        if not self.data or "error" in self.data:
            self.setText(f"Course/participant #{self.id} - Erreur")
            return

        # Créer un widget personnalisé pour afficher un aperçu
        self.setText("")  # Pas de texte simple

        # Déterminer les données à afficher
        if self.donnees_a_afficher:
            # Utiliser seulement les clés spécifiées
            fields_to_display = self.donnees_a_afficher
        else:
            # Afficher tous les champs avec des labels générés automatiquement
            fields_to_display = {
                k: k.replace("_", " ").title() for k in self.data.keys() if k != "error"
            }

        # Créer les lignes d'info à afficher (HTML avec label en gras)
        html_lines = []
        for key, label in fields_to_display.items():
            value = self.data.get(key, "N/A")
            html_lines.append(f"<b>{label}:</b> {value}")

        display_html = "<br/>".join(html_lines)

        # Utiliser un QLabel enfant pour permettre le rendu RichText
        # et rendre le label transparent aux événements souris pour
        # laisser le QPushButton gérer le clic.
        if hasattr(self, "_content_label") and self._content_label is not None:
            self._content_label.setText(display_html)
        else:
            self._content_label = QLabel(self)
            self._content_label.setObjectName("overview_label")
            self._content_label.setTextFormat(Qt.RichText)
            self._content_label.setText(display_html)
            self._content_label.setWordWrap(True)
            # Rendre le label transparent pour éviter le carré blanc
            self._content_label.setStyleSheet(
                "background: transparent; color: #0b2540;"
            )
            # Forcer une taille de police sur le QLabel (le stylesheet du QPushButton
            # n'affecte pas le QLabel enfant quand il contient du rich text)
            try:
                label_font = QFont("Arial", 11)
                self._content_label.setFont(label_font)
            except Exception:
                pass
            self._content_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            try:
                # Certains styles remplissent le background; désactiver le auto-fill
                self._content_label.setAutoFillBackground(False)
                self._content_label.setAttribute(Qt.WA_TranslucentBackground, True)
            except Exception:
                pass
            # Layout pour contenir le label à l'intérieur du bouton
            layout = QHBoxLayout()
            layout.setAlignment(Qt.AlignLeft)
            layout.setContentsMargins(10, 6, 10, 6)
            layout.addWidget(self._content_label)
            # Si un layout existait, on le remplace
            try:
                old = self.layout()
                if old is not None:
                    # enlever tous les widgets de l'ancien layout
                    while old.count():
                        item = old.takeAt(0)
                        w = item.widget()
                        if w:
                            w.setParent(None)
            except Exception:
                pass
            self.setLayout(layout)
            # Defer a recalculation once the widget is laid out in its parent
            try:
                QTimer.singleShot(0, self._update_font_size)
            except Exception:
                pass
            # Update font sizing now that label exists
            self._update_font_size()

        # Style du bouton pour qu'il soit visible
        self.setStyleSheet(
            "QPushButton {"
            f"    background-color: {self.bg_color};"
            "    border: 1px solid #c8d6e0;"
            "    border-radius: 10px;"
            "    padding: 20px;"
            "    text-align: left;"
            "    font-family: Arial;"
            "    font-size: 12px;"
            "    color: #0b2540;"
            "}"
            "QPushButton:hover {"
            "    background-color: #C4D6E8;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #B0C7DF;"
            "}"
        )

        # Let buttons expand horizontally to fill the container width
        try:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass

        # Ombre portée optionnelle pour l'effet de carte
        if self.shadow:
            try:
                effect = QGraphicsDropShadowEffect(self)
                effect.setBlurRadius(self.shadow_blur)
                effect.setColor(QColor(self.shadow_color))
                effect.setOffset(*self.shadow_offset)
                self.setGraphicsEffect(effect)
            except Exception:
                # En cas d'environnement ne supportant pas l'effet, ignorer
                pass

    def _update_font_size(self):
        """Set the QLabel font size. If auto_scale is True, attempt to choose
        the largest font that fits the content within the button width.
        """
        if not hasattr(self, "_content_label") or self._content_label is None:
            return

        # If not auto-scaling, set explicit font size
        if not self.auto_scale:
            f = self._content_label.font()
            f.setPointSize(self.font_size)
            self._content_label.setFont(f)
            return

        # Auto-scale: try sizes from max down to min and pick first that fits
        # We'll use QTextDocument to measure rendered HTML height at a given width
        available_width = max(10, self.width() - 24)  # consider margins
        # account for layout margins if present
        try:
            lm = self.layout().contentsMargins()
            available_width = max(10, self.width() - (lm.left() + lm.right() + 24))
        except Exception:
            pass

        for size in range(self.max_font_size, self.min_font_size - 1, -1):
            test_font = self._content_label.font()
            test_font.setPointSize(size)

            doc = QTextDocument()
            doc.setDefaultFont(test_font)
            # set HTML content and width to compute layout height
            doc.setHtml(self._content_label.text())
            doc.setTextWidth(available_width)
            doc_height = doc.size().height()

            # if the document height fits within available widget height (or reasonable limit), accept
            # we allow up to some maximum (e.g., 6 lines worth) to avoid overly tall cards
            if doc_height <= self.maximumHeight() and doc_height > 0:
                # apply this font size and adjust heights
                test_font.setPointSize(size)
                self._content_label.setFont(test_font)
                # set label fixed height and button min height accordingly
                needed_height = int(doc_height) + 12
                try:
                    self._content_label.setFixedHeight(needed_height)
                except Exception:
                    pass
                # Compute required width to display without wrapping (ideal width)
                try:
                    unbounded = QTextDocument()
                    unbounded.setDefaultFont(test_font)
                    unbounded.setHtml(self._content_label.text())
                    # idealWidth gives intrinsic width for content
                    required_w = int(unbounded.idealWidth()) + 24
                except Exception:
                    required_w = self.minimumWidth()

                # Cap required width to 80% of parent or screen width to avoid runaway sizes
                try:
                    parent_w = self.parent().width() if self.parent() is not None else 0
                    if parent_w and parent_w > 0:
                        cap = int(parent_w * 0.8)
                    else:
                        from PySide6.QtWidgets import QApplication

                        cap = int(QApplication.primaryScreen().size().width() * 0.8)
                except Exception:
                    cap = required_w

                required_w = min(required_w, cap)

                try:
                    self.setMinimumWidth(required_w)
                    # set label width slightly smaller to respect margins
                    self._content_label.setFixedWidth(max(10, required_w - 24))
                except Exception:
                    pass

                # button min height: label height + vertical paddings
                padding_v = 28
                try:
                    lm = self.layout().contentsMargins()
                    padding_v += lm.top() + lm.bottom()
                except Exception:
                    pass
                self.setMinimumHeight(needed_height + padding_v)
                return

        # fallback to min size if nothing fit
        f = self._content_label.font()
        f.setPointSize(self.min_font_size)
        self._content_label.setFont(f)
        try:
            # adjust heights for min size
            doc = QTextDocument()
            doc.setDefaultFont(f)
            doc.setHtml(self._content_label.text())
            doc.setTextWidth(available_width)
            h = int(doc.size().height()) + 12
            self._content_label.setFixedHeight(h)
            padding_v = 28
            try:
                lm = self.layout().contentsMargins()
                padding_v += lm.top() + lm.bottom()
            except Exception:
                pass
            self.setMinimumHeight(h + padding_v)
        except Exception:
            pass

    def resizeEvent(self, event):
        # Recompute font size on resize when auto_scale is enabled
        try:
            self._update_font_size()
        except Exception:
            pass
        return super().resizeEvent(event)

    def showEvent(self, event):
        # When showing the widget, ensure sizing is correct (defer to allow layout)
        try:
            QTimer.singleShot(0, self._update_font_size)
        except Exception:
            pass
        return super().showEvent(event)

        # Fixer une hauteur minimale pour que le texte multiligne soit visible
        self.setMinimumHeight(80)
        self.setMinimumWidth(200)

    def set_bg_color(self, color: str):
        """Change la couleur de fond du 'card' et rafraîchit le style."""
        self.bg_color = color
        self._setup_ui()

    def enable_shadow(self, enabled: bool = True):
        """Active ou désactive l'ombre portée."""
        self.shadow = enabled
        self._setup_ui()

    def _open_detail_window(self):
        if not self.data or "error" in self.data:
            return

        if self.detail_window_class is None:
            return

        # éviter ouvrir 10 fenêtres
        if self._detail_window is None:
            self._detail_window = self.detail_window_class(id=self.id, parent=self)

        self._detail_window.show()
        self._detail_window.raise_()
        self._detail_window.activateWindow()
