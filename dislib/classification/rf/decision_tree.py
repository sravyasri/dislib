from sys import float_info

import numpy as np
from pycompss.api.api import compss_delete_object
from pycompss.api.parameter import FILE_IN
from pycompss.api.task import task
from sklearn.tree import DecisionTreeClassifier as SklearnDTClassifier

from dislib.classification.rf.test_split import test_split


class DecisionTreeClassifier:
    """A distributed decision tree classifier."""

    def __init__(self, try_features, max_depth, distr_depth, bootstrap):
        """
        Constructor for DecisionTreeClassifier

        Parameters
        ----------
        try_features : int
            The number of features to consider when looking for the best split.

            Note: the search for a split does not stop until at least one
            valid partition of the node samples is found, even if it requires
            to effectively inspect more than ``try_features`` features.

        max_depth : int
            The maximum depth of the tree. If np.inf, then nodes are expanded
            until all leaves are pure.

        distr_depth : int
            Number of levels of the tree in which the nodes are split in a
            distributed way.

        bootstrap : bool
            Randomly select n_instances samples with repetition (used in random
            forests).

        """
        self.try_features = try_features
        self.max_depth = max_depth
        self.distr_depth = distr_depth
        self.bootstrap = bootstrap

        self.n_features = None
        self.n_classes = None

        self.tree = None
        self.nodes_info = None
        self.subtrees = None

    def fit(self, dataset):
        """
        Fits the DecisionTreeClassifier.

        Parameters
        ----------
        dataset : dislib.classification.rf.data.RfDataset

        """

        self.n_features = dataset.get_n_features()
        self.n_classes = dataset.get_n_classes()
        samples_path = dataset.samples_path
        features_path = dataset.features_path
        n_samples = dataset.get_n_samples()
        y_codes = dataset.get_y_codes()

        sample, y_s = _sample_selection(n_samples, y_codes, self.bootstrap)
        self.tree = _Node()
        self.nodes_info = []
        self.subtrees = []
        tree_traversal = [(self.tree, sample, y_s, 0)]
        while tree_traversal:
            node, sample, y_s, depth = tree_traversal.pop()
            if depth < self.distr_depth:
                split = _split_node_wrapper(sample, self.n_features, y_s,
                                            self.n_classes, self.try_features,
                                            samples_file=samples_path,
                                            features_file=features_path)
                node_info, left_group, y_l, right_group, y_r = split
                compss_delete_object(sample)
                compss_delete_object(y_s)
                node.content = len(self.nodes_info)
                self.nodes_info.append(node_info)
                node.left = _Node()
                node.right = _Node()
                depth = depth + 1
                tree_traversal.append((node.right, right_group, y_r, depth))
                tree_traversal.append((node.left, left_group, y_l, depth))
            else:
                subtree = _build_subtree_wrapper(sample, y_s, self.n_features,
                                                 self.max_depth - depth,
                                                 self.n_classes,
                                                 self.try_features,
                                                 samples_path, features_path)
                node.content = len(self.subtrees)
                self.subtrees.append(subtree)
                compss_delete_object(sample)
                compss_delete_object(y_s)
        self.nodes_info = _merge(*self.nodes_info)

    def predict(self, subset):
        """
        Predicts classes for the subset samples using a fitted tree.

        Parameters
        ----------
        subset : dislib.data.Subset

        Returns
        -------
        predicted : ndarray
            An array with the predicted classes for the subset. The values are
            codes of the fitted dislib.classification.rf.data.RfDataset. The
            returned object can be a pycompss.runtime.Future object.

        """

        assert self.tree is not None, 'The decision tree is not fitted.'

        branch_predictions = []
        for i, subtree in enumerate(self.subtrees):
            pred = _predict_branch(subset, self.tree, self.nodes_info, i,
                                   subtree, self.distr_depth)
            branch_predictions.append(pred)
        return _merge_branches(None, *branch_predictions)

    def predict_proba(self, subset):
        """
        Predicts class probabilities for the subset using a fitted tree.

        Parameters
        ----------
        subset : dislib.data.Subset

        Returns
        -------
        predicted_proba : ndarray
            An array with the predicted probabilities for the subset samples.
            The shape is (len(subset.samples), self.n_classes), with the index
            of the column being codes of the fitted
            dislib.classification.rf.data.RfDataset. The returned object can be
            a pycompss.runtime.Future object.

        """

        assert self.tree is not None, 'The decision tree is not fitted.'

        branch_predictions = []
        for i, subtree in enumerate(self.subtrees):
            pred = _predict_branch_proba(subset, self.tree, self.nodes_info, i,
                                         subtree, self.distr_depth,
                                         self.n_classes)
            branch_predictions.append(pred)
        return _merge_branches(self.n_classes, *branch_predictions)


