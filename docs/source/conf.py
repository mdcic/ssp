# -*- coding: utf-8 -*-

import sys, os

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.todo']
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'ssp'
copyright = u'2013, Yury Konovalov'
version = '0.0.1'
release = '0.0.1'
exclude_patterns = []
pygments_style = 'sphinx'
html_theme = 'default'
html_static_path = ['_static']
htmlhelp_basename = 'sspdoc'
latex_elements = {
}
latex_documents = [
  ('index', 'ssp.tex', u'ssp Documentation',
   u'Yury Konovalov', 'manual'),
]
man_pages = [
    ('index', 'ssp', u'ssp Documentation',
     [u'Yury Konovalov'], 1)
]
texinfo_documents = [
  ('index', 'ssp', u'ssp Documentation',
   u'Yury Konovalov', 'ssp', 'One line description of project.',
   'Miscellaneous'),
]
