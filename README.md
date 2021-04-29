<!--
{% comment %}
Licensed to the Apache Software Foundation (ASF) under one or more
contributor license agreements.  See the NOTICE file distributed with
this work for additional information regarding copyright ownership.
The ASF licenses this file to you under the Apache License, Version 2.0
(the "License"); you may not use this file except in compliance with
the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
{% endcomment %}
-->

# Fork from "Predicting Breast Cancer Proliferation Scores with TensorFlow, Keras, and Apache Spark"

This fork will deal mostly with WSI preprocessing tasks by optimizing and generalizing CODAIT code.

## Setup (*All nodes* unless other specified):
* System Packages:
  * `openslide`
* Python packages:
  * Basics
    * `pip3 install -U matplotlib numpy pandas scipy jupyter ipython scikit-learn scikit-image openslide-python`
  * TensorFlow (only on driver):
    * `pip3 install tensorflow-gpu` (or `pip3 install tensorflow` for CPU-only)
  * Keras (bleeding-edge; only on driver):
    * `pip3 install git+https://github.com/fchollet/keras.git`

* Add the following to the `data` folder (same location on *all* nodes):
  * `training_image_data` folder with the training slides.
  * `testing_image_data` folder with the testing slides.
  * `training_ground_truth.csv` file containing the tumor & molecular scores for each slide.
  * `mitoses` folder with the following from the mitosis detection auxiliary dataset:
    * `mitoses_test_image_data` folder with the folders of testing images
    * `mitoses_train_image_data` folder with the folders of training images
    * `mitoses_train_ground_truth` folder with the folders of training csv files
* Layout:
  ```
  - MachineLearning-Keras-ResNet50.ipynb
  - breastcancer/
    - preprocessing.py
    - visualization.py
  - ...
  - data/
    - mitoses
      - mitoses_test_image_data
        - 01
          - 01.tif
        - 02
          - 01.tif
        ...
      - mitoses_train_ground_truth
        - 01
          - 01.csv
          - 02.csv
          ...
        - 02
          - 01.csv
          - 02.csv
          ...
        ...
      - mitoses_train_image_data
        - 01
          - 01.tif
          - 02.tif
          ...
        - 02
          - 01.tif
          - 02.tif
          ...
        ...
    - training_ground_truth.csv
    - training_image_data
      - TUPAC-TR-001.svs
      - TUPAC-TR-002.svs
      - ...
    - testing_image_data
      - TUPAC-TE-001.svs
      - TUPAC-TE-002.svs
      - ...
  - preprocess.py
  - preprocess_mitoses.py
  - train_mitoses.py
  ```

  * Preprocessing (preprocess.py):
    ```
    # Save 1/2 executor memory for Python processes
    spark.executor.memory 50g
    ```
    
## Create a Histopath slide “lab” to view the slides (just driver):
  - `git clone https://github.com/openslide/openslide-python.git`
  - Host locally:
    - `python3 path/to/openslide-python/examples/deepzoom/deepzoom_multiserver.py -Q 100 path/to/data/`
  - Host on server:
    - `python3 path/to/openslide-python/examples/deepzoom/deepzoom_multiserver.py -Q 100 -l HOSTING_URL_HERE path/to/data/`
    - Open local browser to `HOSTING_URL_HERE:5000`.
