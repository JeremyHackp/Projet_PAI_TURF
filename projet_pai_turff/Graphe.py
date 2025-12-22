import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class Graphe(QWidget):
    """
    Widget Qt pour afficher des graphiques matplotlib.
    Supporte plot, hist, bar, scatter.
    """

    def __init__(
        self, title="Pas de titre", xlabel="X", ylabel="Y", parent=None, layout=None
    ):
        super().__init__(parent)

        self.default_title = title
        self.default_xlabel = xlabel
        self.default_ylabel = ylabel

        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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
        self.ax.set_aspect("auto")
        self.ax.set_title(title or self.default_title)
        self.ax.set_xlabel(xlabel or self.default_xlabel)
        self.ax.set_ylabel(ylabel or self.default_ylabel)
        self.ax.grid(True)

    def clear(self):
        self.ax.clear()

    # ------------------------
    # Graphiques
    # ------------------------

    def plot(self, x, y, title=None, xlabel=None, ylabel=None, **kwargs):
        self.clear()
        self._setup_axes(title, xlabel, ylabel)
        self.ax.plot(x, y, **kwargs)
        self.canvas.draw_idle()

    def hist(self, data, bins=10, title=None, xlabel=None, ylabel=None, **kwargs):
        self.clear()
        self._setup_axes(title, xlabel, ylabel)
        self.ax.hist(data, bins=bins, **kwargs)
        self.canvas.draw_idle()

    def bar(self, x, y, title=None, xlabel=None, ylabel=None, **kwargs):
        self.clear()
        self._setup_axes(title, xlabel, ylabel)
        self.ax.bar(x, y, **kwargs)
        self.canvas.draw_idle()

    def scatter(self, x, y, title=None, xlabel=None, ylabel=None, **kwargs):
        self.clear()
        self._setup_axes(title, xlabel, ylabel)
        self.ax.scatter(x, y, **kwargs)
        self.canvas.draw_idle()
