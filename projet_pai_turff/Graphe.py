from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget


class Graphe(QWidget):
    """
    Widget Qt pour afficher des graphiques matplotlib.
    Supporte plot, hist, bar, scatter.
    """

    def __init__(
        self, title="Pas de titre", xlabel="X", ylabel="Y", parent=None, layout=None
    ):
        """
        Args:
            title (str): Titre par défaut du graphique
            xlabel (str): Label par défaut de l'axe X
            ylabel (str): Label par défaut de l'axe Y
            parent (QWidget, optional): Widget parent. Par défaut None.
            layout (QLayout, optional): Layout dans lequel insérer le canvas. Si None, le canvas est ajouté directement au widget. Par défaut None.
        """
        super().__init__(parent)

        self.default_title = title
        self.default_xlabel = xlabel
        self.default_ylabel = ylabel

        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        if layout is not None:
            layout.addWidget(self.canvas, 4)
        else:
            vlayout = QVBoxLayout(self)
            vlayout.addWidget(self.canvas)

        self._setup_axes()

    # ------------------------
    # Outils internes
    # ------------------------

    def _setup_axes(self, title=None, xlabel=None, ylabel=None):
        """Configure les axes du graphique avec les titres et labels spécifiés ou par défaut."""
        self.ax.set_aspect("auto")
        self.ax.set_title(title or self.default_title)
        self.ax.set_xlabel(xlabel or self.default_xlabel)
        self.ax.set_ylabel(ylabel or self.default_ylabel)
        self.ax.grid(True)

    def clear(self):
        """Efface le graphique actuel pour préparer un nouveau tracé."""
        self.ax.clear()

    # ------------------------
    # Graphiques
    # ------------------------

    def plot(self, x, y, title=None, xlabel=None, ylabel=None, **kwargs):
        """Trace un graphique en ligne (plot) avec les données x et y, et les options de titre et labels.
        Args:
            x (list): Données pour l'axe X
            y (list): Données pour l'axe Y
            title (str, optional): Titre du graphique. Par défaut None (utilise le titre par défaut).
            xlabel (str, optional): Label de l'axe X. Par défaut None (utilise le label par défaut).
            ylabel (str, optional): Label de l'axe Y. Par défaut None (utilise le label par défaut).
        """
        self.clear()
        self._setup_axes(title, xlabel, ylabel)
        self.ax.plot(x, y, **kwargs)
        self.canvas.draw_idle()

    def hist(self, data, bins=10, title=None, xlabel=None, ylabel=None, **kwargs):
        """
        Trace un histogramme avec les données fournies, le nombre de bins, et les options de titre et labels.
        Args:
            x (list): Données pour l'axe X
            y (list): Données pour l'axe Y
            title (str, optional): Titre du graphique. Par défaut None (utilise le titre par défaut).
            xlabel (str, optional): Label de l'axe X. Par défaut None (utilise le label par défaut).
            ylabel (str, optional): Label de l'axe Y. Par défaut None (utilise le label par défaut).
        """
        self.clear()
        self._setup_axes(title, xlabel, ylabel)
        self.ax.hist(data, bins=bins, **kwargs)
        self.canvas.draw_idle()

    def bar(self, x, y, title=None, xlabel=None, ylabel=None, **kwargs):
        """Trace un graphique en barres avec les données x et y, et les options de titre et labels.
        Args:
            x (list): Données pour l'axe X
            y (list): Données pour l'axe Y
            title (str, optional): Titre du graphique. Par défaut None (utilise le titre par défaut).
            xlabel (str, optional): Label de l'axe X. Par défaut None (utilise le label par défaut).
            ylabel (str, optional): Label de l'axe Y. Par défaut None (utilise le label par défaut).
        """
        self.clear()
        self._setup_axes(title, xlabel, ylabel)
        self.ax.bar(x, y, **kwargs)
        self.canvas.draw_idle()

    def scatter(self, x, y, title=None, xlabel=None, ylabel=None, **kwargs):
        """Trace un graphique de dispersion (scatter) avec les données x et y, et les options de titre et labels.
        Args:
            x (list): Données pour l'axe X
            y (list): Données pour l'axe Y
            title (str, optional): Titre du graphique. Par défaut None (utilise le titre par défaut).
            xlabel (str, optional): Label de l'axe X. Par défaut None (utilise le label par défaut).
            ylabel (str, optional): Label de l'axe Y. Par défaut None (utilise le label par défaut).
        """
        self.clear()
        self._setup_axes(title, xlabel, ylabel)
        self.ax.scatter(x, y, **kwargs)
        self.canvas.draw_idle()
