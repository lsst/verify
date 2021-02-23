"""Sphinx configurations to build package documentation."""

from documenteer.conf.pipelinespkg import *


project = "verify"
html_theme_options["logotext"] = project
html_title = project
html_short_title = project
doxylink = {}
