import os
from glob import glob


from setuptools import find_packages, setup

package_name = 'g18_prii3_turtlesim'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),

    data_files=[
    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],

    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nikos',
    maintainer_email='nikos@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'draw_18_node = g18_prii3_turtlesim.draw_18_node:main',
        ],
    },
)
