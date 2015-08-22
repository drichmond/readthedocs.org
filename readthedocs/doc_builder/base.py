from functools import wraps
import os
import logging
import shutil

log = logging.getLogger(__name__)


def restoring_chdir(fn):
    # XXX:dc: This would be better off in a neutral module
    @wraps(fn)
    def decorator(*args, **kw):
        try:
            path = os.getcwd()
            return fn(*args, **kw)
        finally:
            os.chdir(path)
    return decorator


class BaseBuilder(object):
    """
    The Base for all Builders. Defines the API for subclasses.

    Expects subclasses to define ``old_artifact_path``,
    which points at the directory where artifacts should be copied from.
    """

    _force = False
    # old_artifact_path = ..

    def __init__(self, build_env, force=False):
        self.build_env = build_env
        self.version = build_env.version
        self.project = build_env.project
        self._force = force
        self.target = self.project.artifact_path(
            version=self.version.slug,
            type=self.type
        )

    def force(self, **kwargs):
        """
        An optional step to force a build even when nothing has changed.
        """
        log.info("Forcing a build")
        self._force = True

    def build(self, id=None, **kwargs):
        """
        Do the actual building of the documentation.
        """
        raise NotImplementedError

    def move(self, **kwargs):
        """
        Move the documentation from it's generated place to its artifact directory.
        """
        if os.path.exists(self.old_artifact_path):
            if os.path.exists(self.target):
                shutil.rmtree(self.target)
            log.info("Copying %s on the local filesystem" % self.type)
            shutil.copytree(self.old_artifact_path, self.target)
        else:
            log.warning("Not moving docs, because the build dir is unknown.")

    def clean(self, **kwargs):
        """
        Clean the path where documentation will be built
        """
        if os.path.exists(self.old_artifact_path):
            shutil.rmtree(self.old_artifact_path)
            log.info("Removing old artifact path: %s" % self.old_artifact_path)

    def docs_dir(self, docs_dir=None, **kwargs):
        """
        Handle creating a custom docs_dir if it doesn't exist.
        """
        checkout_path = self.project.checkout_path(self.version.slug)
        if not docs_dir:
            for doc_dir_name in ['docs', 'doc', 'Doc', 'book']:
                possible_path = os.path.join(checkout_path, doc_dir_name)
                if os.path.exists(possible_path):
                    docs_dir = possible_path
                    break
        if not docs_dir:
            docs_dir = checkout_path
        return docs_dir

    def create_index(self, extension='md', **kwargs):
        """
        Create an index file if it needs it.
        """

        docs_dir = self.docs_dir()
        valid_filenames = ('index', 'README')
        index_filenames = [
            os.path.join(docs_dir, '{filename}.{ext}'.format(
                filename=filename, ext=extension))
            for filename in valid_filenames]
        if not any(os.path.exists(filename) for filename in index_filenames):
            primary_index = index_filenames[0]
            index_text = """

Welcome to Read the Docs
------------------------

This is an autogenerated index file.

Please create a ``{dir}/index.{ext}`` or ``{dir}/README.{ext}`` file with your own content.

If you want to use another markup, choose a different builder in your settings.
            """
            with open(primary_index, 'w+') as index_file:
                index_file.write(index_text.format(
                    dir=docs_dir,
                    ext=extension))

    def run(self, *args, **kwargs):
        '''Proxy run to build environment'''
        return self.build_env.run(*args, **kwargs)
