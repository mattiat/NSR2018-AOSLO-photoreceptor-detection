# Copyright (C) Benjamin Davidson, Inc - All Rights Reserved
# Unauthorized copying of this file, without the authors written permission
# via any medium is strictly prohibited
# Proprietary and confidential
# Written by Benjamin Davidson <ben.davidson6@googlemail.com>, January 2018

import os

import numpy as np
import tensorflow as tf


from .data import Data
from .model import DICE_CONV_MD_32U2L_tanh
from .regional_max import get_centers
from . import constants


def run_through_nothing(data, outputs, size):
    for image_name in data.images_by_size[size]:
        output_dict = dict()
        # get image, crop, center, make tensor
        raw_image = data.grayscale_image(image_name)
        cropped = Data.crop_center(raw_image, size)

        # save the name, largest central crop, and the centres as a list
        output_dict['name'] = image_name
        output_dict['cropped'] = cropped
        output_dict['centres'] = []
    outputs.append(output_dict)
    return outputs

def run_through_graph(data, mname, size, brightDark, outputs):

    # get modules location so we can load the tensorflow model
    # parameters
    model_location = os.path.join(constants.MODEL_DIREC, mname, 'model')
    model = DICE_CONV_MD_32U2L_tanh

    # construct graph and apply to images
    with tf.Graph().as_default():
        with tf.Session() as sess:
            # build graph and restore, not we build it implicitly
            # using the size, due to the placeholder
            feed_dict = dict()
            image_place = tf.placeholder(dtype=tf.float32, shape=[1, size, size, 1])
            image, out, prob_of_cone = model(image_place, brightDark)
            saver = tf.train.Saver()
            saver.restore(sess, model_location)

            # process all images where maximum sized cropped is size
            for image_name in data.images_by_size[size]:
                output_dict = dict()

                # get image, crop, center, make tensor
                raw_image = data.grayscale_image(image_name)
                cropped = Data.crop_center(raw_image, size)
                centred = cropped - np.mean(cropped)

                # put through graph
                feed_dict[image_place] = centred[None, :, :, None]
                im, prob_map = sess.run([image, prob_of_cone], feed_dict=feed_dict)
                prob_map = np.reshape(prob_map, [size, size])
                centres = get_centers(prob_map)

                # save the name, largest central crop, and the centres as a list
                output_dict['name'] = image_name
                output_dict['cropped'] = cropped
                output_dict['centres'] = centres
                outputs.append(output_dict)
    return outputs

def locate_cones_with_model(dataFolder, brightDark, mname):

    # load the data and prepare output list
    data = Data(dataFolder)
    outputs = []

    # Process images which are grouped by size
    # reduces number of graphs to construct
    # todo make graph size independent
    for size in data.images_by_size.keys():
        if mname==constants.NO_MODEL:
            outputs = run_through_nothing(data, outputs, size)
            continue
        else:
            outputs = run_through_graph(data, mname, size, brightDark, outputs)

    return outputs
