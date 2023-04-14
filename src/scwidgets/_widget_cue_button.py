import ipywidgets
import functools

class CueButton(ipywidgets.Button):
    def __init__(self, cue_boxes, on_click_action, css_style, disable_after_succesful_action=True, *args, **kwargs):
        self._css_style =  css_style
        self._on_click_action = on_click_action
        self._disable_after_succesful_action = disable_after_succesful_action

        if not(isinstance(cue_boxes, list)):
            cue_boxes = [cue_boxes]

        self._cue_boxes = cue_boxes

        super().__init__(*args, **kwargs)
        self.add_class(self._css_style['__init__'])
        self.add_class(self._css_style['_on_disabled'])
        self.add_class(self._css_style['_on_trait_change'])

        # TODO change this to unique
        for cue_box in self._cue_boxes:
            assert self._cue_boxes[0].widget_to_observe == cue_box.widget_to_observe, "all cue_boxes must have same widget_to_observe"
            assert self._cue_boxes[0].trait_to_observe == cue_box.trait_to_observe, "all cue_boxes must have same trait_to_observe"
        self._cue_boxes[0].widget_to_observe.observe(self._on_trait_change, self._cue_boxes[0].trait_to_observe)

        self.on_click(self._on_click)

    def _on_click(self, change=None):
        success = self._on_click_action()
        if success:
            self.remove_class(self._css_style['_on_trait_change'])
            for cue_box in self._cue_boxes:
                cue_box.remove_cue()
            if self._disable_after_succesful_action:
                self.disabled = True

    def _on_trait_change(self, change=None):
        self.disabled = False
        self.add_class(self._css_style['_on_trait_change'])

class SaveCueButton(CueButton):
    def __init__(self, cue_boxes, save_registry, exercise_name, *args, **kwargs):
        css_style = {'__init__': 'scwidget-save-cue-button',
                     '_on_disabled': 'scwidget-save-cue-button:disabled',
                     '_on_trait_change': 'scwidget-save-cue-button--on_trait_change'}
        action = functools.partial(save_registry.save, exercise_name)
        if 'description' not in kwargs.keys():
            kwargs['description'] = 'Save'
        super().__init__(cue_boxes, action, css_style=css_style, *args, **kwargs)

class CheckCueButton(CueButton):
    def __init__(self, cue_boxes, check_registry, exercise_name, *args, **kwargs):
        css_style = {'__init__': 'scwidget-check-cue-button',
                     '_on_disabled': 'scwidget-check-cue-button:disabled',
                     '_on_trait_change': 'scwidget-check-cue-button--on_trait_change'}
        action = functools.partial(check_registry.check_widget_outputs, exercise_name)
        if 'description' not in kwargs.keys():
            kwargs['description'] = 'Check'
        super().__init__(cue_boxes, action, css_style=css_style, *args, **kwargs)

class UpdateCueButton(CueButton):
    def __init__(self, cue_boxes, update_function, *args, **kwargs):
        css_style = {'__init__': 'scwidget-update-cue-button',
                     '_on_disabled': 'scwidget-update-cue-button:disabled',
                     '_on_trait_change': 'scwidget-update-cue-button--on_trait_change'}
        if 'description' not in kwargs.keys():
            kwargs['description'] = 'Update'
        super().__init__(cue_boxes, update_function, css_style=css_style, *args, **kwargs)
