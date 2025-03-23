# -*- coding: utf-8 -*-
"""CNN_Training_Code_Submission.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1nN3JXDZ056D6hV0CnID6-LbOmxd78Wwd
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import random
import cv2
import os
from sklearn.utils import shuffle


# Reading the data from the csv file
data_df = pd.read_csv('histopathologic-cancer-detection/train_labels.csv')
test_data_df = pd.read_csv('histopathologic-cancer-detection/sample_submission.csv')

# Path to Directories where training and test data is kept
train_path_dir = 'histopathologic-cancer-detection/train/'
test_path_dir = 'histopathologic-cancer-detection/test/'

img_train = os.listdir(train_path_dir)
img_test = os.listdir(test_path_dir)

print('Number of training images: ', len(img_train))
print('Number of test images: ', len(img_test))

# Using the default training dataset without balancing positive and negative labels
from sklearn.model_selection import train_test_split

train_df = data_df.copy()

# Splitting the training dataset into training and validation datasets
model_train_df, model_valid_df = train_test_split(train_df, test_size=0.2, random_state=39, stratify=train_df.label)

print(model_train_df.shape)
print(model_valid_df.shape)

# Concatenating .tif extension to the images name
model_train_df['id'] = model_train_df['id'] + '.tif'
model_valid_df['id'] = model_valid_df['id'] + '.tif'
test_data_df['id'] =  test_data_df['id'] + '.tif'

# Converting the labels in the training and validation datasets into string type
model_train_df['label'] = model_train_df['label'].astype(str)
model_valid_df['label'] = model_valid_df['label'].astype(str)
test_data_df['label'] = test_data_df['label'].astype(str)

# This section of code prepares the data for neural network training

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import backend as KBackend

KBackend.clear_session()

# Default image dimensions
DFLT_IMG_HEIGHT = 96
DFLT_IMG_WIDTH = 96

# Resized image dimensions
RSZ_IMG_HEIGHT = 128
RSZ_IMG_WIDTH = 128

# Define image dimensions
IMG_HEIGHT = 64
IMG_WIDTH = 64

# ALternative image dimensions
ALT_IMG_HEIGHT = 96
ALT_IMG_WIDTH = 96

# Batch size
BATCH_SIZE = 256


# COde for standardizing the image
def std(img):

    # Standardize pixel values to mean=0, std=1
    mean = np.mean(img, axis=(0, 1, 2), keepdims=True)  # Compute mean across all channels
    std = np.std(img, axis=(0, 1, 2), keepdims=True)    # Compute std across all channels

    std_img = (img - mean) / (std + 1e-7)                  # Subtract mean and divide by std

    return std_img

# Custom function to crop the image from the center region, then standardize
def crop_center_resize_std(img):
    height, width = img.shape[0], img.shape[1]
    startx = (width // 2) - (IMG_WIDTH//2)
    starty = (height // 2) - (IMG_HEIGHT//2)

    crp_img = img[starty:starty+IMG_HEIGHT, startx:startx+IMG_WIDTH, :]

    # Standardize pixel values to mean=0, std=1
    mean = np.mean(crp_img, axis=(0, 1, 2), keepdims=True)  # Compute mean across all channels
    std = np.std(crp_img, axis=(0, 1, 2), keepdims=True)    # Compute std across all channels

    std_img = (crp_img - mean) / (std + 1e-7)                  # Subtract mean and divide by std

    return std_img

# Custom function to resize the image, crop from the center and standardize
def resize_crop_center_std(img):

    resize_img = tf.image.resize(img, (RSZ_IMG_WIDTH, RSZ_IMG_HEIGHT))
    height, width = resize_img.shape[0], resize_img.shape[1]

    startx = (width // 2) - (ALT_IMG_WIDTH//2)
    starty = (height // 2) - (ALT_IMG_HEIGHT//2)

    crp_img = resize_img[starty:starty+ALT_IMG_HEIGHT, startx:startx+ALT_IMG_WIDTH, :]

    # Standardize pixel values to mean=0, std=1
    mean = np.mean(crp_img, axis=(0, 1, 2), keepdims=True)  # Compute mean across all channels
    std = np.std(crp_img, axis=(0, 1, 2), keepdims=True)    # Compute std across all channels

    std_img = (crp_img - mean) / (std + 1e-7)                  # Subtract mean and divide by std

    return std_img


# Creating Data Generators for CNN
train_datagen = ImageDataGenerator(
    rescale=1/255,
    # preprocessing_function=crop_center_resize_std,
    # preprocessing_function=resize_crop_center_std,
    preprocessing_function=std,
    rotation_range=40,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

valid_datagen = ImageDataGenerator(
    rescale=1/255,
    # preprocessing_function=crop_center_resize_std
    # preprocessing_function=resize_crop_center_std
    preprocessing_function=std)

test_datagen = ImageDataGenerator(
    rescale=1/255,
    # preprocessing_function=crop_center_resize_std,
    preprocessing_function=resize_crop_center_std)
    # preprocessing_function=std)

model_train_generator = train_datagen.flow_from_dataframe(
    dataframe=model_train_df,
    directory=train_path_dir,
    x_col='id',
    y_col='label',
    target_size=(DFLT_IMG_WIDTH, DFLT_IMG_HEIGHT),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=True
)

model_validation_generator = valid_datagen.flow_from_dataframe(
    dataframe=model_valid_df,
    directory=train_path_dir,
    x_col='id',
    y_col='label',
    target_size=(DFLT_IMG_WIDTH, DFLT_IMG_HEIGHT),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False
)

test_generator = test_datagen.flow_from_dataframe(
    dataframe=test_data_df,
    directory = test_path_dir,
    x_col='id',
    y_col='label',
    target_size=(ALT_IMG_WIDTH, ALT_IMG_HEIGHT),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False
)


# Optimize the data pipeline if using custom generator
model_train_dataset = tf.data.Dataset.from_generator(
    lambda: model_train_generator,
    output_signature=(
        tf.TensorSpec(shape=(None, DFLT_IMG_WIDTH, DFLT_IMG_HEIGHT, 3), dtype=tf.float32),
        tf.TensorSpec(shape=(None, 2), dtype=tf.float32)  # Adjust for your label shape
    )
).cache().prefetch(tf.data.experimental.AUTOTUNE)

model_validation_dataset = tf.data.Dataset.from_generator(
    lambda: model_validation_generator,
    output_signature=(
        tf.TensorSpec(shape=(None, DFLT_IMG_WIDTH, DFLT_IMG_HEIGHT, 3), dtype=tf.float32),
        tf.TensorSpec(shape=(None, 2), dtype=tf.float32)  # Adjust for your label shape
    )
).cache().prefetch(tf.data.experimental.AUTOTUNE)

model_test_dataset = tf.data.Dataset.from_generator(
    lambda: test_generator,
    output_signature=(
        tf.TensorSpec(shape=(None, DFLT_IMG_WIDTH, DFLT_IMG_HEIGHT, 3), dtype=tf.float32),
        tf.TensorSpec(shape=(None, 2), dtype=tf.float32)  # Adjust for your label shape
    )
).cache().prefetch(tf.data.experimental.AUTOTUNE)


TR_STEPS = len(model_train_generator)
VA_STEPS = len(model_validation_generator)


print('Number of batches in the training set:',TR_STEPS)
print('Number of batches in the validation set:',VA_STEPS)

import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow import keras
from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, TensorBoard, Callback, EarlyStopping
from tensorflow.keras.layers import *
from tensorflow.keras import layers,optimizers,models
from keras.metrics import AUC
import psutil
import subprocess
from datetime import datetime

from keras_tuner.tuners import RandomSearch
from keras_tuner.engine.hyperparameters import HyperParameters

import gc
gc.disable()  # Disable garbage collection

# from tensorflow.keras.mixed_precision import set_global_policy
# set_global_policy('mixed_float16')
# tf.debugging.set_log_device_placement(True)  # Log device placement
# tf.debugging.enable_check_numerics()  # Check for NaNs or Infs

# Check if CPU is available
cpu_devices = tf.config.list_physical_devices('CPU')
if cpu_devices:
    print("CPU is available")
else:
    print("CPU is not available")

# Check if GPU is available
gpu_devices = tf.config.list_physical_devices('GPU')
if gpu_devices:
    print("GPU is available")
    for gpu in gpu_devices:
        print(f"GPU device: {gpu}")
else:
    print("GPU is not available")

print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))

# Performing hyperparameter search

def build_model(hp):
    model = keras.Sequential()

    # Hyperparameter: Number of filters in the first Conv2D layer
    hp_filters_1 = hp.Int('filters_input', min_value=32, max_value=512, step=32)
    model.add(layers.Conv2D(filters=hp_filters_1, kernel_size=(3, 3), activation='relu', input_shape=(IMG_WIDTH, IMG_HEIGHT, 3), padding='same'))
    model.add(layers.Conv2D(filters=hp_filters_1, kernel_size=(3, 3), activation='relu', padding='same'))
    model.add(layers.BatchNormalization())
    model.add(layers.MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))

    # Hyperparameter: Number of Conv2D layers
    for i in range(hp.Int('num_conv_layers', 1, 6)):
        hp_filters_2 = hp.Int(f'filters_inner_{i}', min_value=32, max_value=512, step=32)
        model.add(layers.Conv2D(filters=hp_filters_2, kernel_size=(3, 3), activation='relu', padding='same'))
        model.add(layers.Conv2D(filters=hp_filters_2, kernel_size=(3, 3), activation='relu', padding='same'))
        model.add(layers.BatchNormalization())
        model.add(layers.MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))

    model.add(layers.Flatten())

    hp_dropout = hp.Choice('drop_out', values=[0.2, 0.3, 0.4, 0.5])
    # Hyperparameter: Number of Dense layers and units in dense layers
    for i in range(hp.Int('num_dense_layers', 1, 6)):
        model.add(layers.Dense(units=hp.Int(f'dense_units_{i}', min_value=4, max_value=256, step=32), activation='relu'))
        model.add(layers.Dropout(rate=hp_dropout))

    # Output layer
    model.add(layers.BatchNormalization())
    model.add(layers.Dense(2, activation='softmax'))  # Adjust for your task

    # Hyperparameter: Learning rate
    hp_learning_rate = hp.Choice('learning_rate', values=[1e-2, 1e-3, 1e-4, 1e-5])

    # Compile the model
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=hp_learning_rate),
        loss='categorical_crossentropy',  # Adjust for your task
        metrics=['accuracy', tf.keras.metrics.AUC()]
    )

    return model

tuner = RandomSearch(
    build_model,
    objective='val_loss',  # Metric to optimize
    max_trials=40,             # Number of hyperparameter combinations to try
    executions_per_trial=1,    # Number of models to train per trial (for robustness)
    directory='histopathologic-cancer-detection/my_tuner_dir',  # Directory to save results
    project_name='cnn_tuning'  # Project name
)

tuner.search(
    model_train_generator,
    epochs=1,
    validation_data=model_validation_generator
)

# Get the best model
best_hp_model = tuner.get_best_models(num_models=1)[0]

# Print the summary
best_hp_model.summary()

# Get the best hyperparameters
best_hps = tuner.get_best_hyperparameters(num_trials=1)[0]

# Print the best hyperparameters
print(f"""
Best hyperparameters:
- Filters_input_layer: {best_hps.get('filters_input')}
- Number of Conv Layers: {best_hps.get('num_conv_layers')}
- Filters_inner_layer_0: {best_hps.get('filters_inner_0')}
- Filters_inner_layer_1: {best_hps.get('filters_inner_1')}
- Dense Layers: {best_hps.get('num_dense_layers')}
- Dense_units_layer_0: {best_hps.get('dense_units_0')}
- Dense_units_layer_1: {best_hps.get('dense_units_1')}
- Dense_units_layer_2: {best_hps.get('dense_units_2')}
- Dense_units_layer_3: {best_hps.get('dense_units_3')}
- Learning Rate: {best_hps.get('learning_rate')}
- Dropout_rate: {best_hps.get('drop_out')}
""")

# Constructing base model after determining the hyperparameters to begin with

def CNN(model):

    model.add(layers.Conv2D(256, (3,3), activation='relu', input_shape=(IMG_WIDTH, IMG_HEIGHT,3), padding='same'))
    model.add(layers.Conv2D(256, (3,3), activation='relu', padding='same'))
    model.add(layers.BatchNormalization())
    model.add(layers.MaxPool2D(pool_size=(2,2), strides=(2,2)))

    model.add(layers.Conv2D(256, (3,3), activation='relu', padding='same'))
    model.add(layers.Conv2D(256, (3,3), activation='relu', padding='same'))
    model.add(layers.BatchNormalization())
    model.add(layers.MaxPool2D(pool_size=(2,2), strides=(2,2)))


    model.add(layers.Conv2D(64, (3,3), activation='relu', padding='same'))
    model.add(layers.Conv2D(64, (3,3), activation='relu', padding='same'))
    model.add(layers.BatchNormalization())
    model.add(layers.MaxPool2D(pool_size=(2,2), strides=(2,2)))

    # Convert to 1D vector
    model.add(layers.Flatten())

    # Classification layers
    model.add(layers.Dense(256, activation='relu'))
    model.add(layers.Dropout(0.5))
    model.add(layers.Dense(128, activation='relu'))
    model.add(layers.Dropout(0.5))
    model.add(layers.Dense(128, activation='relu'))
    model.add(layers.Dropout(0.5))
    model.add(layers.Dense(4, activation='relu'))
    model.add(layers.Dropout(0.5))
    model.add(layers.BatchNormalization())
    model.add(layers.Dense(2, activation='softmax'))

    return model

cnn_model = CNN(tf.keras.Sequential())

# Adjusting Learning rate parameter to the best hyperparameters
opt = tf.keras.optimizers.Adam(0.001)
cnn_model.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy', tf.keras.metrics.AUC()])
cnn_model.summary()

# Callback helper functions that helps in monitoring and optimizing the training process

# Define the checkpoint callback
checkpoint_path = "histopathologic-cancer-detection/models/model_checkpoint_epoch_{epoch:02d}.h5"

# Define the checkpoint callback
checkpoint_epoch_save = ModelCheckpoint(
    checkpoint_path,
    save_freq='epoch',
    save_weights_only=False,
    verbose=1
)

checkpoint_learning_rate = ReduceLROnPlateau(
            monitor='val_loss',
            mode='min',          # Reduce LR when val_loss stops decreasing
            factor=0.1,  # Reduce learning rate by a factor of 10
            patience=3,  # Wait for 3 epochs without improvement
            min_lr=1e-5, # Minimum learning rate
            verbose=1
)

early_stopping = EarlyStopping(
    monitor='val_loss',  # Monitor validation loss
    mode='min',          # Stop training when val_loss stops decreasing
    patience=3,          # Stop after 5 epochs without improvement
    min_delta=0.001,     # Minimum change to qualify as improvement
    restore_best_weights=False  # Restore the best model weights
)

# Create a log directory for TensorBoard
log = "histopathologic-cancer-detection/logs/profile/" + datetime.now().strftime("%Y%m%d-%H%M%S")
tensorboard_callback = TensorBoard(log_dir=log, profile_batch='10,20')


class ResourceUsageCallback(Callback):
    def on_epoch_end(self, epoch, logs=None):
        # Log GPU usage
        result = subprocess.run(['rocm-smi'], stdout=subprocess.PIPE)
        print("GPU Usage:")
        print(result.stdout.decode('utf-8'))

        # Log CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        print(f"CPU Usage: {cpu_percent}%")
        print(f"Memory Usage: {memory_info.percent}%")

# Add the callback to model.fit
resource_callback = ResourceUsageCallback()


# Flag to track profiler state
profiler_running = False

def start_profiler(logdir):
    global profiler_running
    tf.profiler.experimental.start(logdir)
    profiler_running = True
    print("Profiler started.")

def stop_profiler():
    global profiler_running
    if profiler_running:
        tf.profiler.experimental.stop()
        profiler_running = False
        print("Profiler stopped.")
    else:
        print("Profiler is not running.")

# Commented out IPython magic to ensure Python compatibility.
# # Training the neural network
# 
# %%time
# # stop_profiler()
# # KBackend.clear_session()
# # Start the profiler
# # start_profiler('histopathologic-cancer-detection/logdir')
# 
# cnn_history = cnn_model.fit(
#     x = model_train_generator,
#     steps_per_epoch = TR_STEPS,
#     epochs = 10,
#     validation_data = model_validation_generator,
#     validation_steps = VA_STEPS,
#     verbose = 1,
#     callbacks=[checkpoint_epoch_save, checkpoint_learning_rate, early_stopping]
# )
# 
# # Check and stop the profiler
# # stop_profiler()
# 
# # Clear the session
# # KBackend.clear_session()

# Saving the models and history

import pickle

# Save the model
base_cnn_model.save('histopathologic-cancer-detection/train_models/March_14th_Model_final_epoch_run.h5')

# Save the history
with open('histopathologic-cancer-detection/train_models/March_14th_Model_final_epoch_run.pkl', 'wb') as file:
    pickle.dump(base_cnn_history, file)

# Finetuning the model

# KBackend.set_value(cnn_model.optimizer.learning_rate, 0.00001)
# Load the model from a specific epoch

base_cnn_model_ft = load_model("histopathologic-cancer-detection/models/Models_Training_March_14th/model_checkpoint_epoch_03.h5")
opt = tf.keras.optimizers.Adam(0.00001)

base_cnn_model_ft.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy', tf.keras.metrics.AUC()])

base_cnn_history_ft = base_cnn_model_ft.fit(
    x = model_train_generator,
    steps_per_epoch = TR_STEPS,
    epochs = 10,
    validation_data = model_validation_generator,
    validation_steps = VA_STEPS,
    verbose = 1,
    callbacks=[checkpoint_epoch_save]
)

# Save the model
base_cnn_model_ft.save('histopathologic-cancer-detection/train_models/March_14th_Model_ft.h5')

# Save the history
with open('histopathologic-cancer-detection/train_models/March_14th_Model_ft.pkl', 'wb') as file:
    pickle.dump(base_cnn_history_ft, file)

# Custom functions for visualizing the training and test metrics

def merge_history(hlist):
    history = {}
    for k in hlist[0].history.keys():
        history[k] = sum([h.history[k] for h in hlist], [])
    return history

def vis_training(h, start=1):
    epoch_range = range(start, len(h['loss'])+1)
    s = slice(start-1, None)

    plt.figure(figsize=[14,4])

    n = int(len(h.keys()) / 2)

    for i in range(n):
        k = list(h.keys())[i]
        plt.subplot(1,n,i+1)
        plt.plot(epoch_range, h[k][s], label='Training')
        plt.plot(epoch_range, h['val_' + k][s], label='Validation')
        plt.xlabel('Epoch'); plt.ylabel(k); plt.title(k)
        plt.grid()
        plt.legend()

    plt.tight_layout()
    plt.show()

history = merge_history([base_cnn_history])
vis_training(history)

# Finetuned Training Run (Total 16 epochs)

base_cnn_history_ft.history['auc'] = base_cnn_history_ft.history['auc']
base_cnn_history_ft.history['val_auc'] = base_cnn_history_ft.history['val_auc']
base_cnn_history_ft.history['lr'] = [0.00001] * len(base_cnn_history_ft.history['loss'])

history_1 = merge_history([base_cnn_history, base_cnn_history_ft])
vis_training(history_1, start=1)

# Preparing the submission file for Kaggle

import pickle
from tensorflow.keras.models import load_model

cnn_model_best = load_model("histopathologic-cancer-detection/models/Models_Training_March_18th/model_checkpoint_epoch_07.h5")
cnn_model_best.save('histopathologic-cancer-detection/best_models/best_model.h5')

#Predicting Test Dataset
test_preds = cnn_model_best.predict(test_generator)

# Convert probabilities to predicted class labels
predicted_labels = np.argmax(test_preds, axis=1)

submission_df = pd.read_csv('histopathologic-cancer-detection/sample_submission.csv')

# Create the submission DataFrame using filenames from test_df
submission = pd.DataFrame({'id': submission_df['id'], 'label': predicted_labels})

# Save the DataFrame to a CSV file for submission
submission.to_csv('histopathologic-cancer-detection/submission_files/final_submission_march_21th.csv', index=False)

submission.head()

# Plotting the test labels category distribution

# Calculate frequency distribution
frequency_distribution = (submission.label.value_counts() / len(submission)).to_frame()

# Plotting the frequency distribution as a bar chart
plt.figure(figsize=(6, 4))
colors = ['lightgreen', 'lightcoral']  # light green for benign, light red for malignant

# Plotting bar chart with specified colors
frequency_distribution.iloc[:, 0].plot(kind='bar', color=colors)

# Customizing chart
plt.title('Frequency Distribution of Labels')
plt.xlabel('Label')
plt.ylabel('Frequency')
plt.xticks([0, 1], ['Benign', 'Malignant'], rotation=0)

# Show the plot
plt.show()