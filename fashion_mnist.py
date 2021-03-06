# -*- coding: utf-8 -*-
"""Fashion-MNIST.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1HSwutAV3YCOOyQoBduTzMgmzMgyj8EeT

# Fashion-MNIST

This intro use the updated dataset fashion-mnist from Zalando.
The dataset contains 28x28 images of clothes.

We will start by setting up the environment.
"""

# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Functions for downloading and reading MNIST data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import gzip

import numpy
from six.moves import xrange  # pylint: disable=redefined-builtin

from tensorflow.contrib.learn.python.learn.datasets import base
from tensorflow.python.framework import dtypes

SOURCE_URL = 'https://storage.googleapis.com/tensorflow/tf-keras-datasets/'


def _read32(bytestream):
    dt = numpy.dtype(numpy.uint32).newbyteorder('>')
    return numpy.frombuffer(bytestream.read(4), dtype=dt)[0]


def extract_images(f):
    """Extract the images into a 4D uint8 numpy array [index, y, x, depth].

    Args:
    f: A file object that can be passed into a gzip reader.

    Returns:
    data: A 4D uint8 numpy array [index, y, x, depth].

    Raises:
    ValueError: If the bytestream does not start with 2051.

    """
    print('Extracting', f.name)
    with gzip.GzipFile(fileobj=f) as bytestream:
        magic = _read32(bytestream)
        if magic != 2051:
            raise ValueError('Invalid magic number %d in MNIST image file: %s' %
                           (magic, f.name))
        num_images = _read32(bytestream)
        rows = _read32(bytestream)
        cols = _read32(bytestream)
        buf = bytestream.read(rows * cols * num_images)
        data = numpy.frombuffer(buf, dtype=numpy.uint8)
        data = data.reshape(num_images, rows, cols, 1)
        return data


def dense_to_one_hot(labels_dense, num_classes):
    """Convert class labels from scalars to one-hot vectors."""
    num_labels = labels_dense.shape[0]
    index_offset = numpy.arange(num_labels) * num_classes
    labels_one_hot = numpy.zeros((num_labels, num_classes))
    labels_one_hot.flat[index_offset + labels_dense.ravel()] = 1
    return labels_one_hot


def extract_labels(f, one_hot=False, num_classes=10):
    """Extract the labels into a 1D uint8 numpy array [index].

    Args:
    f: A file object that can be passed into a gzip reader.
    one_hot: Does one hot encoding for the result.
    num_classes: Number of classes for the one hot encoding.

    Returns:
    labels: a 1D uint8 numpy array.

    Raises:
    ValueError: If the bystream doesn't start with 2049.
    """
    print('Extracting', f.name)
    with gzip.GzipFile(fileobj=f) as bytestream:
        magic = _read32(bytestream)
        if magic != 2049:
            raise ValueError('Invalid magic number %d in MNIST label file: %s' %
                           (magic, f.name))
        num_items = _read32(bytestream)
        buf = bytestream.read(num_items)
        labels = numpy.frombuffer(buf, dtype=numpy.uint8)
        if one_hot:
            return dense_to_one_hot(labels, num_classes)
        return labels


class DataSet(object):

    def __init__(self,
               images,
               labels,
               fake_data=False,
               one_hot=False,
               dtype=dtypes.float32,
               reshape=True):
        """Construct a DataSet.
        one_hot arg is used only if fake_data is true.  `dtype` can be either
        `uint8` to leave the input as `[0, 255]`, or `float32` to rescale into
        `[0, 1]`.
        """
        dtype = dtypes.as_dtype(dtype).base_dtype
        if dtype not in (dtypes.uint8, dtypes.float32):
            raise TypeError('Invalid image dtype %r, expected uint8 or float32' %
                          dtype)
        if fake_data:
            self._num_examples = 10000
            self.one_hot = one_hot
        else:
            assert images.shape[0] == labels.shape[0], ('images.shape: %s labels.shape: %s' % (images.shape, labels.shape))
            self._num_examples = images.shape[0]

            # Convert shape from [num examples, rows, columns, depth]
            # to [num examples, rows*columns] (assuming depth == 1)
            if reshape:
                assert images.shape[3] == 1
                images = images.reshape(images.shape[0],
                                        images.shape[1] * images.shape[2])
            if dtype == dtypes.float32:
                # Convert from [0, 255] -> [0.0, 1.0].
                images = images.astype(numpy.float32)
                images = numpy.multiply(images, 1.0 / 255.0)
        self._images = images
        self._labels = labels
        self._epochs_completed = 0
        self._index_in_epoch = 0

    @property
    def images(self):
        return self._images

    @property
    def labels(self):
        return self._labels

    @property
    def num_examples(self):
        return self._num_examples

    @property
    def epochs_completed(self):
        return self._epochs_completed

    def next_batch(self, batch_size, fake_data=False):
        """Return the next `batch_size` examples from this data set."""
        if fake_data:
            fake_image = [1] * 784
            if self.one_hot:
                fake_label = [1] + [0] * 9
            else:
                fake_label = 0
            return [fake_image for _ in xrange(batch_size)], [
              fake_label for _ in xrange(batch_size)
            ]
        start = self._index_in_epoch
        self._index_in_epoch += batch_size
        if self._index_in_epoch > self._num_examples:
            # Finished epoch
            self._epochs_completed += 1
            # Shuffle the data
            perm = numpy.arange(self._num_examples)
            numpy.random.shuffle(perm)
            self._images = self._images[perm]
            self._labels = self._labels[perm]
            # Start next epoch
            start = 0
            self._index_in_epoch = batch_size
            assert batch_size <= self._num_examples
        end = self._index_in_epoch
        return self._images[start:end], self._labels[start:end]


