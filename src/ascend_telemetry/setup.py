from setuptools import find_packages, setup

package_name = 'ascend_telemetry'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='administrator',
    maintainer_email='administrator@todo.todo',
    description='ASCEND Telemetry Node',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'telemetry_node = ascend_telemetry.telemetry_node:main',
        ],
    },
)
