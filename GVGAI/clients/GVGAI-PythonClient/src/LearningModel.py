import tensorflow as tf
import numpy as np

# Model used to choose next subgoal using Deep Q-Learning
# Given a pair (observation, subgoal) encoded as a one-hot observation matrix
# the model predicts the length of the plan that gets that subgoal and, then,
# completes the level

class DQNetwork:

	# Create CNN architecture
    def __init__(self, name="DQNetwork", writer_name="DQNetwork", create_writer = True,
                 l1_num_filt = 2, l1_window = [4,4], l1_strides = [2,2],
                 padding_type = "SAME",
                 max_pool_size = [2, 2],
                 max_pool_str = [1, 1],
                 fc_num_units = [16, 1], dropout_prob = 0.5,
                 l2_regularization=0.0,
                 learning_rate = 0.005):

        self.variable_scope = name

        with tf.variable_scope(self.variable_scope):

            # --- Constants, Variables and Placeholders ---


            # Batch of inputs (game states + goals, one-hot encoded)
            self.X = tf.placeholder(tf.float32, [None, 13, 26, 9], name="X") # type tf.float32 is needed for the rest of operations

            # Batch of outputs (correct predictions of number of actions)
            ## self.Y_corr = tf.placeholder(tf.float32, [None, 1], name="Y")

            # Q_target = R(s,a) + gamma * min Q(s', a') (s' next state after s, R(s,a) : plan length from state s to subgoal a)
            self.Q_target = tf.placeholder(tf.float32, [None, 1], name="Q_target")
            
            # Placeholder for batch normalization
            # During training (big batches) -> true, during test (small batches) -> false
            self.is_training = tf.placeholder(tf.bool, name="is_training")

            # Learning Rate
            self.alfa = tf.constant(learning_rate)

            # Dropout Probability (probability of deactivation)
            self.dropout_placeholder = tf.placeholder(tf.float32)
            self.dropout_prob = dropout_prob
            

            # --- Architecture ---


            """
            Batch Normalization of inputs
            """
            
            self.X_norm = tf.layers.batch_normalization(self.X, axis = 3, momentum=0.99, training=self.is_training)

            
            """
            First convnet:
            """
            
            # Padding = "VALID" -> no padding, "SAME" -> padding to keep the output dimension the same as the input one
            
            self.conv1 = tf.layers.conv2d(inputs = self.X_norm,
                                         filters = l1_num_filt,
                                         kernel_size = l1_window,
                                         strides = l1_strides,
                                         padding = padding_type,
                                         activation = tf.nn.relu,
                                         use_bias = True,
                                         kernel_initializer=tf.contrib.layers.xavier_initializer_conv2d(),
                                         name = "conv1")
                        
            # Max pooling
            
            self.conv1 = tf.layers.max_pooling2d(inputs = self.conv1,
                                                pool_size = max_pool_size,
                                                strides = max_pool_str,
                                                padding = "VALID"
                                                )
            
             
            """
            Second convnet:
            """
            
            """
            self.conv2 = tf.layers.conv2d(inputs = self.conv1,
                                         filters = l2_num_filt,
                                         kernel_size = l2_window,
                                         strides = l2_strides,
                                         padding = padding_type,
                                         activation = tf.nn.relu,
                                         use_bias = True,
                                         kernel_initializer=tf.contrib.layers.xavier_initializer_conv2d(),
                                         name = "conv2")
            
            # Max pooling
            
            self.conv2 = tf.layers.max_pooling2d(inputs = self.conv2,
                                                pool_size = max_pool_size,
                                                strides = max_pool_str,
                                                padding = "VALID"
                                                )
            """
            
            # Flatten output of conv layers
            
            self.flatten = tf.contrib.layers.flatten(self.conv1)
            
            # Fully connected layer 1

            self.fc_1 = tf.layers.dense(inputs = self.flatten,
                                  units = fc_num_units[0],
                                  activation = tf.nn.relu,
                                  kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                  kernel_regularizer=tf.contrib.layers.l2_regularizer(l2_regularization),
                                  name="fc_1")

            # Dropout 1
            
            self.fc_1 = tf.layers.dropout(self.fc_1, rate=self.dropout_placeholder, name="Dropout_1")

            # Fully connected layer 2
            
            self.fc_2 = tf.layers.dense(inputs = self.fc_1,
                                  units = fc_num_units[1],
                                  activation = tf.nn.relu,
                                  kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                  kernel_regularizer=tf.contrib.layers.l2_regularizer(l2_regularization),
                                  name="fc_2")
            
            # Dropout
            
            self.fc_2 = tf.layers.dropout(self.fc_2, rate=self.dropout_placeholder, name="Dropout_2")
            

            # Output Layer -> outputs the Q_value for the current (game state, subgoal) pair
            
            self.Q_val = tf.layers.dense(inputs = self.fc_2, 
                                          kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                          units = 1, 
                                          activation=None,
                                          name="Q_value")
            
            # Train
            
            # The loss is the difference between our predicted Q_values and the Q_targets
            # Sum(Qtarget - Q)^2
            self.loss = tf.reduce_mean(tf.square(self.Q_target - self.Q_val), name="loss")
            
            self.optimizer = tf.train.AdamOptimizer(learning_rate=self.alfa, name="optimizer")
            
            # Mean and Variance Shift Operations needed for Batch Normalization
            self.update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)

            # Execute mean and variance updates of batch norm each training step
            with tf.control_dependencies(self.update_ops):
                self.train_op = self.optimizer.minimize(self.loss, name="train_op")
            

            # --- Summaries ---

            if create_writer:
              self.train_loss_sum = tf.summary.scalar('train_loss', self.loss) # Training loss
              # self.test_loss_sum = tf.summary.scalar('test_loss', self.loss) # Validation loss
              
              self.writer = tf.summary.FileWriter("DQNetworkLogs/" + writer_name)
              self.writer.add_graph(tf.get_default_graph())
            

        # --- Initialization ---


        # Create Session

        # Run on GPU
        """
        # Needed for running on GPU
        gpu_options = tf.GPUOptions(allow_growth=True)
        self.sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))
        """

        # Run on CPU (it's faster if model and batch_size is small)
        self.sess = tf.Session(config=tf.ConfigProto(device_count = {'GPU': 0}))

        # Initialize variables
        self.sess.run(tf.global_variables_initializer())


    # Closes the current tensorflow session and frees the resources.
    # Should be called at the end of the program
    def close_session(self):
        self.sess.close()

    # Predicts the associated y-value (plan length) for x (a (subgoal, game state) pair one-hot encoded)
    # Dropout is not activated
    def predict(self, x):
        # Reshape x so that it has the shape of a one-element batch and can be fed into the placeholder
        x_resh = np.reshape(x, (1, 13, 26, 9))
        data_dict = {self.X : x_resh, self.is_training : False, self.dropout_placeholder : 0.0}

        prediction = self.sess.run(self.Q_val, feed_dict=data_dict)

        return prediction

    # Execute num_it training steps using X, Y (Q_targets) as the current batches. They must have the same number of elements
    # Dropout is activated
    def train(self, X, Y, num_it = 1):
        data_dict = {self.X : X, self.Q_target : Y, self.is_training : True, self.dropout_placeholder : self.dropout_prob}

        for it in range(num_it):
            self.sess.run(self.train_op, feed_dict=data_dict)

    # Calculate Training Loss and store it as a log
    # Dropout is not activated
    def save_logs(self, X, Y, it):
        # Training Loss
        data_dict_train = {self.X : X, self.Q_target : Y, self.is_training : True, self.dropout_placeholder : 0.0}

        train_loss_log = self.sess.run(self.train_loss_sum, feed_dict=data_dict_train)
        self.writer.add_summary(train_loss_log, it)

    # Saves the model variables in the file given by 'path', so that it can be loaded next time
    def save_model(self, path = "./SavedModels/DQmodel.ckpt", num_it = None):
        saver = tf.train.Saver(
          tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, self.variable_scope)) # Only save the variables within this variable scope
        
        if num_it is None:
          saver.save(self.sess, path)
        else:
          saver.save(self.sess, path, global_step = num_it)

    # Loads a model previously saved with 'save_model'
    def load_model(self, path = "./SavedModels/DQmodel.ckpt", num_it = None):
        saver = tf.train.Saver(
          tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, self.variable_scope)) # Only load the variables within this variable scope
        
        if num_it is None:
          saver.restore(self.sess, path)
        else:
          saver.restore(self.sess, path + '-' + str(num_it))

    # Runs update_ops to update the current weights. This method is used to update the target network's weights
    # every tau steps
    def update_weights(self, update_ops):
        self.sess.run(update_ops)