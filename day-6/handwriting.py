# -*- coding: utf-8 -*-
"""Handwriting.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1rBcLonHFlBjklauyHiZQrMw-8thlVJQk

# Imports
"""

import tensorflow as tf
from numpy.random import seed
seed(888)
tf.random.set_seed(404)
from time import strftime

import os
import numpy as np
from PIL import Image

"""# Constants"""

X_TRAIN_PATH = "/content/digit_xtrain.csv"
X_TEST_PATH = "/content/digit_xtest.csv"
Y_TRAIN_PATH = "/content/digit_ytrain.csv"
Y_TEST_PATH = "/content/digit_ytest.csv"
LOGGING_PATH = 'tensorboard_mnist_digit_logs/'
NR_CLASSES = 10
VALIDATION_SIZE = 10000
IMAGE_WIDTH = 28
IMAGE_HEIGHT = 28
CHANNELS = 1
TOTAL_INPUTS = IMAGE_WIDTH*IMAGE_HEIGHT*CHANNELS

"""# GET THE DATA

"""

# Commented out IPython magic to ensure Python compatibility.
# % time
y_train_all = np.loadtxt(Y_TRAIN_PATH,delimiter=',',dtype=int)
y_test = np.loadtxt(Y_TEST_PATH,delimiter=',',dtype=int)

x_train_all = np.genfromtxt(X_TRAIN_PATH,delimiter=',',dtype=int)
x_test = np.loadtxt(X_TEST_PATH,delimiter=',',dtype=int)

x_train_all.shape

y_train_all[:5]

"""# Data Preprocessing"""

# rescale
x_train_all, x_test_all = x_train_all/255.0 , x_test_all/255.0

"""### one hot encoding"""

y_train_all = np.eye(10)[y_train_all]

y_test_all = np.eye(10)[y_test_all]

"""### Create Validation dataset from training data"""

x_val = x_train_all[:VALIDATION_SIZE]
y_val = y_train_all[:VALIDATION_SIZE]
x_train = x_train_all[:VALIDATION_SIZE:]
y_train = y_train_all[:VALIDATION_SIZE]

"""# Setup Tensorflow Graph"""

x = tf.compat.v1.placeholder(shape=[None, 2], dtype=tf.float32)

X = tf.placeholder(tf.float32,shape=[None,784])

Y = tf.placeholder(tf.float32,shape=[None,10])

"""# Neural Network Architecture

### Hyperparameters
"""

nr_epochs=5
learning_rate = 1e-4
n_hidden1=512
n_hidden2=64

initial_w1 = tf.truncated_normal(shape=[738,n_hidden1],stddev=0.1,seed=42)
w1 = tf.Variable(initial_value=initial_w1)

initial_b1 = tf.constant(value=0.0,shape=[n_hidden1])
b1=tf.Variable(initial_value=initial_b1)

layer1_in = matmul()

def setup_layer(input, weight_dim, bias_dim, name):
    
    with tf.name_scope(name):
        initial_w = tf.truncated_normal(shape=weight_dim, stddev=0.1, seed=42)
        w = tf.Variable(initial_value=initial_w, name='W')

        initial_b = tf.constant(value=0.0, shape=bias_dim)
        b = tf.Variable(initial_value=initial_b, name='B')

        layer_in = tf.matmul(input, w) + b
        
        if name=='out':
            layer_out = tf.nn.softmax(layer_in)
        else:
            layer_out = tf.nn.relu(layer_in)
        
        tf.summary.histogram('weights', w)
        tf.summary.histogram('biases', b)
        
        return layer_out

# Model without dropout
# layer_1 = setup_layer(X, weight_dim=[TOTAL_INPUTS, n_hidden1], 
#                       bias_dim=[n_hidden1], name='layer_1')

# layer_2 = setup_layer(layer_1, weight_dim=[n_hidden1, n_hidden2], 
#                       bias_dim=[n_hidden2], name='layer_2')

# output = setup_layer(layer_2, weight_dim=[n_hidden2, NR_CLASSES], 
#                       bias_dim=[NR_CLASSES], name='out')

# model_name = f'{n_hidden1}-{n_hidden2} LR{learning_rate} E{nr_epochs}'

layer_1 = setup_layer(X, weight_dim=[TOTAL_INPUTS, n_hidden1], 
                      bias_dim=[n_hidden1], name='layer_1')

layer_drop = tf.nn.dropout(layer_1, keep_prob=0.8, name='dropout_layer')

layer_2 = setup_layer(layer_drop, weight_dim=[n_hidden1, n_hidden2], 
                      bias_dim=[n_hidden2], name='layer_2')

output = setup_layer(layer_2, weight_dim=[n_hidden2, NR_CLASSES], 
                      bias_dim=[NR_CLASSES], name='out')

