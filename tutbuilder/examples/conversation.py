from .. import tutlib as tl

def setup_tutorial(default_fail='Nope, that\'s not right'):
    tmaster = tl.TutorialMaster()
    tmaster.add_action(tl.UserAction('Hello world!', intro_str='Say "Hello world!"', onfail_str=default_fail))
    tmaster.add_action(tl.UserAction('I am hungry.', intro_str='Say "I am hungry."', onfail_str=default_fail))
    tmaster.add_action(tl.UserAction('Goodbye world!', intro_str='Say "Goodbye world!', onfail_str=default_fail))
    return tmaster

setup_tutorial().start()