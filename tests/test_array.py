# import os
import unittest
from math import ceil

import numpy as np
from scipy import sparse as sp
from scipy.sparse import issparse
from sklearn.datasets import load_svmlight_file

import dislib as ds
from dislib.data.array import Array


def equal(arr1, arr2):
    if issparse(arr1) and not issparse(arr2):
        raise AttributeError('Arrays are of different type: %s != %s' % (
            type(arr1), type(arr2)))

    if issparse(arr1):
        equal = (arr1 != arr2).nnz == 0
    else:
        equal = not (arr1 != arr2).any()

    if not equal:
        print("\nArr1: \n%s" % arr1)
        print("Arr2: \n%s" % arr2)

    return equal


def equivalent_types(arr1, arr2):
    equivalent = type(arr1) == type(arr2) or (
        type(arr1) == np.ndarray and type(arr2) == np.matrix) or (
                     type(arr1) == np.matrix and type(arr2) == np.ndarray)

    if not equivalent:
        print("Type(arr1): %s" % type(arr1))
        print("Type(arr2): %s" % type(arr2))

    return equivalent


def _validate_arrays(self, darray, x, block_shape):
    # Different size and type comparison if arrays have 1 or 2 dimensions
    if len(x.shape) == 1:
        n, m = len(x), 1
        self.assertEqual(type(darray.collect()[0]), type(x[0]))
        self.assertEqual(darray.shape[0], x.shape[0])
    else:
        n, m = x.shape
        self.assertEqual(type(darray.collect()[0, 0]), type(x[0, 0]))
        self.assertEqual(darray.shape, x.shape)

    bn, bm = block_shape

    self.assertTrue(equal(darray.collect(), x))
    self.assertTrue(equivalent_types(darray.collect(), x))
    self.assertEqual(type(darray), Array)

    self.assertEqual(darray._number_of_blocks, (ceil(n / bn), ceil(m / bm)))


class DataLoadingTest(unittest.TestCase):
    def test_array_constructor(self):
        """ Tests load_data
        """
        n, m = 6, 10
        bn, bm = 4, 3
        x = np.random.randint(0, 10, size=(n, m))
        darray = ds.array(x=x, blocks_shape=(bn, bm))

        _validate_arrays(self, darray, x, (bn, bm))

        x = sp.csr_matrix(x)
        darray = ds.array(x=x, blocks_shape=(bn, bm))

        _validate_arrays(self, darray, x, (bn, bm))

    def test_load_libsvm_file(self):
        """ Tests loading a LibSVM file in dense mode.
        """
        file_ = "tests/files/libsvm/1"

        x, y = load_svmlight_file(file_, n_features=780)

        bn, bm = 25, 100

        # Load SVM and store in sparse
        arr_x, arr_y = ds.load_svmlight_file(file_, (25, 100), n_features=780,
                                             store_sparse=True)

        _validate_arrays(self, arr_x, x, (bn, bm))
        _validate_arrays(self, arr_y, y, (bn, 1))

        # Load SVM and store in dense
        arr_x, arr_y = ds.load_svmlight_file(file_, (25, 100), n_features=780,
                                             store_sparse=False)

        _validate_arrays(self, arr_x, x.toarray(), (bn, bm))
        _validate_arrays(self, arr_y, y, (bn, 1))


