from __future__ import print_function

import os
import shlex
import shutil
from six.moves import input
import subprocess
import tempfile

class AbstractClassInstance(Exception):
    pass


class AbstractClassMethod(AbstractClassInstance):
    pass


def _standard_exit_hook():
    print('Congratulations! You have completed the tutorial.')
    print('Goodbye.')


class TutorialMaster(object):
    def __init__(self, exit_hook=_standard_exit_hook, scratch_prefix=None):
        self.actions = []
        self.stop = exit_hook
        self._setup_scratch_dir(scratch_prefix=scratch_prefix)

    def _setup_scratch_dir(self, lesson_template_dir, scratch_prefix):
        self.scratch_dir = tempfile.mkdtemp(prefix=scratch_prefix)
        for obj in os.listdir(lesson_template_dir):
            shutil.copytree(os.path.join(lesson_template_dir, obj), os.path.join(self.scratch_dir, obj), symlinks=True)

    def add_action(self, action):
        if not isinstance(action, TutorialAction):
            raise TypeError('action must derive from TutorialAction')

        action.tutorial_master = self
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

    @staticmethod
    def _check_exec_dir(scratch_dir, exec_dir):
        scratch_dir = os.path.abspath(os.path.realpath(scratch_dir))
        exec_dir = os.path.abspath(os.path.realpath(exec_dir))
        if not exec_dir.startswith(scratch_dir):
            raise RuntimeError('Cannot have code executing outside of the scratch directory')

    @staticmethod
    def _check_args_dirs(scratch_dir, user_cmd):
        if isinstance(user_cmd, str):
            user_cmd = shlex.split(user_cmd)
        elif not isinstance(user_cmd, list) or any([not isinstance(el, str) for el in user_cmd]):
            raise TypeError('user_cmd must be a string or list of strings')

        for arg in user_cmd:
            # Using shlex.split here should ensure that any quotes are removed, since, e.g. '"/"'
            # would not test as a directory
            arg_tmp = shlex.split(arg)
            if len(arg_tmp) > 1:
                TutorialAction._check_args_dirs(scratch_dir, arg_tmp)
                return
            else:
                arg_parsed = arg_tmp[0]

            if os.path.isdir(arg_parsed) or os.path.isfile(arg_parsed):
                real_path = os.path.abspath(os.path.realpath(arg_parsed))
                if not real_path.startswith(scratch_dir):
                    raise RuntimeError('User input argument "{}" appears to reference a directory or file outside the '
                                       'scratch directory'.format(arg))


class UserAction(TutorialAction):
    def __init__(self, test_function, intro_str=None, onfail_str=None, hints=None,
                 postaction_str=None, prompt='$ ', execute=False, execute_dir='.'):
        """
        A class representing an action a user must take to advance the tutorial.
        :param test_function: how the action knows that the user has entered the correct input. Can be a string or a
        function. If given as a string, then this instance will compare the user's input to the string after stripping
        leading and trailing whitespace and, if they are equal, will judge the action to be completed successfully.
        If given a function, the user's input will be passed to it as the sole input. The function must return True or
        False, depending if the user gave the correct command. This might be useful if there is some flexibility to what
        the exact correct command is, i.e. if you are doing a Bash tutorial and want the user to "ls -lsh" any single
        file in the current directory.
        :param intro_str: optional, if given, the string that will be printed before the user is given a chance to try
        this action.
        :param onfail_str: optional, if given, the string that will be printed each time the user fails to complete the
        action correctly.
        :param hints: a dictionary with integers as keys and strings as values. Each time the user fails the action,
        this instance will be told how many attempts the user has made and will print the hint string for the greatest
        key that is <= the number of attempts. The first failure is attempt 0. As an example, if hints = {0: 'Look up
        the "du" command', 2:'The command is "du -hs"'}, then the first two times the user entered the wrong command
        the first hint is printed, after that, the second is.
        :param postaction_str: optional, if given, the string that will be printed after the user successfully completes
        the action.
        :param prompt: optional, the string that begins lines on which the user may enter input. Default is '$ '
        :param execute: controls whether the user command will be executed. Default is false, i.e. the user command will
        not be executed at all. If set to True, the user input will be parsed using shlex into a list of commands and
        executed with subprocess.check_call in the scratch directory provided by the tutorial master. This can also be a
        list of strings or a string, in which case that exact command will be executed (in the latter case, with shell=True).
        :param execute_dir: the directory, relative to the scratch directory provided by the tutorial master.
        :return:
        """
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

        if not isinstance(execute, (bool, list)):
            raise TypeError('execute must be a boolean or a list')
        elif isinstance(execute, list):
            if any([not isinstance(el, str) for el in execute]):
                raise TypeError('If a list, all elements of execute must be strings')

        if not isinstance(execute_dir, str):
            raise TypeError('execute_dir must be a string')

        self.intro_string = intro_str
        self.failure_string = onfail_str
        self.post_string = postaction_str
        self.prompt = prompt
        self.hints = hints if hints is not None else dict()
        self.do_execute = execute
        self.execute_dir = execute_dir

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
        ans_correct = self.test(user_ans)

        try:
            exec_dir = os.path.join(self.tutorial_master, self.execute_dir)
        except AttributeError:
            # TODO: make sure this raises from the AttributeError
            raise RuntimeError('It appears that the tutorial_master is not set on this action')

        if self.do_execute: # this will execute if do_execute is True, a string, or a list
            self._check_args_dirs(self.tutorial_master.scratch_dir, exec_dir)
            if isinstance(self.do_execute, bool):
                cmd = shlex.split(user_ans)
                use_shell = False
            elif isinstance(self.do_execute, (list, str)):
                cmd = self.do_execute
                use_shell = isinstance(cmd, str)
            else:
                TypeError('self.do_execute must be a boolean, list, or string')

            self._check_args_dirs(self.tutorial_master.scratch_dir, cmd)
            subprocess.check_call(cmd, shell=use_shell, cwd=exec_dir)

        return ans_correct