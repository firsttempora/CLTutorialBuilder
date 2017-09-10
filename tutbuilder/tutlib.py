from __future__ import print_function

import shlex

class AbstractClassInstance(Exception):
    pass

class AbstractClassMethod(AbstractClassInstance):
    pass


class TutorialAction(object):
    def __init__(self):
        raise AbstractClassInstance('TutorialAction is an abstract class and should not be instantiated directly')

    def intro(self):
        """
        This is the method that will be called by the tutorial master before this action occurs. It offers an opportunity
        to print information about a step.
        :return:
        """
        raise AbstractClassMethod('"intro" is an abstract method that should be overridden in a concrete class')

    def run(self):
        """
        This is the method that will be called by the tutorial master to execute this step of the tutorial.
        :return: True if the step completed successfully, False otherwise (if the user did the incorrect thing for example)
        """
        raise AbstractClassMethod('"run" is an abstract method that should be overridden in a concrete class')


class UserAction(TutorialAction):
    def __init__(self, test_function, intro=None, prompt='$ '):
        if isinstance(test_function, str):
            self.test = lambda cmd: UserAction.simple_check(cmd, test_function)
        else:
            self.test = test_function

        self.intro_string = intro
        self.prompt = prompt

    @staticmethod
    def simple_check(user_command, expected_command):
        return user_command.strip() == expected_command.strip()

    def intro(self):
        if self.intro_string is not None:
            print(self.intro_string)

    def run(self):
        """
        Prints a prompt and then
        :return:
        """