def read_data_sets(train_dir,
                   fake_data=False,
                   one_hot=False,
                   dtype=dtypes.float32,
                   reshape=True,
                   validation_size=5000):
    if fake_data:

        def fake():
            return DataSet([], [], fake_data=True, one_hot=one_hot, dtype=dtype)

        train = fake()
        validation = fake()
        test = fake()
        return base.Datasets(train=train, validation=validation, test=test)

    TRAIN_IMAGES = 'train-images-idx3-ubyte.gz'
    TRAIN_LABELS = 'train-labels-idx1-ubyte.gz'
    TEST_IMAGES = 't10k-images-idx3-ubyte.gz'
    TEST_LABELS = 't10k-labels-idx1-ubyte.gz'

    local_file = base.maybe_download(TRAIN_IMAGES, train_dir,
                                   SOURCE_URL + TRAIN_IMAGES)
    with open(local_file, 'rb') as f:
        train_images = extract_images(f)

        local_file = base.maybe_download(TRAIN_LABELS, train_dir,
                                   SOURCE_URL + TRAIN_LABELS)
    with open(local_file, 'rb') as f:
        train_labels = extract_labels(f, one_hot=one_hot)

        local_file = base.maybe_download(TEST_IMAGES, train_dir,
                                   SOURCE_URL + TEST_IMAGES)
    with open(local_file, 'rb') as f:
        test_images = extract_images(f)

        local_file = base.maybe_download(TEST_LABELS, train_dir,
                                   SOURCE_URL + TEST_LABELS)
    with open(local_file, 'rb') as f:
        test_labels = extract_labels(f, one_hot=one_hot)

    if not 0 <= validation_size <= len(train_images):
        raise ValueError(
            'Validation size should be between 0 and {}. Received: {}.'
            .format(len(train_images), validation_size))

    validation_images = train_images[:validation_size]
    validation_labels = train_labels[:validation_size]
    train_images = train_images[validation_size:]
    train_labels = train_labels[validation_size:]

    train = DataSet(train_images, train_labels, dtype=dtype, reshape=reshape)
    validation = DataSet(validation_images,
                       validation_labels,
                       dtype=dtype,
                       reshape=reshape)
    test = DataSet(test_images, test_labels, dtype=dtype, reshape=reshape)

    return base.Datasets(train=train, validation=validation, test=test)


def load_mnist(train_dir='MNIST-data'):
    return read_data_sets(train_dir)
  
print("Done")

!pip install -q import-ipynb

# Import libraries
import import_ipynb
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow.python.framework import ops
#from tensorflow.examples.tutorials.mnist import input_data

# Import Fashion MNIST dataset
fashion_mnist = read_data_sets('input/data', one_hot=True)


print("Done")

"""### Print the shape of the data
Display the shape of data in terms of rows and columns of training and test data
"""

# Shapes of training set
print("Training set (images) shape: {shape}".format(shape=fashion_mnist.train.images.shape))
print("Training set (labels) shape: {shape}".format(shape=fashion_mnist.train.labels.shape))
print("-"*60)
# Shapes of test set
print("Test set (images) shape: {shape}".format(shape=fashion_mnist.test.images.shape))
print("Test set (labels) shape: {shape}".format(shape=fashion_mnist.test.labels.shape))

