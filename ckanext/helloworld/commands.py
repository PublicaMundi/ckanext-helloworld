import sys, re, os, os.path, json, logging

import ckan.model as model
import ckan.logic as logic

from ckan.logic import get_action, ValidationError

from ckan.lib.cli import CkanCommand

class Greet(CkanCommand):
    '''
    This is an example of a helloworld-specific paster command:

    The command should be invoked as below:

    paster [PASTER-OPTIONS] helloworld-greet --config=../ckan/development.ini [COMMAND-OPTIONS]

    '''

    summary = 'This is an example of a helloworld-specific paster command'
    usage = __doc__
    group_name = 'ckanext-helloworld'
    max_args = 10
    min_args = 0

    def __init__(self, name):
        CkanCommand.__init__(self, name)
        # Configure options parser
        self.parser.add_option('-t', '--to', dest='target', help='Specify target', type=str, default='World')

    def command(self):
        self._load_config()
        self.log = logging.getLogger(__name__)

        # Create a context for action api calls
        context = {'model':model,'session':model.Session,'ignore_auth':True}
        self.admin_user = get_action('get_site_user')(context,{})
        context.update({'user': self.admin_user.get('name')})

        self.log.info ('Remaining args are ' + repr(self.args))
        self.log.info ('Options are ' + repr(self.options))

        print 'Hello (' + self.options.target + ')'


