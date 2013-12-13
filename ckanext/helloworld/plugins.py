# Plugins for ckanext-helloworld

import json, jsonpickle, time

import logging

import ckan.model           as model
import ckan.plugins         as p
import ckan.plugins.toolkit as toolkit
import ckan.logic           as logic

import weberror

_t = toolkit._

log1 = logging.getLogger(__name__)

class DatasetForm(p.SingletonPlugin, toolkit.DefaultDatasetForm):
    ''' A plugin that provides some metadata fields and
    overrides the default dataset form
    '''
    p.implements(p.ITemplateHelpers)
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IDatasetForm, inherit=True)

    ## helper methods ## 

    MUSIC_GENRES = ['classical', 'rock', 'pop', 'heavy-metal', 'jazz', 'ethnic',]

    @classmethod
    def create_music_genres(cls):
        '''Create music genres vocabulary and tags, if they don't exist already.
        Note that you could also create the vocab and tags using CKAN's api,
        and once they are created you can edit them (add or remove items) using the api.
        '''
        user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
        context = {'user': user['name']}
        try:
            data = {'id': 'music_genres'}
            toolkit.get_action ('vocabulary_show') (context, data)
            log1.info("The music-genres vocabulary already exists. Skipping.")
        except toolkit.ObjectNotFound:
            log1.info("Creating vocab 'music_genres'")
            data = {'name': 'music_genres'}
            vocab = toolkit.get_action ('vocabulary_create') (context, data)
            for tag in cls.MUSIC_GENRES:
                log1.info("Adding tag {0} to vocab 'music_genres'".format(tag))
                data = {'name': tag, 'vocabulary_id': vocab['id']}
                toolkit.get_action ('tag_create') (context, data)

    @classmethod
    def music_genres(cls):
        '''Return the list of all existing genres from the music_genres vocabulary.'''
        cls.create_music_genres()
        try:
            music_genres = toolkit.get_action ('tag_list') (data_dict={ 'vocabulary_id': 'music_genres'})
            return music_genres
        except toolkit.ObjectNotFound:
            return None

    @classmethod
    def music_genres_options(cls):
        ''' This generator method is only usefull for creating select boxes. '''
        for name in cls.music_genres():
            yield { 'value': name, 'text': name }

    @classmethod
    def hello_world(cls):
        ''' This is our simple helper function. '''
        html = '<span>Hello World</span>'
        return p.toolkit.literal(html)

    @classmethod
    def organization_list_objects(cls, org_names = []):
        ''' Make a action-api call to fetch the a list of full dict objects (for each organization) '''
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user,
        }

        options = { 'all_fields': True }
        if org_names and len(org_names):
            t = type(org_names[0])
            if   t is str:
                options['organizations'] = org_names
            elif t is dict:
                options['organizations'] = map(lambda org: org.get('name'), org_names)

        return logic.get_action('organization_list') (context, options)

    @classmethod
    def organization_dict_objects(cls, org_names = []):
        ''' Similar to organization_list_objects but returns a dict keyed to the organization name. '''
        results = {}
        for org in cls.organization_list_objects(org_names):
            results[org['name']] = org
        return results

    @classmethod
    def debug_template_vars(cls, debug_info):
        ''' A debug helper similar to h.debug_full_info_as_list '''
        out = {}
        ignored_keys = [
            'c', 'app_globals', 'g', 'h', 'request', 'tmpl_context', 'actions', 'translator', 'session', 'N_', 'ungettext', 'config', 'response', '_']
        ignored_context_keys = [
            '__class__', '__context', '__delattr__', '__dict__', '__doc__', '__format__', '__getattr__', '__getattribute__', '__hash__', '__init__',
            '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__',
            '__weakref__', 'action', 'environ', 'pylons', 'start_response', 'userobj', 'page']

        debug_vars = debug_info['vars']

        for key in filter(lambda k: not k in ignored_keys, debug_vars.keys()):
            out[key] = debug_vars[key]

        if 'tmpl_context' in debug_vars:
            for key in filter(lambda k: not k in ignored_context_keys, debug_info['c_vars']):
                val = getattr(debug_vars['tmpl_context'], key)
                if hasattr(val, '__call__'):
                    val = repr(val)
                out['c.%s' % key] = val

        return out

    @classmethod
    def dump_jsonpickle(cls, obj):
        ''' Encode (i.e serialize) an object using jsonpickle '''
        return jsonpickle.encode(obj)

    ## ITemplateHelpers interface ##

    def get_helpers(self):
        ''' Return a dict of named helper functions (as defined in the ITemplateHelpers interface).
        These helpers will be available under the 'h' thread-local global object.
        '''
        return {
            # define externsion-specific helpers
            'hello_world': self.hello_world,
            'music_genres': self.music_genres,
            'music_genres_options': self.music_genres_options,
            'organization_list_objects': self.organization_list_objects,
            'organization_dict_objects': self.organization_dict_objects,
            # define debug helpers
            'debug_template_vars': self.debug_template_vars,
            'dump_jsonpickle': self.dump_jsonpickle,
        }

    ## IConfigurer interface ##

    def update_config(self, config):
        ''' Setup the (fanstatic) resource library, public and template directory '''
        p.toolkit.add_public_directory(config, 'public')
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_resource('public', 'ckanext-helloworld')

    ## IConfigurable interface ##

    def configure(self, config):
        ''' Apply configuration options to this plugin '''
        pass

    ## IDatasetForm interface ##

    def is_fallback(self):
        '''
        Return True to register this plugin as the default handler for
        package types not handled by any other IDatasetForm plugin.
        '''
        return True

    def package_types(self):
        '''
        This plugin doesn't handle any special package types, it just
        registers itself as the default (above).
        '''
        return []

    def _modify_package_schema(self, schema):
        ''' Override CKAN's create/update schema '''

        # Define some closures as custom callbacks for the validation process

        from ckan.lib.navl.dictization_functions import missing, StopOnError, Invalid

        def music_title_converter_1(key, data, errors, context):
            ''' Demo of a typical behaviour inside a validator/converter '''

            ## Stop processing on this key and signal the validator with another error (an instance of Invalid) 
            #raise Invalid('The music title (%s) is invalid' %(data.get(key,'<none>')))

            ## Stop further processing on this key, but not an error
            #raise StopOnError
            pass

        def music_title_converter_2(key, data, errors, context):
            #raise Exception ('Breakpoint music_title_converter_2')
            pass

        def after_validation_processor(key, data, errors, context):
            assert key[0] == '__after', 'This validator can only be invoked in the __after stage'
            #raise Exception ('Breakpoint after_validation_processor')
            # Demo of howto create/update an automatic extra field 
            extras_list = data.get(('extras',), [])
            modification_metadata_key = 'modified-at'
            modification_metadata_exists = False
            datestamp = time.strftime('%Y-%m-%d %T')
            for x in extras_list:
                if x.get('key') == modification_metadata_key:
                    x['value'] = datestamp
                    modification_metadata_exists = True
            if not modification_metadata_exists:
                extras_list.append ({ 'key': modification_metadata_key, 'value': datestamp })
            pass

        def before_validation_processor(key, data, errors, context):
            assert key[0] == '__before', 'This validator can only be invoked in the __before stage'
            #raise Exception ('Breakpoint before_validation_processor')
            pass

        # Update default validation schema (inherited from DefaultDatasetForm)

        schema.update({
            # Add our custom "music_genre" metadata field to the schema.
            'music_genre': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_tags')('music_genres'),
            ],
            # Add our "music_title" metadata field to the schema, this one will use
            # convert_to_extras instead of convert_to_tags.
            'music_title': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_extras'),
                music_title_converter_1,
                music_title_converter_2,
            ],
        })

        # Add callbacks to the '__after' pseudo-key to be invoked after all key-based validators/converters

        if not schema.get('__after'):
            schema['__after'] = []
        schema['__after'].append(after_validation_processor)

        # A similar hook is also provided by the '__before' pseudo-key with obvious functionality.

        if not schema.get('__before'):
            schema['__before'] = []
        # any additional validator must be inserted before the default 'ignore' one. 
        schema['__before'].insert(-1, before_validation_processor) # insert as second-to-last

        return schema

    def create_package_schema(self):
        schema = super(DatasetForm, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(DatasetForm, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(DatasetForm, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(toolkit.get_converter('free_tags_only'))

        schema.update({
            # Add our custom "music_genre" metadata field to the schema.
            'music_genre': [
                toolkit.get_converter('convert_from_tags')('music_genres'),
                toolkit.get_validator('ignore_missing')
            ],
            # Add our "music_title" field to the dataset schema.
            'music_title': [
                toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_missing')
            ],
        })

        return schema

    def setup_template_variables(self, context, data_dict):
        ''' Setup (add/modify/hide) variables to feed the template engine.
        This is done through through toolkit.c (template thread-local context object).
        '''
        super(DatasetForm, self).setup_template_variables(context, data_dict)
        c = toolkit.c
        c.helloworld_magic_number = 99
        if c.pkg_dict:
            c.pkg_dict['helloworld'] = { 'author': 'foofootos', 'plugin-name': self.__class__.__name__ }

    # Note for all *_template hooks: 
    # We choose not to modify the path for each template (so we simply call the super() method). 
    # If a specific template's behaviour needs to be overriden, this can be done by means of 
    # template inheritance (e.g. Jinja2 `extends' or CKAN `ckan_extends')

    def new_template(self):
        return super(DatasetForm, self).new_template()

    def read_template(self):
        return super(DatasetForm, self).read_template()

    def edit_template(self):
        return super(DatasetForm, self).edit_template()

    def comments_template(self):
        return super(DatasetForm, self).comments_template()

    def search_template(self):
        return super(DatasetForm, self).search_template()

    def history_template(self):
        return super(DatasetForm, self).history_template()

