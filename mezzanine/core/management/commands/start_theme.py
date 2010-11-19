
import os
from shutil import copy

from django.core.management.base import CommandError
from django.core.management.commands.startapp import Command as StartAppCommand
from django.utils.importlib import import_module

from mezzanine.conf import settings


def template_path(template):
    """
    Django 1.2 and higher moved to class-based template loaders and 
    deprecated ``find_template_source`` - there's a ``find_template`` 
    function that is similar but always returns ``None`` for the 
    template path so it appears to be broken. This function works as far 
    as retrieving the template path goes which is all we're concerned 
    with.
    """
    from django import VERSION
    if VERSION < (1, 2, 0):
        from django.template.loader import find_template_source
        return find_template_source(template)[1]
    from django.template.loader import find_template_loader, \
                                       TemplateDoesNotExist
    for loader_name in settings.TEMPLATE_LOADERS:
        loader = find_template_loader(loader_name)
        if loader is not None:
            try:
                return loader.load_template_source(template, None)[1]
            except TemplateDoesNotExist:
                pass
    return None


class Command(StartAppCommand):
    """
    Creates a theme directory which is a Django app plus all existing 
    templates in the current project.
    """

    help = ("Creates a theme directory which is a Django app plus all "
            "existing templates in the current project.")
    args = "[theme_name]"
    label = "theme name"
    can_import_settings = True

    def handle_label(self, theme_name, **options):
        """
        Create a new Django app and copy all available templates into it.
        """
        super(Command, self).handle_label(theme_name, **options)
        # Build a unique list of template names from ``INSTALLED_APPS`` and 
        # ``TEMPLATE_DIRS`` then use Django's ``find_template_source`` to 
        # determine which to copy.
        templates = set()
        for app in settings.INSTALLED_APPS:
            if app.startswith("django.") or app in settings.OPTIONAL_APPS:
                continue
            app_module = import_module(app)
            app_path = os.path.dirname(os.path.abspath(app_module.__file__))
            templates_path = os.path.join(app_path, "templates")
            for (root, dirs, files) in os.walk(templates_path):
                for f in files:
                    template = os.path.join(root, f)[len(templates_path):]
                    if not template.startswith("/admin/"):
                        templates.add(template.lstrip("/"))
        os.mkdir(os.path.join(theme_name, "templates"))
        for template in templates:
            path_from = unicode(template_path(template))
            path_to = os.path.join(theme_name, "templates", template)
            try:
                os.makedirs(os.path.dirname(path_to))
            except OSError:
                pass
            copy(path_from, path_to)
