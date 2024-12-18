import glob
import json
import os
from tempfile import TemporaryDirectory
from typing import Union

import pytest

from scwidgets.exercise import ExerciseRegistry, ExerciseWidget


def mock_answer_widget(answer_registry: ExerciseRegistry, exercise_key: str):
    class MockExerciseWidget(ExerciseWidget):
        def __init__(self, answer_registry: ExerciseRegistry, exercise_key: str):
            super().__init__(answer_registry, exercise_key)
            self._answer = "answer"

        @property
        def answer(self) -> str:
            return self._answer

        @answer.setter
        def answer(self, answer: str):
            self._answer = answer

        def handle_save_result(self, result: Union[str, Exception]):
            pass

        def handle_load_result(self, result: Union[str, Exception]):
            pass

    return MockExerciseWidget(answer_registry, exercise_key)


class TestExerciseRegistry:
    prefix = "pytest"
    student_name = "test-answer-registry"
    tmp_dir = None

    @classmethod
    def setup_class(cls):
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        cls.tmp_dir = TemporaryDirectory()

    @classmethod
    def teardown_class(cls):
        """teardown any state that was previously setup with a call to
        setup_class.
        """
        cls.tmp_dir.cleanup()

    def setup_method(self, method):
        """setup any state tied to the execution of the given method in a
        class.  setup_method is invoked for every test method of a class.
        """
        # in case the test stopped unexpectedly and the file still exists from last
        # run
        for filename in glob.glob(os.getcwd() + f"/{self.prefix}-*.json"):
            os.remove(filename)

    def teardown_method(self, method):
        """teardown any state that was previously setup with a setup_method
        call.
        """
        for filename in glob.glob(os.getcwd() + f"/{self.prefix}-*.json"):
            os.remove(filename)

    def test_create_new_file_from_dropdown(self):
        answers = {"exercise_1": "update", "exercise_2": "answer_2"}
        with open(f"{self.prefix}-{self.student_name}-2.json", "w") as answer_file:
            json.dump(answers, answer_file)

        answer_registry = ExerciseRegistry(filename_prefix=self.prefix)
        # test if existing file is selected on initialization
        assert (
            f"{self.prefix}-{self.student_name}-2.json"
            in answer_registry._answers_files_dropdown.options
        )

        exercise_key_1 = "exercise_1"
        answer_widget_1 = mock_answer_widget(answer_registry, exercise_key_1)
        answer_widget_1.answer = "answer_1"

        # simulating typing of name into text widget
        answer_registry._student_name_text.value = self.student_name
        assert not (os.path.exists(f"{self.prefix}-{self.student_name}.json"))
        answer_registry.create_new_file_from_dropdown()

        with open(f"{self.prefix}-{self.student_name}.json", "r") as answer_file:
            answers = json.load(answer_file)
        assert answers == {"exercise_1": "answer_1"}

        with pytest.raises(
            FileExistsError,
            match=r".*The name is already used for file "
            "'pytest-test-answer-registry.json'.*",
        ):
            answer_registry.create_new_file_from_dropdown()

    def test_save_answer(self):
        answer_registry = ExerciseRegistry(filename_prefix=self.prefix)

        with pytest.raises(
            KeyError,
            match=r".*There is no widget registered with exercise key 'notkey'.*",
        ):
            answer_registry.save_answer("notkey")

        exercise_key_1 = "exercise_1"
        answer_widget_1 = mock_answer_widget(answer_registry, exercise_key_1)
        answer_widget_1.answer = "answer_1"

        # Test if error is raised when no file is loaded
        with pytest.raises(FileNotFoundError, match=r".*No file has been loaded.*"):
            answer_registry.save_answer(exercise_key_1)

        # create file
        answer_registry._student_name_text.value = self.student_name
        answer_registry.create_new_file_from_dropdown()

        # Tests if error is raised on moved file
        os.rename(f"{self.prefix}-{self.student_name}.json", "tmp.json")
        with pytest.raises(
            FileNotFoundError, match=r".*Loaded file does not exist anymore.*"
        ):
            answer_registry.save_answer(exercise_key_1)
        os.rename("tmp.json", f"{self.prefix}-{self.student_name}.json")

        # Test that file is contains only the updated answer
        answer_widget_1.answer = "update"
        exercise_key_2 = "exercise_2"
        answer_widget_2 = mock_answer_widget(  # noqa: F841
            answer_registry, exercise_key_2
        )

        result = answer_registry.save_answer(exercise_key_1)
        assert (
            result == "Exercise has been saved in file "
            "'pytest-test-answer-registry.json'."
        )
        with open(f"{self.prefix}-{self.student_name}.json", "r") as answer_file:
            answers = json.load(answer_file)
        assert answers == {"exercise_1": "update"}

    def test_save_all_answers(self):
        answer_registry = ExerciseRegistry(filename_prefix=self.prefix)

        exercise_key_1 = "exercise_1"
        answer_widget_1 = mock_answer_widget(answer_registry, exercise_key_1)
        answer_widget_1.answer = "answer_1"

        # Test if error is raised when no file is loaded
        with pytest.raises(FileNotFoundError, match=r".*No file has been loaded.*"):
            answer_registry.save_answer(exercise_key_1)

        # create file
        answer_registry._student_name_text.value = self.student_name
        answer_registry.create_new_file_from_dropdown()

        # Tests if error is raised on moved file
        os.rename(f"{self.prefix}-{self.student_name}.json", "tmp.json")
        with pytest.raises(
            FileNotFoundError, match=r".*Loaded file does not exist anymore.*"
        ):
            answer_registry.save_answer(exercise_key_1)
        os.rename("tmp.json", f"{self.prefix}-{self.student_name}.json")

        # Test that file is contains all updated answers
        answer_widget_1.answer = "update"
        exercise_key_2 = "exercise_2"
        answer_widget_2 = mock_answer_widget(answer_registry, exercise_key_2)
        answer_widget_2.answer = "answer_2"

        result = answer_registry.save_all_answers()
        assert (
            result
            == "All answers were saved in file 'pytest-test-answer-registry.json'."
        )
        with open(f"{self.prefix}-{self.student_name}.json", "r") as answer_file:
            answers = json.load(answer_file)
        assert answers == {"exercise_1": "update", "exercise_2": "answer_2"}

    def test_load_file_from_dropdown(self):
        answers = {"exercise_1": "update_1", "exercise_2": "update_2"}
        with open(f"{self.prefix}-{self.student_name}.json", "w") as answer_file:
            json.dump(answers, answer_file)

        answer_registry = ExerciseRegistry(filename_prefix=self.prefix)
        # test if existing file is selected on initialization
        assert (
            f"{self.prefix}-{self.student_name}.json"
            in answer_registry._answers_files_dropdown.options
        )
        exercise_key_1 = "exercise_1"
        answer_widget_1 = mock_answer_widget(answer_registry, exercise_key_1)
        answer_widget_1.answer = "answer_1"

        # Test if error is raised when no file is loaded
        answer_registry._answers_files_dropdown.value = (
            answer_registry._create_new_file_dropdown_option()
        )
        with pytest.raises(
            ValueError, match=r".*No file has been selected in the dropdown list.*"
        ):
            answer_registry.load_file_from_dropdown()
        # select back file to load
        answer_registry._answers_files_dropdown.value = (
            f"{self.prefix}-{self.student_name}.json"
        )

        # Tests if error is raised on moved file
        os.rename(f"{self.prefix}-{self.student_name}.json", "tmp.json")
        with pytest.raises(
            FileNotFoundError,
            match=r".*The file 'pytest-test-answer-registry.json' does not exist.*",
        ):
            answer_registry.load_file_from_dropdown()
        os.rename("tmp.json", f"{self.prefix}-{self.student_name}.json")

        # Test that file is contains only the updated answer
        with pytest.raises(
            ValueError,
            match=r".*Your file contains an answer with key 'exercise_2' "
            r"with no corresponding registered widget.*",
        ):
            answer_registry.load_file_from_dropdown()

        exercise_key_2 = "exercise_2"
        answer_widget_2 = mock_answer_widget(answer_registry, exercise_key_2)
        answer_widget_2.answer = "answer_2"
        result = answer_registry.load_file_from_dropdown()
        assert (
            result == "All answers loaded from file 'pytest-test-answer-registry.json'."
        )
        assert answer_widget_1.answer == "update_1"
        assert answer_widget_2.answer == "update_2"

    def test_load_answer_from_loaded_file(self):
        answers = {"exercise_1": "answer_1", "exercise_2": "answer_2"}
        with open(f"{self.prefix}-{self.student_name}.json", "w") as answer_file:
            json.dump(answers, answer_file)

        answer_registry = ExerciseRegistry(filename_prefix=self.prefix)
        with pytest.raises(
            ValueError,
            match=r".*No file has been loaded*",
        ):
            answer_registry.load_answer_from_loaded_file("notkey")

        # To avoid the no loaded file error
        answer_registry._loaded_file_name = "some"
        with pytest.raises(
            KeyError,
            match=r".*There is no widget registered with exercise key 'notkey'.*",
        ):
            answer_registry.load_answer_from_loaded_file("notkey")
        answer_registry._loaded_file_name = None

        exercise_key_1 = "exercise_1"
        answer_widget_1 = mock_answer_widget(answer_registry, exercise_key_1)
        exercise_key_2 = "exercise_2"
        answer_widget_2 = mock_answer_widget(answer_registry, exercise_key_2)
        answer_widget_1.answer = "update_2"

        # Test if error is raised when no file is loaded
        answer_registry._answers_files_dropdown.value = (
            answer_registry._create_new_file_dropdown_option()
        )
        with pytest.raises(ValueError, match=r".*No file has been loaded.*"):
            answer_registry.load_answer_from_loaded_file(exercise_key_1)
        # select back file to load
        answer_registry._answers_files_dropdown.value = (
            f"{self.prefix}-{self.student_name}.json"
        )
        answer_registry.load_file_from_dropdown()

        # Tests if error is raised on moved file
        os.rename(f"{self.prefix}-{self.student_name}.json", "tmp.json")
        with pytest.raises(
            FileNotFoundError,
            match=r".*The file 'pytest-test-answer-registry.json' does not exist.*",
        ):
            answer_registry.load_answer_from_loaded_file(exercise_key_1)
        os.rename("tmp.json", f"{self.prefix}-{self.student_name}.json")

        # Test that file is contains only the updated answer
        answer_widget_1.answer = "update_1"
        answer_widget_2.answer = "update_2"
        result = answer_registry.load_answer_from_loaded_file(exercise_key_1)
        assert (
            result == "Exercise has been loaded from file "
            "'pytest-test-answer-registry.json'."
        )
        assert answer_widget_1.answer == "answer_1"
        assert answer_widget_2.answer == "update_2"