#
#     def test_load_libsvm_files_sparse(self):
#         """ Tests loading multiple LibSVM files in sparse mode.
#         """
#         dir_ = "tests/files/libsvm"
#
#         file_list = os.listdir(dir_)
#         data = load_libsvm_files(dir_, 780)
#         data.collect()
#
#         for i, subset in enumerate(data):
#             samples = subset.samples.toarray()
#             file_ = os.path.join(dir_, file_list[i])
#             x, y = load_svmlight_file(file_, n_features=780)
#
#             self.assertTrue((samples == x).all())
#             self.assertTrue((subset.labels == y).all())
#
#         self.assertEqual(len(data), 3)
#
#     def test_load_libsvm_files_dense(self):
#         """ Tests loading multiple LibSVM files in dense mode.
#         """
#         dir_ = "tests/files/libsvm"
#
#         file_list = os.listdir(dir_)
#         data = load_libsvm_files(dir_, 780, False)
#         data.collect()
#
#         for i, subset in enumerate(data):
#             samples = subset.samples
#             file_ = os.path.join(dir_, file_list[i])
#             x, y = load_svmlight_file(file_, n_features=780)
#
#             self.assertTrue((samples == x).all())
#             self.assertTrue((subset.labels == y).all())
#
#         self.assertEqual(len(data), 3)
#
#     def test_load_csv_file(self):
#         """ Tests loading a CSV file.
#         """
#         csv_file = "tests/files/csv/1"
#
#         data = load_txt_file(csv_file, subset_size=300, n_features=122)
#         data.collect()
#         csv = np.loadtxt(csv_file, delimiter=",")
#
#         read_x = np.empty((0, csv.shape[1]))
#
#         for subset in data:
#             read_x = np.concatenate((read_x, subset.samples))
#
#         self.assertTrue((read_x == csv).all())
#         self.assertEqual(len(data), 15)
#         self.assertIsNone(subset.labels)
#
#     def test_load_csv_file_labels_last(self):
#         """ Tests loading a CSV file with labels at the last column.
#         """
#         csv_file = "tests/files/csv/1"
#
#         data = load_txt_file(csv_file, subset_size=1000, n_features=121,
#                              label_col="last")
#         data.collect()
#         csv = np.loadtxt(csv_file, delimiter=",")
#
#         read_x = np.empty((0, csv.shape[1] - 1))
#         read_y = np.empty(0)
#
#         for subset in data:
#             read_x = np.concatenate((read_x, subset.samples))
#             read_y = np.concatenate((read_y, subset.labels))
#
#         self.assertTrue((read_x == csv[:, :-1]).all())
#         self.assertTrue((read_y == csv[:, -1]).all())
#         self.assertEqual(len(data), 5)
#
#     def test_load_csv_file_labels_first(self):
#         """ Tests loading a CSV file with labels at the first column.
#         """
#         csv_file = "tests/files/csv/2"
#
#         data = load_txt_file(csv_file, subset_size=100, n_features=121,
#                              label_col="first")
#         data.collect()
#         csv = np.loadtxt(csv_file, delimiter=",")
#
#         read_x = np.empty((0, csv.shape[1] - 1))
#         read_y = np.empty(0)
#
#         for subset in data:
#             read_x = np.concatenate((read_x, subset.samples))
#             read_y = np.concatenate((read_y, subset.labels))
#
#         self.assertTrue((read_x == csv[:, 1:]).all())
#         self.assertTrue((read_y == csv[:, 0]).all())
#         self.assertEqual(len(data), 44)
#
#     def test_load_csv_files(self):
#         """ Tests loading multiple CSV files.
#         """
#         csv_dir = "tests/files/csv"
#
#         file_list = os.listdir(csv_dir)
#         data = load_txt_files(csv_dir, n_features=122)
#         data.collect()
#
#         for i, subset in enumerate(data):
#             csv_file = os.path.join(csv_dir, file_list[i])
#             csv = np.loadtxt(csv_file, delimiter=",")
#
#             self.assertTrue((subset.samples == csv).all())
#
#         self.assertEqual(len(data), 3)
#
#     def test_load_csv_files_labels_last(self):
#         """ Tests loading multiple CSV files with labels at the last column.
#         """
#         csv_dir = "tests/files/csv"
#
#         file_list = os.listdir(csv_dir)
#         data = load_txt_files(csv_dir, n_features=122, label_col="last")
#         data.collect()
#
#         for i, subset in enumerate(data):
#             csv_file = os.path.join(csv_dir, file_list[i])
#             csv = np.loadtxt(csv_file, delimiter=",")
#
#             self.assertTrue((subset.samples == csv[:, :-1]).all())
#             self.assertTrue((subset.labels == csv[:, -1]).all())
#
#         self.assertEqual(len(data), 3)
#
#     def test_load_csv_files_labels_first(self):
#         """ Tests loading multiple CSV files with labels at the first column.
#         """
#         csv_dir = "tests/files/csv"
#
#         file_list = os.listdir(csv_dir)
#         data = load_txt_files(csv_dir, n_features=122, label_col="first")
#         data.collect()
#
#         for i, subset in enumerate(data):
#             csv_file = os.path.join(csv_dir, file_list[i])
#             csv = np.loadtxt(csv_file, delimiter=",")
#
#             self.assertTrue((subset.samples == csv[:, 1:]).all())
#             self.assertTrue((subset.labels == csv[:, 0]).all())
#
#         self.assertEqual(len(data), 3)
#
#     def test_load_txt_delimiter(self):
#         """ Tests load_txt_file with a custom delimiter """
#         path_ = "tests/files/other/4"
#         data = load_txt_file(path_, n_features=122, subset_size=1000,
#                              delimiter=" ")
#         csv = np.loadtxt(path_, delimiter=" ")
#
#         self.assertTrue(np.array_equal(data.samples, csv))
#         self.assertEqual(len(data), 5)
#         self.assertIsNone(data.labels)
#
#     def test_load_txt_files_delimiter(self):
#         """ Tests loading multiple files with a custom delimiter"""
#         path_ = "tests/files/other"
#
#         file_list = os.listdir(path_)
#         data = load_txt_files(path_, n_features=122, delimiter=" ")
#         data.collect()
#
#         for i, subset in enumerate(data):
#             file_ = os.path.join(path_, file_list[i])
#             read_data = np.loadtxt(file_, delimiter=" ")
#
#             self.assertTrue(np.array_equal(subset.samples, read_data))
#
#         self.assertEqual(len(data), 2)
#
#


