.. image:: ../logos/dislib-logo-full.png
   :height: 90px
   :align: left

.. toctree::
   :maxdepth: 2
   :caption: Contents:
|
|
|
|
|
|
|

The Distributed Computing Library (dislib) provides distributed algorithms ready
to use as a library. So far, dislib is highly focused on machine learning
algorithms, and is greatly inspired by `scikit-learn <https://scikit-learn
.org>`_. However, other types of numerical algorithms might be added in the
future. The main objective of dislib is to facilitate the execution of big
data analytics algorithms in distributed platforms, such as clusters, clouds,
and supercomputers.

Dislib has been implemented on top of `PyCOMPSs <https://www.bsc
.es/research-and-development/software-and-apps/software-list/comp-superscalar
/>`_ programming model, and it is being developed by the `Workflows
and Distributed Computing <https://www.bsc
.es/discover-bsc/organisation/scientific-structure/workflows-and-distributed
-computing>`_ group of the `Barcelona Supercomputing Center <http://www.bsc
.es>`_.


Contents
--------

* :doc:`Quickstart <quickstart>`
* :doc:`API Reference <api-reference>`
* :doc:`Development <development>`
* :doc:`FAQ <faq>`

Performance
-----------

The following plot shows fit time of some dislib models on the
`MareNostrum 4 <https://www.bsc.es/marenostrum/marenostrum>`_ supercomputer
(using 8 worker nodes):

.. image:: ./performance.png
    :align: center
    :width: 500px

Labels on the horizontal axis represent algorithm-dataset, where:

- ALS = AlternatingLeastSquares
- CSVM = CascadeSVM
- GMM = GaussianMixture
- RF = RandomForestClassifier

and:

- Netflix = The Netflix Prize `dataset <https://www.kaggle
  .com/netflix-inc/netflix-prize-data>`_.
- ijcnn1 = The `ijcnn1 <https://www.csie.ntu.edu
  .tw/~cjlin/libsvmtools/datasets/binary.html#ijcnn1>`_ dataset.
- KDD99 = The `KDDCUP 1999 <http://kdd.ics.uci.edu/databases
  /kddcup99/kddcup99.html>`_ dataset.
- gaia = The Tycho-Gaia Astrometric Solution dataset [1]_.
- 1M and 3M = 1 and 3 million random samples.
- mnist = The `mnist <https://www.csie.ntu.edu
  .tw/~cjlin/libsvmtools/datasets/multiclass.html#mnist>`_ dataset.


Source code
-----------

The source code of dislib is available online at `Github <https://github
.com/bsc-wdc/dislib>`_.

Support
-------

If you have questions or issues about the dislib you can join us in `Slack
<https://bit.ly/bsc-wdc-community>`_.

Alternatively, you can send us an e-mail to `support-compss@bsc.es
<mailto:support-compss@bsc.es>`_.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. [1] Michalik, Daniel, Lindegren, Lennart, and Hobbs, David, “The
  Tycho-Gaia astrometric solution - How to get 2.5 million parallaxes with less
  than one year of Gaia data,” A&A, vol. 574, p. A115, 2015.