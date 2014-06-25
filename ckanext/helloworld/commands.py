import sys
import re
import os.path
import json
import logging
import optparse
from optparse import make_option 

import ckan.model as model
import ckan.logic as logic

from ckan.logic import get_action, ValidationError

from ckan.lib.cli import CkanCommand

def parser_error(msg):
    '''Monkey-patch for optparse parser's error() method.
    This is used whenever we want to prevent the default exit() behaviour.
    '''
    raise ValueError(msg)

class CommandDispatcher(CkanCommand):
    '''
    This command should be invoked as below:

    paster [PASTER-OPTIONS] helloworld --config=../ckan/development.ini [COMMAND] [COMMAND-OPTIONS]

    '''

    summary = 'An entry point for helloworld-related Paster commands'
    usage = __doc__
    group_name = 'ckanext-helloworld'
    max_args = 15
    min_args = 0

    subcommand_usage = 'paster [PASTER-OPTIONS] helloworld --config INI_FILE %(name)s [OPTIONS]'

    subcommands = {
        'foo': { 
            'method_name': 'invoke_foo',
            'options': [
                make_option("-n", "--foo-name",
                    action="store", type="string", dest="foo_name"),
            ],
         },
        'baz': { 
            'method_name': 'invoke_baz',
            'options': [
                make_option("-n", "--baz-name",
                    action="store", type="string", dest="baz_name"),
            ],
         },
    }

    def __init__(self, name):
        CkanCommand.__init__(self, name)
        self.parser.disable_interspersed_args()        
        
    def command(self):
        self._load_config()
        self.logger = logging.getLogger('ckanext.helloworld')
        self.logger.setLevel(logging.INFO)
        
        self.logger.debug('Remaining args are ' + repr(self.args))
        self.logger.debug('Options are ' + repr(self.options))

        subcommand = self.args.pop(0)

        if subcommand in self.subcommands:
            spec = self.subcommands.get(subcommand)
            method_name = spec.get('method_name')
            assert method_name and hasattr(self, method_name), 'No method named %s' %(method_name) 
            method = getattr(self, method_name)
            parser = self.standard_parser()
            parser.set_usage(self.subcommand_usage %(dict(name=subcommand)))
            parser.error = parser_error
            parser.add_options(option_list=spec.get('options'))
            try:
                opts, args = parser.parse_args(args=self.args)
            except Exception as ex:
                self.logger.error('Bad options for subcommand %s: %s', subcommand, str(ex))
                print 
                print method.__doc__
                print
                parser.print_help()
                return
            else:
                self.logger.debug('Trying to invoke "%s" with: opts=%r, args=%s' %(
                    subcommand, opts, args))
                return method(opts, *args)
        else:
            self.logger.error('Unknown subcommand: %s' %(subcommand))
            print
            print 'The available helloworld commands are:'
            for k, spec in self.subcommands.items():
                method = getattr(self, spec['method_name'])    
                print '  %s: %s' %(k, method.__doc__.split("\n")[0])
            return
    
    ## Subcommands

    def invoke_foo(self, opts, *args):
        '''Run foo command'''
        self.logger.info('Running "foo" with args: %r %r', opts, args)

    def invoke_baz(self, opts, *args):
        '''Run baz command'''
        self.logger.info('Running "baz" with args: %r %r', opts, args)

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