"""## Let's visualize some of the data

The intro does say it is images of clothes - but let's find out ourselves. Run the cell

Go ahead and choose an image index yourself. Change the "sample_index_1/2" variables under the red text below"
"""

# Create dictionary of target classes
label_dict = { 0: 'T-shirt/top', 1: 'Trouser', 2: 'Pullover', 3: 'Dress', 4: 'Coat', 5: 'Sandal', 6: 'Shirt', 7: 'Sneaker',
 8: 'Bag', 9: 'Ankle boot'}

"""
    Try changing the number in sample_index_1/2
    Then run the cell.
    Did the images update?
"""
sample_index_1 = 47
sample_index_2 = 27

fig=plt.figure(figsize=(8,8))
# Get 28x28 image
sample_1 = fashion_mnist.train.images[sample_index_1].reshape(28,28)
# Get corresponding integer label from one-hot encoded data
sample_label_1 = np.where(fashion_mnist.train.labels[sample_index_1] == 1)[0][0]
# Plot sample
print("y = {label_index} ({label})".format(label_index=sample_label_1, label=label_dict[sample_label_1]))
fig.add_subplot(1,2,1)
plt.imshow(sample_1, cmap='Greys')

# Get 28x28 image
sample_2 = fashion_mnist.train.images[sample_index_2].reshape(28,28)
# Get corresponding integer label from one-hot encoded data
sample_label_2 = np.where(fashion_mnist.train.labels[sample_index_2] == 1)[0][0]
# Plot sample
print("y = {label_index} ({label})".format(label_index=sample_label_2, label=label_dict[sample_label_2]))
fig.add_subplot(1,2,2)
plt.imshow(sample_2, cmap='Greys')

"""# Building our network

Hopefully you're not tired of all the boring stuff like importing data.
Let's begin with the fun part.

## Steps
#### 1 -  Set network parameters
#### 2 - Create placeholders
#### 3 - Initialize placeholders
#### 4 - Forward propagation
#### 5 - Compute cost
#### 6 - Backpropagation
#### 7 - Put it together

## 1 - Set network parameters

- The first layer: Input layer
The first layer consist of the number of input nodes. In out case, this is 28 pixel x 28 pixel = 784.

- The second and third layer: Hidden layers
The second and third layer are hidden layers, and you can decide yourself how many nodes each hidden layer will have. Here you can test with different number of nodes.

- The fourth layer: Out layer
The output layer consists of number of classes it is able to predict. In our case, this is 10. Which node that gets chosen is determined by the softmax function.

## TASK 1 - Deside layers

- What is the number of input nodes? (hint: pizel size of an image)
- Explore different node sizes of the hidden layers
- What is the output node size? (hint: number of labels
"""

# Set network parameters
n_input = XX # Fashion MNIST data input (image: 28*28=784)
n_hidden_1 = 128 # Units in first hidden layer
n_hidden_2 = 128 # Units in second hidden layer
n_classes = XX # Fashion MNIST total classes (10 different target clothes)
n_samples = fashion_mnist.train.num_examples # Number of examples in training set 

print("Number of training samples: " + str(n_samples))
print("\nDone")

"""## 2 - Create placeholders

Creating a function which takes some info about the dimensions of the data - and returns Tensorflow placeholders. We will pass data while running our nerual network using these placeholders:
"""

# Create placeholders
def create_placeholders(n_x, n_y):
    '''
    Creates the placeholders for the tensorflow session.

    Arguments:
    n_x -- scalar, size of an image vector (28*28 = 784)
    n_y -- scalar, number of classes (10)

    Returns:
    X -- placeholder for the data input, of shape [n_x, None] and dtype "float"
    Y -- placeholder for the input labels, of shape [n_y, None] and dtype "float"
    '''

    X = tf.placeholder(tf.float32, [n_x, None], name="X")
    Y = tf.placeholder(tf.float32, [n_y, None], name="Y")
 
    return X, Y

print("Done")

"""## 3 - Initialize Placeholders

Initialize placeholders:
Here we initialize our weights with values.
"""

