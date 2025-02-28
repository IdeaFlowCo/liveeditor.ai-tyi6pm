#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs
import re
from setuptools import setup, find_packages  # setuptools ~=68.0.0

# Path to the current directory
HERE = os.path.abspath(os.path.dirname(__file__))

def read(file_path):
    """
    Helper function to read contents of a file with proper encoding.
    
    Args:
        file_path (str): Path to the file to be read
        
    Returns:
        str: Contents of the file
    """
    with codecs.open(os.path.join(HERE, file_path), 'r', 'utf-8') as f:
        return f.read()

def find_version(file_path, pattern):
    """
    Extract version information from the specified Python file using regex pattern matching.
    
    Args:
        file_path (str): Path to the file containing version information
        pattern (str): Regex pattern to match version string
        
    Returns:
        str: Version string extracted from the file
        
    Raises:
        RuntimeError: If version pattern not found in the file
    """
    content = read(file_path)
    version_match = re.search(pattern, content, re.M)
    
    if version_match:
        return version_match.group(1)
    
    raise RuntimeError("Unable to find version string in {0}".format(file_path))

def get_requirements():
    """
    Parse requirements.txt to extract package dependencies.
    
    Returns:
        list: List of package requirement strings
    """
    requirements = []
    try:
        requirements_file = read('requirements.txt')
        for line in requirements_file.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
    except FileNotFoundError:
        # If requirements.txt is not found, return minimal dependencies
        return [
            'flask==2.3.0',
            'langchain==0.0.267',
            'flask-restful==0.3.10',
            'gunicorn==21.2.0',
            'pyjwt==2.7.0',
        ]
    
    return requirements

# Package metadata and setup configuration
setup_kwargs = {
    'name': 'ai-writing-enhancement-backend',
    'version': '0.1.0',  # Could also use find_version() if version is stored in a Python file
    'description': 'AI-powered writing enhancement backend service providing intelligent suggestions and document management',
    'long_description': read('README.md'),
    'long_description_content_type': 'text/markdown',
    'author': 'AI Writing Enhancement Team',
    'author_email': 'team@example.com',
    'url': 'https://github.com/organization/ai-writing-enhancement',
    'packages': find_packages(where='src/backend'),
    'package_dir': {'': 'src/backend'},
    'include_package_data': True,
    'install_requires': get_requirements(),
    'extras_require': {
        'dev': [
            'pytest>=7.4.0',
            'pytest-flask>=1.2.0',
            'pytest-mock>=3.11.1',
            'pytest-cov>=4.1.0',
            'black>=23.7.0',
            'flake8>=6.1.0',
            'isort>=5.12.0',
            'mypy>=1.4.1',
        ],
    },
    'entry_points': {
        'console_scripts': [
            'ai-backend=app:application',
        ],
    },
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
    ],
    'python_requires': '>=3.10',
}

# Execute setup
if __name__ == '__main__':
    setup(**setup_kwargs)