model_name = f'{n_hidden1}-DO-{n_hidden2} LR{learning_rate} E{nr_epochs}'

"""# Tensorboard Setup"""

# Folder for Tensorboard

folder_name = f'{model_name} at {strftime("%H:%M")}'
directory = os.path.join(LOGGING_PATH, folder_name)

try:
    os.makedirs(directory)
except OSError as exception:
    print(exception.strerror)
else:
    print('Successfully created directories!')

"""# Loss, Optimisation & Metrics

#### Defining Loss Function
"""

with tf.name_scope('loss_calc'):
    loss = tf.reduce_mean(tf.compat.v1.nn.softmax_cross_entropy_with_logits_v2(labels=Y, logits=output))

"""#### Defining Optimizer"""

with tf.name_scope('optimizer'):
    optimizer = tf.compat.v1.train.AdamOptimizer(learning_rate)
    train_step = optimizer.minimize(loss)

"""#### Accuracy Metric"""

with tf.name_scope('accuracy_calc'):
    correct_pred = tf.equal(tf.argmax(output, axis=1), tf.argmax(Y, axis=1))
    accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

with tf.name_scope('performance'):
    tf.summary.scalar('accuracy', accuracy)
    tf.summary.scalar('cost', loss)

"""#### Check Input Images in Tensorboard"""

with tf.name_scope('show_image'):
    x_image = tf.reshape(X, [-1, 28, 28, 1])
    tf.summary.image('image_input', x_image, max_outputs=4)

"""# Run Session"""

sess = tf.compat.v1.Session()

"""#### Setup Filewriter and Merge Summaries"""

merged_summary = tf.compat.v1.summary.merge_all()

train_writer = tf.compat.v1.summary.FileWriter(directory + '/train')
train_writer.add_graph(sess.graph)

validation_writer = tf.compat.v1.summary.FileWriter(directory + '/validation')

"""#### Initialise all the variables"""

init = tf.compat.v1.global_variables_initializer()
sess.run(init)

"""### Batching the Data"""

size_of_batch = 1000

num_examples = y_train.shape[0]
nr_iterations = int(num_examples/size_of_batch)

index_in_epoch = 0

def next_batch(batch_size, data, labels):
    
    global num_examples
    global index_in_epoch
    
    start = index_in_epoch
    index_in_epoch += batch_size
    
    if index_in_epoch > num_examples:
        start = 0
        index_in_epoch = batch_size
    
    end = index_in_epoch
    
    return data[start:end], labels[start:end]

"""### Training Loop"""

for epoch in range(nr_epochs):
    
    # ============= Training Dataset =========
    for i in range(nr_iterations):
        
        batch_x, batch_y = next_batch(batch_size=size_of_batch, data=x_train, labels=y_train)
        
        feed_dictionary = {X:batch_x, Y:batch_y}
        
        sess.run(train_step, feed_dict=feed_dictionary)
        
    
    s, batch_accuracy = sess.run(fetches=[merged_summary, accuracy], feed_dict=feed_dictionary)
        
    train_writer.add_summary(s, epoch)
    
    print(f'Epoch {epoch} \t| Training Accuracy = {batch_accuracy}')
    
    # ================== Validation ======================
    
    summary = sess.run(fetches=merged_summary, feed_dict={X:x_val, Y:y_val})
    validation_writer.add_summary(summary, epoch)

print('Done training!')

"""# Make a Prediction"""

img = Image.open('/test_img.png')
img

bw = img.convert('L')

img_array = np.invert(bw)

img_array.shape

test_img = img_array.ravel()

test_img.shape

prediction = sess.run(fetches=tf.argmax(output, axis=1), feed_dict={X:[test_img]})

print(f'Prediction for test image is {prediction}')

"""# Testing and Evaluation"""

x_test1= x_test[:10]
y_test1= y_test[:10]

test_accuracy = sess.run(fetches=accuracy, feed_dict={X:x_test1, Y:y_test1})
print(f'Accuracy on test set is {test_accuracy:0.2%}')

"""# Reset for the Next Run"""

train_writer.close()
validation_writer.close()
sess.close()
tf.compat.v1.reset_default_graph()

"""# Code for 1st Part of Module"""

with tf.name_scope('hidden_1'):

    initial_w1 = tf.random.truncated_normal(shape=[TOTAL_INPUTS, n_hidden1], stddev=0.1, seed=42)
    w1 = tf.Variable(initial_value=initial_w1, name='w1')

    initial_b1 = tf.constant(value=0.0, shape=[n_hidden1])
    b1 = tf.Variable(initial_value=initial_b1, name='b1')

    layer1_in = tf.matmul(X, w1) + b1

    layer1_out = tf.nn.relu(layer1_in)
