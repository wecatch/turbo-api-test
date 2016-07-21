from setuptools import setup, find_packages


version = __import__('turbo_api_test').version


install_requires = [

]

for k in ['PyYAML', 'requests', 'turbo']:
    try:
        __import__(k)
    except ImportError:
        install_requires.append(k)

setup(
    name="turbo_api_test",
    version=version,
    author="Wecatch.me",
    author_email="wecatch.me@gmail.com",
    url="http://github.com/wecatch/turbo-api-test",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    description="Turbo_api_test is a framework/tool for api test",
    packages=find_packages(),
    install_requires=install_requires,
)