class _Node:

    def __init__(self):
        self.content = None
        self.left = None
        self.right = None

    def predict(self, sample):
        node_content = self.content
        if isinstance(node_content, _LeafInfo):
            return np.full((len(sample),), node_content.mode)
        if isinstance(node_content, _SkTreeWrapper):
            return node_content.sk_tree.predict(sample)
        if isinstance(node_content, _InnerNodeInfo):
            pred = np.empty((len(sample),), dtype=np.int64)
            left_mask = sample[:, node_content.index] <= node_content.value
            pred[left_mask] = self.left.predict(sample[left_mask])
            pred[~left_mask] = self.right.predict(sample[~left_mask])
            return pred
        assert False, 'Type not supported'

    def predict_proba(self, sample, n_classes):
        node_content = self.content
        if isinstance(node_content, _LeafInfo):
            single_pred = node_content.frequencies/node_content.size
            return np.repeat(single_pred, len(sample), 1)
        if isinstance(node_content, _SkTreeWrapper):
            sk_tree_pred = node_content.sk_tree.predict_proba(sample)
            pred = np.zeros((len(sample), n_classes), dtype=np.int64)
            pred[:, node_content.sk_tree.classes_] = sk_tree_pred
            return pred
        if isinstance(node_content, _InnerNodeInfo):
            pred = np.empty((len(sample), n_classes), dtype=np.int64)
            left_mask = sample[:, node_content.index] <= node_content.value
            pred[left_mask] = self.left.predict_proba(sample[left_mask])
            pred[~left_mask] = self.right.predict_proba(sample[~left_mask])
            return pred
        assert False, 'Type not supported'  # Execution shouldn't reach here


class _InnerNodeInfo:
    def __init__(self, index=None, value=None):
        self.index = index
        self.value = value


class _LeafInfo:
    def __init__(self, size=None, frequencies=None, mode=None):
        self.size = size
        self.frequencies = frequencies
        self.mode = mode


class _SkTreeWrapper:
    def __init__(self, tree):
        self.sk_tree = tree
        self.classes = tree.classes_


def _get_sample_attributes(samples_file, indices):
    samples_mmap = np.load(samples_file, mmap_mode='r', allow_pickle=False)
    x = samples_mmap[indices]
    return x


def _get_feature_mmap(features_file, i):
    return _get_features_mmap(features_file)[i]


def _get_features_mmap(features_file):
    return np.load(features_file, mmap_mode='r', allow_pickle=False)


@task(priority=True, returns=2)
def _sample_selection(n_samples, y_codes, bootstrap):
    if bootstrap:
        np.random.seed()
        selection = np.random.choice(n_samples, size=n_samples, replace=True)
        selection.sort()
        return selection, y_codes[selection]
    else:
        return np.arange(n_samples), y_codes


def _feature_selection(untried_indices, m_try):
    selection_len = min(m_try, len(untried_indices))
    return np.random.choice(untried_indices, size=selection_len, replace=False)


@task(returns=tuple)
def _test_splits(sample, y_s, n_classes, feature_indices, *features):
    min_score = float_info.max
    b_value = None
    b_index = None
    for t in range(len(feature_indices)):
        feature = features[t]
        score, value = test_split(sample, y_s, feature, n_classes)
        if score < min_score:
            min_score = score
            b_index = feature_indices[t]
            b_value = value
    return min_score, b_value, b_index


