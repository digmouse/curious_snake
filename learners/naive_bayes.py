# Copyright 2000 by Jeffrey Chang.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

"""This provides code for a general Naive Bayes learner.

Naive Bayes is a supervised classification algorithm that uses Bayes
rule to compute the fit between a new observation and some previously
observed data.  The observations are discrete feature vectors, with
the Bayes assumption that the features are independent.  Although this
is hardly ever true, the classifier works well enough in practice.

Glossary:
observation    A feature vector of discrete data.
class          A possible classification for an observation.


Classes:
NaiveBayes     Holds information for a naive Bayes classifier.

Functions:
train          Train a new naive Bayes classifier.
calculate      Calculate the probabilities of each class, given an observation.
classify       Classify an observation into a class.

"""
# To Do:
# add code to help discretize data
# use objects

import pdb

try:
    import numpy
    from numpy import *
except ImportError, x:
    raise ImportError, "This module requires NumPy"

from Bio import mathfns, listfns

class NaiveBayes:
    """Holds information for a NaiveBayes classifier.

    Members:
    classes         List of the possible classes of data.
    p_conditional   CLASS x DIM array of dicts of value -> P(value|class,dim)
    p_prior         List of the prior probabilities for every class.
    dimensionality  Dimensionality of the data.

    """
    def __init__(self):
        self.classes = []
        self.p_conditional = None
        self.p_prior = []
        self.dimensionality = None

def calculate(nb, observation, scale=0):
    """calculate(nb, observation[, scale]) -> probability dict

    Calculate log P(class|observation) for each class.  nb is a NaiveBayes
    classifier that has been trained.  observation is a list representing
    the observed data.  scale is whether the probability should be
    scaled by P(observation).  By default, no scaling is done.  The return
    value is a dictionary where the keys is the class and the value is the
    log probability of the class.

    """
    # P(class|observation) = P(observation|class)*P(class)/P(observation)
    # Taking the log:
    # lP(class|observation) = lP(observation|class)+lP(class)-lP(observation)

    # Make sure the observation has the right dimensionality.
    if len(observation) != nb.dimensionality:
        raise ValueError, "observation in %d dimension, but classifier in %d" \
              % (len(observation), nb.dimensionality)

    # Calculate log P(observation|class) for every class.
    lp_observation_class = []     # list of log P(observation|class)
    for i in range(len(nb.classes)):
        # log P(observation|class) = SUM_i log P(observation_i|class)
        probs = [None] * len(observation)
        for j in range(len(observation)):
            probs[j] = nb.p_conditional[i][j].get(observation[j], 0)
        
        lprobs = [mathfns.safe_log(x, -10000) for x in probs]
        lprob = sum(lprobs)
        lp_observation_class.append(lprob)

    # Calculate log P(class).
    lp_prior = map(math.log, nb.p_prior)

    # Calculate log P(observation).
    lp_observation = 0.0          # P(observation)
    if scale:   # Only calculate this if requested.
        # log P(observation) = log SUM_i P(observation|class_i)P(class_i)
        pdb.set_trace()
        obs = zeros(len(nb.classes))
        for i in range(len(nb.classes)):
            obs[i] = mathfns.safe_exp(lp_prior[i]+lp_observation_class[i],
                                      under=1E-300)
        lp_observation = math.log(sum(obs))

    # Calculate log P(class|observation).
    lp_class_observation = {}      # Dict of class : log P(class|observation)
    for i in range(len(nb.classes)):
        lp_class_observation[nb.classes[i]] = \
            lp_observation_class[i] + lp_prior[i] - lp_observation

    return lp_class_observation

def classify(nb, observation):
    """classify(nb, observation) -> class

    Classify an observation into a class.

    """
    # The class is the one with the highest probability.
    probs = calculate(nb, observation, scale=0)
    print "PROBS"
    print probs
    max_prob = max_class = None
    
    for klass in nb.classes:
        if max_prob is None or probs[klass] > max_prob:
            max_prob, max_class = probs[klass], klass
    return max_class


def train(training_set, results, priors=None, typecode=None):
    """train(training_set, results[, priors]) -> NaiveBayes

    Train a naive bayes classifier on a training set.  training_set is a
    list of observations.  results is a list of the class assignments
    for each observation.  Thus, training_set and results must be the same
    length.  priors is an optional dictionary specifying the prior
    probabilities for each type of result.  If not specified, the priors
    will be estimated from the training results.

    """
    if not len(training_set):
        raise ValueError, "No data in the training set."
    if len(training_set) != len(results):
        raise ValueError, "training_set and results should be parallel lists."

    # If no typecode is specified, try to pick a reasonable one.  If
    # training_set is a Numeric array, then use that typecode.
    # Otherwise, choose a reasonable default.
    # XXX NOT IMPLEMENTED

    # Check to make sure each vector in the training set has the same
    # dimensionality.
    dimensions = [len(x) for x in training_set]
    if min(dimensions) != max(dimensions):
        raise ValueError, "observations have different dimensionality"

    nb = NaiveBayes()
    nb.dimensionality = dimensions[0]
    
    # Get a list of all the classes.
    nb.classes = listfns.items(results)
    nb.classes.sort()   # keep it tidy
    
    # Estimate the prior probabilities for the classes.
    if priors is not None:
        percs = priors
    else:
        percs = listfns.contents(results)
    nb.p_prior = zeros(len(nb.classes))
    for i in range(len(nb.classes)):
        nb.p_prior[i] = percs[nb.classes[i]]

    # Collect all the observations in class.  For each class, make a
    # matrix of training instances versus dimensions.  I might be able
    # to optimize this with Numeric, if the training_set parameter
    # were guaranteed to be a matrix.  However, this may not be the
    # case, because the client may be hacking up a sparse matrix or
    # something.
    c2i = listfns.itemindex(nb.classes)      # class to index of class
    observations = [[] for c in nb.classes]  # separate observations by class
    for i in range(len(results)):
        klass, obs = results[i], training_set[i]
        observations[c2i[klass]].append(obs)
    # Now make the observations Numeric matrics.
    for i in range(len(observations)):
        # XXX typecode must be specified!
        observations[i] = asarray(observations[i], typecode)

    # Calculate P(value|class,dim) for every class.
    # This is a good loop to optimize.
    nb.p_conditional = []
    for i in range(len(nb.classes)):
        class_observations = observations[i]   # observations for this class
        nb.p_conditional.append([None] * nb.dimensionality)
        for j in range(nb.dimensionality):
            # Collect all the values in this dimension.
            values = class_observations[:, j]

            # Add pseudocounts here.  This needs to be parameterized.
            #values = list(values) + range(len(nb.classes))  # XXX add 1
            
            # Estimate P(value|class,dim)
            nb.p_conditional[i][j] = listfns.contents(values)
    return nb
