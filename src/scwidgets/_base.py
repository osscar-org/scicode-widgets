import ipywidgets

class CueBox(ipywidgets.Box):
    def __init__(self, widget_to_observe, trait_to_observe, widget_to_cue=None, css_style=None, *args, **kwargs):
        self._css_style = css_style
        self._widget_to_cue = widget_to_observe if (widget_to_cue is None) else widget_to_cue
        self._widget_to_observe = widget_to_observe
        self._css_style = css_style
        super().__init__([self._widget_to_cue], *args, **kwargs)
        self._widget_to_observe.observe(self._on_trait_change, trait_to_observe)
        self.add_class(f"{self._css_style['__init__']}")

    @property
    def widget_to_observe(self):
        return self._widget_to_observe

    @property
    def widget_to_cue(self):
        return self._widget_to_cue

    def _on_trait_change(self, change=None):
        self.add_class(self._css_style['_on_trait_change'])

    def remove_cue(self):
        self.remove_class(self._css_style['_on_trait_change'])

SAVE_CUE = functools.partial(Cue, css_style={
                      '__init__': 'scwidget-answer-widget',
                      '_on_trait_change': 'scwidget-answer-widget--change__left'})

CHECK_CUE = functools.partial(Cue, css_style={
                      '__init__': 'scwidget-answer-widget',
                      '_on_trait_change': 'scwidget-answer-widget--change__left'})

UPDATE_CUE = functools.partial(Cue, css_style={
                      '__init__': 'scwidget-answer-widget',
                      '_on_trait_change': 'scwidget-answer-widget--change__left'})


class CueButton(ipywidgets.Button):
    def __init__(self, cue_boxes, on_click_action, css_style=None, *args, **kwargs):
        if not(isinstance(cue_boxes, list)):
            cue_boxes = [cue_boxes]

        self._cue_boxes = cue_boxes

        super().__init__(*args, **kwargs)

        for cue_box in self._cue_boxes:
            assert self._cue_boxes[0].widget_to_observe == cue_box.widget_to_observe, "all cue_boxes must have same widget_to_observe"
            assert iself._cue_boxes[0].trait_to_observe == cue_box.trait_to_observe, "all cue_boxes must have same trait_to_observe"
        self._cue_boxes[0].widget_to_observe.observe(self._on_trait_change, self._cue_boxes[0].trait_to_observe)

        self.on_click(self._on_click)

        self._on_click_action()

    #def _action(self):
    #    raise NotImplemented("_action is virtual, needs to be implemented")

    def _on_click(self, change=None):
        success = self._run()
        if success:
            for cue_box in self._cue_boxes:
                cue_box.remove_cue()
            self.disabled = True

    def _on_trait_change(self, change=None):
        self.disabled = False


class SaveButton(CueButton):
    def __init__(self, cue_boxes, save_registry, exercise_name, *args, **kwargs):
        self._save_registry = save_registry
        self._exercise_name = exercise_name

        css_style = {'__init__': 'scwidget-save-button',
                     '_on_trait_change': 'scwidget-save-button:disabled'}
        super().__init__(cue_boxes, css_style=css_style, *args, **kwargs)

    def _action(self):
        return self._save_registry.save(self._exercise_name)

class CheckButton(CueButton):
    def __init__(self, cue_boxes, check_registry, exercise_name, *args, **kwargs):
        self._check_registry = check_registry
        self._exercise_name = exercise_name

        css_style = {'__init__': 'scwidget-check-button',
                     '_on_trait_change': 'scwidget-check-button:disabled'}
        super().__init__(cue_boxes, css_style=css_style, *args, **kwargs)

    def _action(self):
        return self._check_registry.check(self._exercise_name)

class UpdateButton(CueButton):
    def __init__(self, cue_boxes, updatable_widget, *args, **kwargs):
        self._updatable_widget = updatable_widget

        css_style = {'__init__': 'scwidget-update-button',
                     '_on_trait_change': 'scwidget-update-button:disabled'}
        super().__init__(cue_boxes, css_style=css_style, *args, **kwargs)

    def _action(self):
        return self._updatable_widget.update()

#        self._widget.update()
#        self._save_registry.save(self._exercise_name)
#        self._check_registry.check(self._exercise_name)
