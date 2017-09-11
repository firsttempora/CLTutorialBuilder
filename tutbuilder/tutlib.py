from __future__ import print_function

import shlex
from six.moves import input


class AbstractClassInstance(Exception):
    pass


class AbstractClassMethod(AbstractClassInstance):
    pass


def _standard_exit_hook():
    print('Congratulations! You have completed the tutorial.')
    print('Goodbye.')


class TutorialMaster(object):
    def __init__(self, exit_hook=_standard_exit_hook):
        self.actions = []
        self.stop = exit_hook

    def add_action(self, action):
        if not isinstance(action, TutorialAction):
            raise TypeError('action must derive from TutorialAction')

        if len(self.actions) > 0:
            self.actions[-1].next_action = action
        self.actions.append(action)

    def start(self):
        next_action = self.actions[0]
        num_attempts = 0
        while True:
            next_action.hook_on_pre_action()
            action_success = next_action.run()

            if action_success:
                next_action.hook_on_post_action()
                num_attempts = 0
                try:
                    next_action = next_action.next_action
                except AttributeError:
                    break
            else:
                next_action.hook_on_fail_action(num_attempts=num_attempts)
                num_attempts += 1

        self.stop()


class TutorialAction(object):
    def __init__(self):
        raise AbstractClassInstance('TutorialAction is an abstract class and should not be instantiated directly')

    def hook_on_pre_action(self):
        """
        This is the method that will be called by the tutorial master before this action occurs. It offers an opportunity
        to print information about a step.
        :return: None
        """
        pass

    def hook_on_post_action(self):
        """
        This is the method that will be called after an action is completed successfully
        :return: None
        """
        pass

    def hook_on_fail_action(self, num_attempts):
        """
        This is the method that will be called each time an action fails, with the number of attempts
        the user has made. This can be helpful for issuing hints.
        :return:
        """
        pass

    def run(self):
        """
        This is the method that will be called by the tutorial master to execute this step of the tutorial.
        :return: True if the step completed successfully, False otherwise (if the user did the incorrect thing for example)
        """
        raise AbstractClassMethod('"run" is an abstract method that should be overridden in a concrete class')


class UserAction(TutorialAction):
    def __init__(self, test_function, intro_str=None, onfail_str=None, hints=None,
                 postaction_str=None, prompt='$ '):
        if isinstance(test_function, str):
            self.test = lambda cmd: UserAction.simple_check(cmd, test_function)
        else:
            self.test = test_function

        # Input type checking
        if intro_str is not None and not isinstance(intro_str, str):
            raise TypeError('intro_str must be a string (if given)')
        if onfail_str is not None and not isinstance(onfail_str, str):
            raise TypeError('onfail_str must be a string or None')
        if postaction_str is not None and not isinstance(postaction_str, str):
            raise TypeError('postaction_str must be a string (if given)')
        if not isinstance(prompt, str):
            raise TypeError('prompt must be a string')

        if hints is None:
            hints = dict()
        elif not isinstance(hints, dict):
            raise TypeError('hints must be a dict (if given)')
        elif any([not isinstance(k, int) for k in hints.keys()]):
            raise TypeError('All keys in the hints dict must be integers')
        elif any([not isinstance(v, str) for v in hints.values()]):
            raise TypeError('All values in the hints dict must be strings')

        self.intro_string = intro_str
        self.failure_string = onfail_str
        self.post_string = postaction_str
        self.prompt = prompt
        self.hints = hints if hints is not None else dict()

    @staticmethod
    def simple_check(user_command, expected_command):
        return user_command.strip() == expected_command.strip()

    def hook_on_pre_action(self):
        # Print a blank line to separate us from the last step
        print('')
        if self.intro_string is not None:
            print(self.intro_string)

    def hook_on_fail_action(self, num_attempts):
        """
        If this instance has a failure string, print it. Also, compare the number of attempts to
        the keys of the hints dictionary and print the message associated with the greatest key
        that is less than the number of attempts. I.e., if the user has made 3 attempts and the
        the hints dictionary has keys 0, 2, and 4, the message associated with key 2 will be printed.
        :param num_attempts: the number of attempts the user has made
        :return: none
        """
        if self.failure_string is not None:
            print(self.failure_string)

        hints_key = None
        for k in self.hints.keys():
            if num_attempts >= k and (hints_key is None or k > hints_key):
                hints_key = k
        if hints_key is not None:
            print(self.hints[hints_key])

    def hook_on_post_action(self):
        if self.post_string is not None:
            print(self.post_string)

    def run(self):
        """
        Prints a prompt and then waits for user input
        :return: True if user completed task successfully, False otherwise
        """
        user_ans = input(self.prompt)
        return self.test(user_ans)