class ArrayTest(unittest.TestCase):
    def test_sizes(self):
        """ Tests sizes consistency. """

        x_size, y_size = 40, 25
        bn, bm = 9, 11
        x = np.random.randint(10, size=(x_size, y_size))
        darray = ds.array(x=x, blocks_shape=(bn, bm))

        self.assertEqual(darray.shape, (x_size, y_size))

        self.assertEqual(darray._number_of_blocks,
                         (ceil(x_size / bn), ceil(y_size / bm)))
        self.assertEqual(darray._blocks_shape, (bn, bm))

        x = sp.csr_matrix(x)
        darray = ds.array(x=x, blocks_shape=(bn, bm))

        self.assertEqual(darray.shape, (x_size, y_size))
        self.assertEqual(darray._number_of_blocks,
                         (ceil(x_size / bn), ceil(y_size / bm)))
        self.assertEqual(darray._blocks_shape, (bn, bm))

    def test_iterate_rows(self):
        """ Testing the row _iterator of the ds.array
        """
        x_size = 2
        # Dense
        x = np.random.randint(10, size=(10, 10))
        data = ds.array(x=x, blocks_shape=(x_size, 2))
        for i, r in enumerate(data._iterator(axis='rows')):
            r_data = r.collect()
            r_x = x[i * x_size:(i + 1) * x_size]
            self.assertTrue(equal(r_data, r_x))

        # Sparse
        x = sp.csr_matrix(x)
        data = ds.array(x=x, blocks_shape=(x_size, 2))
        for i, r in enumerate(data._iterator(axis='rows')):
            r_data = r.collect()
            r_x = x[i * x_size:(i + 1) * x_size]
            self.assertTrue(equal(r_data, r_x))

    def test_iterate_cols(self):
        """ Tests iterating through the rows of the ds.array
        """
        bn, bm = 2, 2
        # Dense
        x = np.random.randint(10, size=(10, 10))
        data = ds.array(x=x, blocks_shape=(bn, bm))

        for i, c in enumerate(data._iterator(axis='columns')):
            c_data = c.collect()
            c_x = x[:, i * bm:(i + 1) * bm]
            self.assertTrue(equal(c_data, c_x))

        # Sparse
        x = sp.csr_matrix(x)
        data = ds.array(x=x, blocks_shape=(bn, bm))

        for i, c in enumerate(data._iterator(axis='columns')):
            c_data = c.collect()
            c_x = x[:, i * bm:(i + 1) * bm]
            self.assertTrue(equal(c_data, c_x))

    def test_get_item(self):
        """ Tests get item of the ds.array
        """
        bn, bm = 2, 2
        x = np.random.randint(10, size=(10, 10))
        data = ds.array(x=x, blocks_shape=(bn, bm))

        for i in range(x.shape[0]):
            for j in range(x.shape[1]):
                element = data[i, j].collect()
                self.assertEqual(element, x[i, j])

    def test_get_slice_simple(self):
        """ Tests get a simple slice of the ds.array
        """
        bn, bm = 5, 5
        x = np.random.randint(100, size=(30, 30))
        print(x)
        data = ds.array(x=x, blocks_shape=(bn, bm))

        slice_indices = [(7, 22, 7, 22),  # many row-column
                         (6, 8, 6, 8),  # single block row-column
                         (6, 8, None, None),  # single-block rows, all columns
                         (None, None, 6, 8),  # all rows, single-block columns
                         (15, 16, 15, 16),  # single element
                         # (-10, -5, -10, -5),  # out-of-bounds (not implemented)
                         # (-10, 5, -10, 5),  # out-of-bounds (not implemented)
                         (21, 40, 21, 40)]  # out-of-bounds (correct)

        # bn, bm = 3, 3
        # x = np.random.randint(100, size=(10, 10))
        # print(x)
        # data = ds.array(x=x, blocks_shape=(bn, bm))
        #
        # slice_indices = [(4, 5, 4, 5),  # single element
        #                  (2, 7, 2, 7),  # many row-column
        #                  (3, 5, 3, 5),  # single block row-column
        #                  (3, 5, None, None),  # single-block rows, all columns
        #                  (None, None, 3, 5),  # all rows, single-block columns
        #                  (5, 20, 5, 20)] # out-of-bounds (correct)

        for top, bot, left, right in slice_indices:
            print("Indices: %s" % [top, bot, left, right])
            got = data[top:bot, left:right].collect()
            expected = x[top:bot, left:right]

            print("Expected: %s\nGot: %s" % (expected, got))

            try:
                self.assertTrue(equal(got, expected))
            except:
                import ipdb
                ipdb.set_trace()
