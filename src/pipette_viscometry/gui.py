import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector, Button
import numpy as np
from .fitting import fit_span_data, FitResult
from .physics import calculate_viscosity, ViscoResults
from .config import Config
from .theme import Theme, FONT, format_value

# Status glyphs: shape distinguishes them, so state never rests on colour alone.
# Both are present in the UI sans stack (Segoe UI has no check mark or warning sign).
READY = "●"
WARN = "▲"


class FitState:
    def __init__(self, ax, color, title, theme: Theme):
        self.ax = ax
        self.color = color
        self.title = title
        self.theme = theme
        self.line = None
        self.markers = None
        self.raw_line = None
        self.fit: FitResult | None = None

    def update_fit(self, x: np.ndarray, y: np.ndarray, xmin: float, xmax: float):
        self.fit = fit_span_data(x, y, xmin, xmax)
        self._clear_marks()

        fit_x = np.array([self.fit.xmin, self.fit.xmax])
        fit_y = self.fit.slope * fit_x + self.fit.intercept

        self.line, = self.ax.plot(
            fit_x, fit_y, color=self.color, linewidth=2,
            solid_capstyle="round", zorder=5, label=self._legend_label(),
        )
        # >=8px end markers with a 2px surface ring so they stay legible on the trace.
        self.markers, = self.ax.plot(
            fit_x, fit_y, linestyle="none", marker="o", markersize=8,
            markerfacecolor=self.color, markeredgecolor=self.theme.surface,
            markeredgewidth=2, zorder=6,
        )
        self._refresh_legend()

    def _clear_marks(self):
        for artist in (self.line, self.markers):
            if artist is not None:
                artist.remove()
        self.line = None
        self.markers = None

    def _legend_label(self) -> str:
        return f"{self.title} fit  ·  m = {format_value(self.fit.slope)}"

    def _refresh_legend(self):
        # A single series needs no legend box; once a fit exists there are two.
        legend = self.ax.legend(
            loc="upper left", frameon=False, fontsize=9,
            labelcolor=self.theme.ink_secondary, handlelength=1.8,
            borderpad=0.0, borderaxespad=0.4, labelspacing=0.35,
        )
        for text in legend.get_texts():
            text.set_fontfamily(FONT)