def initialize_parameters():
    '''
    Initializes parameters to build a neural network with tensorflow. The shapes are:
                        W1 : [n_hidden_1, n_input]
                        b1 : [n_hidden_1, 1]
                        W2 : [n_hidden_2, n_hidden_1]
                        b2 : [n_hidden_2, 1]
                        W3 : [n_classes, n_hidden_2]
                        b3 : [n_classes, 1]
    
    Returns:
    parameters -- a dictionary of tensors containing W1, b1, W2, b2, W3, b3
    '''
    
    # Set random seed for reproducibility
    tf.set_random_seed(42)
    
    # Initialize weights and biases for each layer
    # First hidden layer
    W1 = tf.get_variable("W1", [n_hidden_1, n_input], initializer=tf.contrib.layers.xavier_initializer(seed=42))
    b1 = tf.get_variable("b1", [n_hidden_1, 1], initializer=tf.zeros_initializer())
    
    # Second hidden layer
    W2 = tf.get_variable("W2", [n_hidden_2, n_hidden_1], initializer=tf.contrib.layers.xavier_initializer(seed=42))
    b2 = tf.get_variable("b2", [n_hidden_2, 1], initializer=tf.zeros_initializer())
    
    # Output layer
    W3 = tf.get_variable("W3", [n_classes, n_hidden_2], initializer=tf.contrib.layers.xavier_initializer(seed=42))
    b3 = tf.get_variable("b3", [n_classes, 1], initializer=tf.zeros_initializer())
    
    # Store initializations as a dictionary of parameters
    parameters = {
        "W1": W1,
        "b1": b1,
        "W2": W2,
        "b2": b2,
        "W3": W3,
        "b3": b3
    }
    
    return parameters

"""## 4 - Forward propagation

Forward propagation is how our neural network will make a prediction given our input image. It all starts by putting an image into the input layer. From there on, the data is processed forward from input layer -> hidden layer 1 -> hidden layer 2 -> out layer -> prediction of class.

## TASK 2 - Configure the last layer on the neural network

Take a look the layer Z1 and Z2 - and configure Z3.
"""

def forward_propagation(X, parameters):
    '''
    Implements the forward propagation for the model: 
    LINEAR -> RELU -> LINEAR -> RELU -> LINEAR -> SOFTMAX
    
    Arguments:
    X -- input dataset placeholder, of shape (input size, number of examples)
    parameters -- python dictionary containing your parameters "W1", "b1", "W2", "b2", "W3", "b3"
                  the shapes are given in initialize_parameters
    Returns:
    Z3 -- the output of the last LINEAR unit
    '''
    
    # Retrieve parameters from dictionary
    W1 = parameters['W1']
    b1 = parameters['b1']
    W2 = parameters['W2']
    b2 = parameters['b2']
    W3 = parameters['W3']
    b3 = parameters['b3']
    
    # Carry out forward propagation      
    Z1 = tf.add(tf.matmul(W1,X), b1)     
    A1 = tf.nn.relu(Z1)                  
    Z2 = tf.add(tf.matmul(W2,A1), b2)    
    A2 = tf.nn.relu(Z2)                  
    Z3 = 
    
    return Z3

"""## 5 - Compute the cost

Next, we can create a function to compute the cost based on the output from our last linear layer (Z3) and the actual target classes (Y). The cost is just a measure of the difference between the target class predicted by our neural network and the actual target class in Y.

This cost will be used during backpropagation to update the weights — the greater the cost, the greater the magnitude of each parameter update.
"""

def compute_cost(Z3, Y):
    '''
    Computes the cost
    
    Arguments:
    Z3 -- output of forward propagation (output of the last LINEAR unit), of shape (10, number_of_examples)
    Y -- "true" labels vector placeholder, same shape as Z3
    
    Returns:
    cost - Tensor of the cost function
    '''
    
    # Get logits (predictions) and labels
    logits = tf.transpose(Z3)
    labels = tf.transpose(Y)
    
    # Compute cost
    cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=logits, labels=labels))
    
    return cost

"""## 6 - Backpropagation

Backprop is an essential step for our neural network, because it decides how much to update our parameters (weights and biases) based on the cost from the previous computation.

Our implementation uses the well-known Adam optimiser for backpropagation. We will implement this in the following step where we assemble our model.

## 7 - Putting it all together

Finally, let’s combine all our previously-created functions into one single function called model(). This function will create our placeholders, initialise parameters, carry out forward prop and backprop, and also help us visualise our cost decrease over time.

The function will take in the training and the test sets, an option to print out costs after each epoch, as well as some (optional) hyperparameter values such as:

- learning_rate (learning rate of the optimisation)
- num_epochs (number of epochs of the optimisation loop)
- minibatch_size (size of a minibatch)

After building the network and training it, the function will compute the model’s accuracies, and return the final updated parameters dictionary.
"""