def _get_groups(sample, y_s, features_mmap, index, value):
    if index is None:
        empty_sample = np.array([], dtype=np.int64)
        empty_labels = np.array([], dtype=np.int8)
        return sample, y_s, empty_sample, empty_labels
    feature = features_mmap[index][sample]
    mask = feature < value
    left = sample[mask]
    right = sample[~mask]
    y_l = y_s[mask]
    y_r = y_s[~mask]
    return left, y_l, right, y_r


def _compute_leaf_info(y_s, n_classes):
    frequencies = np.bincount(y_s, minlength=n_classes)
    mode = np.argmax(frequencies)
    return _LeafInfo(len(y_s), frequencies, mode)


def _split_node_wrapper(sample, n_features, y_s, n_classes, m_try,
                        samples_file=None, features_file=None):
    if features_file is not None:
        return _split_node_using_features(sample, n_features, y_s, n_classes,
                                          m_try, features_file)
    elif samples_file is not None:
        return _split_node(sample, n_features, y_s, n_classes, m_try,
                           samples_file)
    else:
        raise ValueError('Invalid combination of arguments. samples_file is '
                         'None and features_file is None.')


@task(features_file=FILE_IN, returns=(object, list, list, list, list))
def _split_node_using_features(sample, n_features, y_s, n_classes, m_try,
                               features_file):
    features_mmap = np.load(features_file, mmap_mode='r', allow_pickle=False)
    return _compute_split(sample, n_features, y_s, n_classes, m_try,
                          features_mmap)


@task(samples_file=FILE_IN, returns=(object, list, list, list, list))
def _split_node(sample, n_features, y_s, n_classes, m_try, samples_file):
    features_mmap = np.load(samples_file, mmap_mode='r', allow_pickle=False).T
    return _compute_split(sample, n_features, y_s, n_classes, m_try,
                          features_mmap)


def _compute_split(sample, n_features, y_s, n_classes, m_try, features_mmap):
    node_info = left_group = y_l = right_group = y_r = None
    split_ended = False
    tried_indices = []
    while not split_ended:
        untried_indices = np.setdiff1d(np.arange(n_features), tried_indices)
        index_selection = _feature_selection(untried_indices, m_try)
        b_score = float_info.max
        b_index = None
        b_value = None
        for index in index_selection:
            feature = features_mmap[index]
            score, value = test_split(sample, y_s, feature, n_classes)
            if score < b_score:
                b_score, b_value, b_index = score, value, index
        groups = _get_groups(sample, y_s, features_mmap, b_index, b_value)
        left_group, y_l, right_group, y_r = groups
        if left_group.size and right_group.size:
            split_ended = True
            node_info = _InnerNodeInfo(b_index, b_value)
        else:
            tried_indices.extend(list(index_selection))
            if len(tried_indices) == n_features:
                split_ended = True
                node_info = _compute_leaf_info(y_s, n_classes)

    return node_info, left_group, y_l, right_group, y_r


def _build_subtree_wrapper(sample, y_s, n_features, max_depth, n_classes,
                           m_try, samples_file, features_file):
    if features_file is not None:
        return _build_subtree_using_features(sample, y_s, n_features,
                                             max_depth, n_classes, m_try,
                                             samples_file, features_file)
    else:
        return _build_subtree(sample, y_s, n_features, max_depth, n_classes,
                              m_try, samples_file)


@task(samples_file=FILE_IN, features_file=FILE_IN, returns=_Node)
def _build_subtree_using_features(sample, y_s, n_features, max_depth,
                                  n_classes, m_try, samples_file,
                                  features_file):
    return _compute_build_subtree(sample, y_s, n_features, max_depth,
                                  n_classes, m_try, samples_file,
                                  features_file=features_file)