class InteractiveFitter:
    def __init__(self, x: np.ndarray, y: np.ndarray, filename: str, config: Config,
                 theme: str | Theme | None = None):
        self.x = x
        self.y = y
        self.filename = filename
        self.config = config
        self.skipped = False
        self.aborted = False

        if isinstance(theme, Theme):
            self.theme = theme
        else:
            self.theme = Theme.named(theme or getattr(config, "theme", "light"))
        t = self.theme

        self.fig = plt.figure(figsize=(12, 7.5), facecolor=t.page)
        self.fig.canvas.manager.set_window_title(f"Pipette Viscometry — {filename}")

        gs = self.fig.add_gridspec(
            2, 2, width_ratios=[3.1, 1.0],
            left=0.065, right=0.985, top=0.835, bottom=0.145,
            hspace=0.28, wspace=0.09,
        )
        self.ax_asp = self.fig.add_subplot(gs[0, 0])
        self.ax_ret = self.fig.add_subplot(gs[1, 0], sharex=self.ax_asp)
        self.info_ax = self.fig.add_subplot(gs[:, 1])

        self._info_artists: list = []

        self._build_header()
        self.asp_state = FitState(self.ax_asp, t.asp, "Aspiration", t)
        self.ret_state = FitState(self.ax_ret, t.ret, "Retraction", t)
        for state in (self.asp_state, self.ret_state):
            self._style_axes(state)
        self.ax_asp.tick_params(labelbottom=False)
        self.ax_ret.set_xlabel("Frame", fontsize=9.5, color=t.ink_secondary,
                               fontfamily=FONT, labelpad=6)

        self._build_info_panel()
        self._build_selectors()
        self._build_controls()

        self._render_info()
        self._set_status("Drag across each panel to fit its linear region.", t.muted)

        self.fig.canvas.mpl_connect("key_press_event", self._on_key_press)

    # ---------- construction helpers ----------

    def _text(self, x, y, s, *, size=9.5, color=None, weight="normal",
              ha="left", va="baseline", ax=None):
        target = ax if ax is not None else self.fig
        transform = ax.transAxes if ax is not None else self.fig.transFigure
        return target.text(
            x, y, s, fontsize=size, color=color or self.theme.ink_secondary,
            fontweight=weight, ha=ha, va=va, fontfamily=FONT,
            transform=transform,
        )

    def _build_header(self):
        t = self.theme
        self._text(0.065, 0.955, self.filename, size=15, color=t.ink,
                   weight="semibold", va="top")
        self._text(
            0.065, 0.912,
            "Select the linear region in each panel  ·  "
            "drag the edges to adjust  ·  "
            "Enter accept  ·  X skip  ·  Esc abort",
            size=9, color=t.muted, va="top",
        )

    def _style_axes(self, state: FitState):
        t = self.theme
        ax = state.ax
        ax.set_facecolor(t.surface)
        ax.set_axisbelow(True)
        ax.grid(True, color=t.grid, linewidth=0.8, linestyle="-")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(t.axis)
            ax.spines[side].set_linewidth(1.0)
        ax.tick_params(colors=t.muted, labelsize=9, length=3, width=0.8, color=t.axis)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontfamily(FONT)

        ax.set_title(state.title, loc="left", color=t.ink, fontsize=11.5,
                     fontweight="semibold", fontfamily=FONT, pad=9)
        ax.set_ylabel("Position (µm)", fontsize=9.5, color=t.ink_secondary,
                      fontfamily=FONT, labelpad=6)

        state.raw_line, = ax.plot(
            self.x, self.y, linestyle="none", marker="o", markersize=3.2,
            markerfacecolor=t.raw, markeredgecolor="none", alpha=0.5,
            label="Raw trace", zorder=2,
        )

    def _build_info_panel(self):
        ax = self.info_ax
        ax.set_facecolor(self.theme.surface)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    def _build_selectors(self):
        self.span_asp = self._make_selector(self.asp_state)
        self.span_ret = self._make_selector(self.ret_state)

    def _make_selector(self, state: FitState) -> SpanSelector:
        return SpanSelector(
            state.ax,
            lambda xmin, xmax, s=state: self._on_select(s, xmin, xmax),
            "horizontal", useblit=True, interactive=True, drag_from_anywhere=True,
            props=dict(facecolor=state.color, alpha=0.12, edgecolor="none"),
            handle_props=dict(color=state.color, linewidth=1.5, alpha=0.9),
        )

    def _build_controls(self):
        t = self.theme
        pos = self.info_ax.get_position()
        gap = 0.012
        width = (pos.width - gap) / 2
        ax_skip = self.fig.add_axes([pos.x0, 0.045, width, 0.055])
        ax_done = self.fig.add_axes([pos.x0 + width + gap, 0.045, width, 0.055])

        self.btn_skip = Button(ax_skip, "Skip", color=t.btn_face, hovercolor=t.btn_hover)
        self.btn_done = Button(ax_done, "Done", color=t.asp, hovercolor=t.accent_hover)

        self._style_button(self.btn_skip, t.ink_secondary, border=t.axis)
        self._style_button(self.btn_done, "#ffffff", border=None)

        self.btn_done.on_clicked(self._on_done)
        self.btn_skip.on_clicked(self._on_skip)

        self.status_text = self._text(0.065, 0.072, "", size=9.5, va="center")

    def _style_button(self, button: Button, label_color: str, border: str | None):
        button.label.set_color(label_color)
        button.label.set_fontsize(10)
        button.label.set_fontweight("semibold")
        button.label.set_fontfamily(FONT)
        for spine in button.ax.spines.values():
            spine.set_visible(border is not None)
            if border is not None:
                spine.set_color(border)
                spine.set_linewidth(1.0)

    # ---------- info panel rendering ----------

    def _set_status(self, message: str, color: str):
        self.status_text.set_text(message)
        self.status_text.set_color(color)

    def _clear_info(self):
        for artist in self._info_artists:
            artist.remove()
        self._info_artists = []

    def _info_text(self, x, y, s, **kwargs):
        artist = self._text(x, y, s, ax=self.info_ax, va="center", **kwargs)
        self._info_artists.append(artist)
        return artist

    def _section(self, y, label):
        self._info_text(0.09, y, label.upper(), size=8, color=self.theme.muted,
                        weight="bold")

    def _slope_block(self, y, state: FitState):
        t = self.theme
        key, = self.info_ax.plot(
            [0.045, 0.075], [y, y], color=state.color, linewidth=2.5,
            solid_capstyle="round", transform=self.info_ax.transAxes,
        )
        self._info_artists.append(key)
        self._info_text(0.10, y, f"{state.title} slope", size=9, color=t.ink_secondary)

        fit = state.fit
        self._info_text(0.09, y - 0.048, format_value(fit.slope) if fit else "—",
                        size=15, color=t.ink if fit else t.muted, weight="semibold")
        meta = (f"n = {fit.n_points} pts  ·  frames {fit.xmin:.0f}–{fit.xmax:.0f}"
                if fit else "not selected")
        self._info_text(0.09, y - 0.088, meta, size=8.5, color=t.muted)

    def _derived_block(self, y, symbol, name, value, *, hero=False):
        t = self.theme
        self._info_text(0.09, y, f"{symbol}   {name}", size=9, color=t.ink_secondary)
        self._info_text(
            0.09, y - (0.072 if hero else 0.048), format_value(value),
            size=26 if (hero and value is not None) else 15,
            color=t.ink if value is not None else t.muted, weight="semibold",
        )

    def _render_info(self):
        t = self.theme
        self._clear_info()

        self._section(0.965, "Measured slopes")
        self._slope_block(0.905, self.asp_state)
        self._slope_block(0.755, self.ret_state)

        divider, = self.info_ax.plot(
            [0.045, 0.955], [0.635, 0.635], color=t.grid, linewidth=1.0,
            transform=self.info_ax.transAxes,
        )
        self._info_artists.append(divider)

        self._section(0.585, "Derived quantities")
        results, error = self._current_results()
        if error:
            self._info_text(0.51, 0.51, f"{WARN}  {error}", size=9, color=t.critical)
        else:
            self._derived_block(0.520, "η", "viscosity (Pa.s)",
                                results.eta if results else None, hero=True)
            self._derived_block(0.345, "Pc", "critical pressure (Pa)",
                                results.Pc if results else None)
            self._derived_block(0.215, "γ", "surface tension (Pa)",
                                results.gamma if results else None)

    def _current_results(self) -> tuple[ViscoResults | None, str | None]:
        if not (self.asp_state.fit and self.ret_state.fit):
            return None, None
        try:
            return self._compute(), None
        except ValueError as exc:
            return None, str(exc)

    def _compute(self) -> ViscoResults:
        return calculate_viscosity(
            self.asp_state.fit.slope,
            self.ret_state.fit.slope,
            self.config.instrument.Rp,
            self.config.instrument.P_default,
            self.config.instrument.Rcac,
        )

    # ---------- events ----------

    def _on_select(self, state: FitState, xmin: float, xmax: float):
        try:
            state.update_fit(self.x, self.y, xmin, xmax)
        except ValueError as exc:
            self._set_status(f"{WARN}  {exc}", self.theme.critical)
        else:
            self._update_live_display()
        self.fig.canvas.draw_idle()

    def _update_live_display(self):
        self._render_info()
        if self.asp_state.fit and self.ret_state.fit:
            self._set_status(f"{READY}  Both spans fitted — press Done to accept.",
                             self.theme.good)
        else:
            missing = "retraction" if self.asp_state.fit else "aspiration"
            self._set_status(f"Now select the {missing} span.", self.theme.muted)

    def _on_done(self, event):
        if not self.asp_state.fit or not self.ret_state.fit:
            self._set_status(f"{WARN}  Select a span in both panels first.",
                             self.theme.critical)
            self.fig.canvas.draw_idle()
            return
        plt.close(self.fig)

    def _on_skip(self, event):
        self.skipped = True
        plt.close(self.fig)

    def _on_key_press(self, event):
        if event.key in ("x", "X"):
            self._on_skip(event)
        elif event.key == "escape":
            try:
                answer = input("Abort remaining batch? [y/N] ").strip().lower()
            except EOFError:
                answer = ""
            if answer in ("y", "yes"):
                self.aborted = True
                plt.close(self.fig)
            else:
                self._set_status("Abort cancelled.", self.theme.muted)
                self.fig.canvas.draw_idle()
        elif event.key == "enter":
            self._on_done(event)

    def show(self) -> tuple[bool, bool, ViscoResults | None, FitResult | None, FitResult | None]:
        plt.show()
        if self.skipped or self.aborted or not (self.asp_state.fit and self.ret_state.fit):
            return self.skipped, self.aborted, None, self.asp_state.fit, self.ret_state.fit

        return False, False, self._compute(), self.asp_state.fit, self.ret_state.fit
