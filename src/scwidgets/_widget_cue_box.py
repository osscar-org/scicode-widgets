import ipywidgets
import functools

class CueBox(ipywidgets.Box):
    def __init__(self, widget_to_observe, trait_to_observe, widget_to_cue=None, css_style=None, *args, **kwargs):
        self._css_style = css_style
        self._widget_to_cue = widget_to_observe if (widget_to_cue is None) else widget_to_cue
        self._widget_to_observe = widget_to_observe
        self._trait_to_observe = trait_to_observe
        self._css_style = css_style
        super().__init__([self._widget_to_cue], *args, **kwargs)
        self._widget_to_observe.observe(self._on_trait_change, trait_to_observe)
        self.add_class(f"{self._css_style['__init__']}")
        self.add_class(self._css_style['_on_trait_change'])

    @property
    def widget_to_observe(self):
        return self._widget_to_observe

    @property
    def trait_to_observe(self):
        return self._trait_to_observe

    @property
    def widget_to_cue(self):
        return self._widget_to_cue

    def _on_trait_change(self, change=None):
        self.add_class(self._css_style['_on_trait_change'])

    def remove_cue(self):
        self.remove_class(self._css_style['_on_trait_change'])

SaveCueBox = functools.partial(CueBox, css_style={
                      '__init__': 'scwidget-save-cue-box',
                      '_on_trait_change': 'scwidget-save-cue-box--on-trait-change'})

CheckCueBox = functools.partial(CueBox, css_style={
                      '__init__': 'scwidget-check-cue-box',
                      '_on_trait_change': 'scwidget-check-cue-box--on-trait-change'})

UpdateCueBox = functools.partial(CueBox, css_style={
                      '__init__': 'scwidget-update-cue-box',
                      '_on_trait_change': 'scwidget-update-cue-box--on-trait-change'})