@task(samples_file=FILE_IN, returns=_Node)
def _build_subtree(sample, y_s, n_features, max_depth, n_classes, m_try,
                   samples_file):
    return _compute_build_subtree(sample, y_s, n_features, max_depth,
                                  n_classes, m_try, samples_file)


def _compute_build_subtree(sample, y_s, n_features, max_depth, n_classes,
                           m_try, samples_file, features_file=None,
                           use_sklearn=True, sklearn_max=1e8):
    np.random.seed()
    if not sample.size:
        return []
    if features_file is not None:
        mmap = np.load(features_file, mmap_mode='r', allow_pickle=False)
    else:
        mmap = np.load(samples_file, mmap_mode='r', allow_pickle=False).T
    subtree = _Node()
    tree_traversal = [(subtree, sample, y_s, 0)]
    while tree_traversal:
        node, sample, y_s, depth = tree_traversal.pop()
        if depth < max_depth:
            if use_sklearn and n_features * len(sample) <= sklearn_max:
                if max_depth == np.inf:
                    sklearn_max_depth = None
                else:
                    sklearn_max_depth = max_depth - depth
                dt = SklearnDTClassifier(max_features=m_try,
                                         max_depth=sklearn_max_depth)
                unique = np.unique(sample, return_index=True,
                                   return_counts=True)
                sample, new_indices, sample_weight = unique
                x = _get_sample_attributes(samples_file, sample)
                y_s = y_s[new_indices]
                dt.fit(x, y_s, sample_weight=sample_weight, check_input=False)
                node.content = _SkTreeWrapper(dt)
            else:
                split = _compute_split(sample, n_features, y_s, n_classes,
                                       m_try, mmap)
                node_info, left_group, y_l, right_group, y_r = split
                node.content = node_info
                if isinstance(node_info, _InnerNodeInfo):
                    node.left = _Node()
                    node.right = _Node()
                    tree_traversal.append((node.right, right_group, y_r,
                                           depth + 1))
                    tree_traversal.append((node.left, left_group, y_l,
                                           depth + 1))
        else:
            node.content = _compute_leaf_info(y_s, n_classes)
    return subtree


@task(returns=list)
def _merge(*object_list):
    return object_list


def _get_subtree_path(subtree_index, distr_depth):
    if distr_depth == 0:
        return ''
    return bin(subtree_index)[2:].zfill(distr_depth)


def _get_predicted_indices(samples, tree, nodes_info, path):
    indices_mask = np.full((len(samples),), True)
    for direction in path:
        node_info = nodes_info[tree.content]
        col = node_info.index
        value = node_info.value
        if direction == '0':
            indices_mask[indices_mask] = samples[indices_mask, col] <= value
            tree = tree.left
        else:
            indices_mask[indices_mask] = samples[indices_mask, col] > value
            tree = tree.right
    return indices_mask


@task(returns=1)
def _predict_branch(subset, tree, nodes_info, subtree_index, subtree,
                    distr_depth):
    samples = subset.samples
    path = _get_subtree_path(subtree_index, distr_depth)
    indices_mask = _get_predicted_indices(samples, tree, nodes_info, path)
    prediction = subtree.predict(samples[indices_mask])
    return indices_mask, prediction


@task(returns=1)
def _predict_branch_proba(subset, tree, nodes_info, subtree_index, subtree,
                          distr_depth, n_classes):
    samples = subset.samples
    path = _get_subtree_path(subtree_index, distr_depth)
    indices_mask = _get_predicted_indices(samples, tree, nodes_info, path)
    prediction = subtree.predict_proba(samples[indices_mask], n_classes)
    return indices_mask, prediction


@task(returns=list)
def _merge_branches(n_classes, *predictions):
    samples_len = len(predictions[0][0])
    if n_classes is not None:
        shape = (samples_len, n_classes)
    else:
        shape = (samples_len,)
    merged_prediction = np.empty(shape, dtype=np.int64)
    for selected, prediction in predictions:
        merged_prediction[selected] = prediction
    return merged_prediction