# def test_mean(self):
    #     bn, bm = 2, 2
    #
    #     # Dense
    #     # =====
    #
    #     x = np.random.randint(10, size=(10, 10))
    #     # to test mean in empty blocks
    #     x[0:bn+1, 0:bm+1] = 0
    #     data = ds.array(x=x, blocks_shape=(bn, bm))
    #
    #     _validate_arrays(self, data.mean(axis=0),
    #                      x.mean(axis=0).reshape(1, -1),
    #                      (bn, bm))
    #
    #     _validate_arrays(self, data.mean(axis=1),
    #                      x.mean(axis=1).reshape(-1, 1), (bn, bm))
    #
    #     # Sparse
    #     # ======
    #     x = sp.csr_matrix(x)
    #     data = ds.array(x=x, blocks_shape=(bn, bm))
    #
    #     # Compute the mean counting empty positions as 0
    #     _validate_arrays(self, data.mean(axis=0, count_zero=True),
    #                      x.mean(axis=0), (bn, bm))
    #
    #     _validate_arrays(self, data.mean(axis=1, count_zero=True),
    #                      x.mean(axis=1), (bn, bm))
    #
    #     # Compute the mean without considering empty positions
    #     x_mean = x.sum(axis=0) / (x != 0).toarray().sum(axis=0)
    #     _validate_arrays(self, data.mean(axis=0, count_zero=False),
    #                      x_mean, (bn, bm))
    #
    #     x_mean = x.sum(axis=1) / (x != 0).toarray().sum(axis=1).reshape(-1, 1)
    #     _validate_arrays(self, data.mean(axis=1, count_zero=False),
    #                      x_mean, (bn, bm))

    def test_transpose(self):
        """ Tests array transpose."""

        x_size, y_size = 4, 6
        bn, bm = 2, 3

        x = np.random.randint(10, size=(x_size, y_size))
        darray = ds.array(x=x, blocks_shape=(bn, bm))

        darray_t = darray.transpose(mode='all')
        _validate_arrays(self, darray_t, x.transpose(), (bm, bn))
        # ensure that original data was not modified
        _validate_arrays(self, darray, x, (bn, bm))

        darray_t = darray.transpose(mode='rows')
        _validate_arrays(self, darray_t, x.transpose(), (bm, bn))
        # ensure that original data was not modified
        _validate_arrays(self, darray, x, (bn, bm))

        darray_t = darray.transpose(mode='columns')
        _validate_arrays(self, darray_t, x.transpose(), (bm, bn))
        # ensure that original data was not modified
        _validate_arrays(self, darray, x, (bn, bm))

        self.assertRaises(Exception, darray.transpose, 'invalid')


# def test_min_max_features(self):
#         """ Tests that min_features and max_features correctly return min
#         and max values in a toy dataset.
#         """
#         s1 = Subset(samples=np.array([[1, 2], [4, 5], [2, 2], [6, 6]]),
#                     labels=np.array([0, 1, 1, 1]))
#         s2 = Subset(samples=np.array([[7, 8], [9, 8], [0, 4]]),
#                     labels=np.array([0, 1, 1]))
#         s3 = Subset(samples=np.array([[3, 9], [0, 7], [6, 1], [0, 8]]),
#                     labels=np.array([0, 1, 1, 1]))
#         dataset = Dataset(n_features=2)
#         dataset.append(s1)
#         dataset.append(s2)
#         dataset.append(s3)
#
#         min_ = dataset.min_features()
#         max_ = dataset.max_features()
#
#         self.assertTrue(np.array_equal(min_, np.array([0, 1])))
#         self.assertTrue(np.array_equal(max_, np.array([9, 9])))
#
#     def test_min_max_features_sparse(self):
#         """ Tests that min_features and max_features correctly return min
#         and max values with sparse dataset. """
#
#         file_ = "tests/files/libsvm/1"
#         sparse = load_libsvm_file(file_, 10, 780)
#         dense = load_libsvm_file(file_, 10, 780, store_sparse=False)
#
#         max_sp = sparse.max_features()
#         max_d = dense.max_features()
#         min_sp = sparse.min_features()
#         min_d = sparse.min_features()
#
#         self.assertTrue(np.array_equal(max_sp, max_d))
#         self.assertTrue(np.array_equal(min_sp, min_d))
#


def main():
    unittest.main()


if __name__ == '__main__':
    main()