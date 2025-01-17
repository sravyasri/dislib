Developer's guide
=================

Drafting new releases
---------------------

Follow these steps when drafting a new release:

1. Ensure that the master branch is passing the tests and that the `latest
   version of the documentation <https://dislib.bsc.es/en/latest>`_ is
   properly being built.

2. Decide whether to issue a minor or a major release following this
   `guide <https://semver.org/>`_.

3. Create and switch to a new branch named ``release-X.Y``.

4. Update the release number accordingly in the `VERSION
   <https://github.com/bsc-wdc/dislib/blob/master/VERSION>`_ file.

5. Update the required PyCOMPSs version in the `quickstart guide
   <https://github.com/bsc-wdc/dislib/blob/master/QUICKSTART.md>`_ if
   necessary.

6. Update the `change log
   <https://github.com/bsc-wdc/dislib/blob/master/CHANGELOG.md>`_.

7. Update the `performance plot <https://github
   .com/bsc-wdc/dislib/blob/master/docs/source/performance.png>`_ in the
   documentation if necessary.

8. Push the release branch with the changes.

9. Merge the newly created branch to the master branch.

10. Draft a new release in `Github <https://github.com/bsc-wdc/
    dislib/releases>`_ using this `template <https://github
    .com/bsc-wdc/dislib/blob/master/.github/RELEASE_TEMPLATE.md>`_ using tag
    name ``vX.Y.Z``.

11. Create and tag a docker image for the release running the following at the
    repo's root (change ``VERSION`` accordingly):

    - Create the image:
     
    .. code:: bash
     
       docker build -t bscwdc/dislib:VERSION .
       # Create also new 'latest' tag using newly created image
       docker tag bscwdc/dislib:VERSION bscwdc/dislib:latest
   
    - Log in and push it to dockerhub
   
    .. code:: bash

       docker login -u DOCKERHUB_USER -p DOCKERHUB_PASSWORD
       docker push bscwdc/dislib:VERSION
       docker push bscwdc/dislib:latest

12. Create a pip package and upload it to PyPi:

    .. code:: bash

     python3 setup.py sdist bdist_wheel
     python3 -m twine upload dist/*