def model(train, test, learning_rate=0.0001, num_epochs=16, minibatch_size=32, print_cost=True, graph_filename='costs'):
    '''
    Implements a four-layer tensorflow neural network: INPUT->HIDDEN1->HIDDEN2->SOFTMAX.
    
    Arguments:
    train -- training set
    test -- test set
    learning_rate -- learning rate of the optimization
    num_epochs -- number of epochs of the optimization loop
    minibatch_size -- size of a minibatch
    print_cost -- True to print the cost every epoch
    
    Returns:
    parameters -- parameters learnt by the model. They can then be used to predict.
    '''
    
    print("Setting up model..")

    
    # Ensure that model can be rerun without overwriting tf variables
    ops.reset_default_graph()
    # For reproducibility
    tf.set_random_seed(42)
    seed = 42
    # Get input and output shapes
    (n_x, m) = train.images.T.shape
    n_y = train.labels.T.shape[0]
    
    costs = []
    
    # Create placeholders of shape (n_x, n_y)
    X, Y = create_placeholders(n_x, n_y)
    # Initialize parameters
    parameters = initialize_parameters()
    
    # Forward propagation
    Z3 = forward_propagation(X, parameters)
    # Compute cost
    cost = compute_cost(Z3, Y)
    # Backpropagation (using Adam optimizer)
    optimizer = tf.train.AdamOptimizer(learning_rate).minimize(cost)
    
    # Initialize variables
    init = tf.global_variables_initializer()
    
    true_label_last_mini_batch = []
    
    # Start session to compute Tensorflow graph
    with tf.Session() as sess:
        print("Initializing Tensorflow session..")
        # Run initialization
        sess.run(init)
        # Training loop
        for epoch in range(num_epochs):
            
            epoch_cost = 0.
            num_minibatches = int(m / minibatch_size)
            seed = seed + 1
            
            for i in range(num_minibatches):
                
                # Get next batch of training data and labels
                minibatch_X, minibatch_Y = train.next_batch(minibatch_size)
                
                # Execute optimizer and cost function
                _, minibatch_cost = sess.run([optimizer, cost], feed_dict={X: minibatch_X.T, Y: minibatch_Y.T})
                      
                # Update epoch cost
                epoch_cost += minibatch_cost / num_minibatches
                
            # Print the cost every epoch
            if print_cost == True:
                print("Cost after epoch {epoch_num}: {cost}".format(epoch_num=epoch, cost=epoch_cost))
                costs.append(epoch_cost)
        
        # Plot costs
        #plt.figure(figsize=(16,5))
        #plt.plot(np.squeeze(costs), color='#2A688B')
        plt.xlim(0, num_epochs-1)
        plt.ylabel("cost")
        plt.xlabel("iterations")
        plt.title("learning rate = {rate}".format(rate=learning_rate))
        plt.savefig(graph_filename, dpi=300)
        plt.show()
        
        # Save parameters
        parameters = sess.run(parameters)
        print("Parameters have been trained!")

        # Calculate correct predictions
        correct_prediction = tf.equal(tf.argmax(Z3), tf.argmax(Y))
        
        # Calculate accuracy on test set
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))
        
        print ("Train Accuracy:", accuracy.eval({X: train.images.T, Y: train.labels.T}))
        print ("Test Accuracy:", accuracy.eval({X: test.images.T, Y: test.labels.T}))
        
        
        # Plot a random sample of 10 test images, their predicted labels and ground truth
        figure = plt.figure(figsize=(20, 8))
        for i, index in enumerate(np.random.choice(test.images.shape[0], size=15, replace=False)):
            ax = figure.add_subplot(3, 5, i + 1, xticks=[], yticks=[])
            # Display each image
            ax.imshow(np.squeeze(test.images[index].reshape(28,28)),cmap='Greys')
            predict_index = np.argmax(Z3.eval(feed_dict={X:test.images[index].reshape(784,1)}))
            true_index = np.argmax(test.labels[index])
            # Set the title for each image
            ax.set_title("{} (solution: {})".format(label_dict[predict_index], 
                                          label_dict[true_index]),
                                          color=("green" if predict_index == true_index else "red"))

        return parameters

print("Done")

"""## TASK 3 - Run with different input parameters 

Experiment and decide the following parameters:

- learning_rate
- num_epochs
- minibatch_size

Let's do this
"""

# Running our model
train = fashion_mnist.train
test = fashion_mnist.test

# Decide 
learning_rate = # Choose between 0.0001 and 0.1
num_epochs = # Choose between 1 and 100. More epochs = more training
minibatch_size = # Choose number of images each bach should coontain. Between 1 and 55000

parameters = model(train, test, learning_rate)