"""Hyperparameter tuning - mitosis detection"""
import argparse
import json
import os
import random
import sys

import numpy as np
import tensorflow as tf

import train_mitoses


def main(args=None):
  # parse args
  parser = argparse.ArgumentParser()
  parser.add_argument("--patches_path", required=True,
      help="path to the generated image patches containing `train` & `val` folders ")
  parser.add_argument("--exp_parent_path",
      default=os.path.join("experiments", "mitoses", "hyp"),
      help="parent path in which to store experiment folders (default: %(default)s)")
  parser.add_argument("--models", nargs='*', default=["vgg", "resnet"],
      help="list of names of models to use, where the names can be selected from ['logreg', "\
           "'vgg', 'vgg_new', 'vgg19', 'resnet', 'resnet_new', 'resnet_custom'] "\
           "(default: %(default)s)")
  parser.add_argument("--model_weights", default=None,
      help="optional hdf5 file containing the initial weights of the model. if not supplied, the "\
           "model will start with pretrained weights from imagenet. if this is set, the `models` "\
           "list must contain a single model that is compatible with these weights "\
           "(default: %(default)s)")
  parser.add_argument("--patch_size", type=int, default=64,
      help="integer length to which the square patches will be resized (default: %(default)s)")
  parser.add_argument("--train_batch_sizes", nargs='*', type=int, default=[32],
      help="list of training batch sizes (default: %(default)s)")
  parser.add_argument("--val_batch_size", type=int, default=32,
      help="validation batch size for all experiments (default: %(default)s)")
  parser.add_argument("--clf_epochs", type=int, default=5,
      help="number of epochs for which to train the new classifier layers (default: %(default)s)")
  parser.add_argument("--finetune_epochs", type=int, default=5,
      help="number of epochs for which to fine-tune the unfrozen layers (default: %(default)s)")
  parser.add_argument("--clf_lr_range", nargs=2, type=float, default=(1e-5, 1e-2),
      help="half-open interval for the learning rate for training the new classifier layers "\
           "(default: %(default)s)")
  parser.add_argument("--finetune_lr_range", nargs=2, type=float, default=(1e-7, 1e-2),
      help="half-open interval for the learning rate for fine-tuning the unfrozen layers "\
           "(default: %(default)s)")
  parser.add_argument("--finetune_momentum_range", nargs=2, type=float, default=(0.85, 0.95),
      help="half-open interval for the momentum rate for fine-tuning the unfrozen layers "\
           "(default: %(default)s)")
  parser.add_argument("--finetune_layers", nargs='*', type=int, default=[0, -1],
      help="list of the number of layers at the end of the pretrained portion of the model to "\
           "fine-tune (note: the new classifier layers will still be trained during fine-tuning "\
           "as well) (default: %(default)s)")
  parser.add_argument("--l2_range", nargs=2, type=float, default=[0, 1e-2],
      help="half-closed interval for the amount of l2 weight regularization (default: %(default)s)")
  parser.add_argument("--reg_biases", default=False, action="store_true",
      help="whether or not to regularize biases. (default: %(default)s)")
  parser.add_argument("--skip_reg_final", dest="reg_final", action="store_false",
      help="whether or not to skip regularization of the logits-producing layer "\
           "(default: %(default)s)")
  parser.set_defaults(reg_final=True)
  augment_parser = parser.add_mutually_exclusive_group(required=False)
  augment_parser.add_argument("--augment", dest="augment", action="store_true",
      help="apply random augmentation to the training images (default: True)")
  augment_parser.add_argument("--no_augment", dest="augment", action="store_false",
      help="do not apply random augmentation to the training images (default: False)")
  parser.set_defaults(augment=True)
  parser.add_argument("--marginalize", default=False, action="store_true",
      help="use noise marginalization when evaluating the validation set. if this is set, then "\
           "the validation batch_size must be divisible by 4, or equal to 1 for no augmentation "\
           "(default: %(default)s)")
  parser.add_argument("--oversample", default=False, action="store_true",
      help="oversample the minority mitosis class during training via class-aware sampling "\
           "(default: %(default)s)")
  parser.add_argument("--num_gpus", type=int, default=1,
      help="num_gpus: Integer number of GPUs to use for data parallelism. (default: %(default)s)")
  parser.add_argument("--threads", type=int, default=5,
      help="number of threads for dataset parallel processing; note: this will cause "\
           "non-reproducibility for values > 1 (default: %(default)s)")
  parser.add_argument("--prefetch_batches", type=int, default=100,
      help="number of batches to prefetch (default: %(default)s)")
  parser.add_argument("--log_interval", type=int, default=100,
      help="number of steps between logging during training (default: %(default)s)")
  parser.add_argument("--num_experiments", type=int, default=100,
      help="number of experiments to run (default: %(default)s)")

  args = parser.parse_args(args)

  # save args to a file in the experiment parent folder, appending if it exists
  if not os.path.exists(args.exp_parent_path):
    os.makedirs(args.exp_parent_path)
  with open(os.path.join(args.exp_parent_path, 'args.txt'), 'a') as f:
    json.dump(args.__dict__, f)
    print("", file=f)
    # can be read in later with
    #with open('args.txt', 'r') as f:
    #  args = json.load(f)

  # save command line invocation to txt file for ease of rerunning the exact hyperparam search
  with open(os.path.join(args.exp_parent_path, 'invoke.txt'), 'a') as f:
    f.write("python3 " + " ".join(sys.argv) + "\n")

  # hyperparameter search
  for i in range(args.num_experiments):
    # NOTE: as a quick POC, we will use the command-line interface of the training script
    # TODO: extract experiment setup code in the training script main function into a class so that
    # we can reuse it from here
    train_args = []
    train_args.append("--patches_path={args.patches_path}".format(args=args))

    train_args.append("--exp_parent_path={args.exp_parent_path}".format(args=args))

    model = random.choice(args.models)
    train_args.append("--model={model}".format(model=model))

    if args.model_weights:
      train_args.append("--model_weights={args.model_weights}".format(args=args))

    train_args.append("--patch_size={args.patch_size}".format(args=args))

    train_batch_size = random.choice(args.train_batch_sizes)
    train_args.append("--train_batch_size={train_batch_size}".format(train_batch_size=train_batch_size))

    train_args.append("--val_batch_size={args.val_batch_size}".format(args=args))

    train_args.append("--clf_epochs={args.clf_epochs}".format(args=args))

    train_args.append("--finetune_epochs={args.finetune_epochs}".format(args=args))

    clf_lr_lb, clf_lr_ub = args.clf_lr_range
    clf_lr = np.random.uniform(clf_lr_lb, clf_lr_ub)
    train_args.append("--clf_lr={clf_lr}".format(clf_lr=clf_lr))

    finetune_lr_lb, finetune_lr_ub = args.finetune_lr_range
    finetune_lr = np.random.uniform(finetune_lr_lb, finetune_lr_ub)
    train_args.append("--finetune_lr={finetune_lr}".format(finetune_lr=finetune_lr))

    finetune_momentum_lb, finetune_momentum_ub = args.finetune_momentum_range
    finetune_momentum = np.random.uniform(finetune_momentum_lb, finetune_momentum_ub)
    train_args.append("--finetune_momentum={finetune_momentum}".format(finetune_momentum=finetune_momentum))

    finetune_layers = random.choice(args.finetune_layers)
    train_args.append("--finetune_layers={finetune_layers}".format(finetune_layers=finetune_layers))

    l2_lb, l2_ub = args.l2_range
    l2 = np.random.uniform(l2_lb, l2_ub)
    train_args.append("--l2={l2}".format(l2=l2))

    if args.reg_biases:
      train_args.append("--reg_biases")

    if not args.reg_final:
      train_args.append("--skip_reg_final")

    if args.augment:
      train_args.append("--augment")
    else:
      train_args.append("--no_augment")

    if args.marginalize:
      train_args.append("--marginalize")

    if args.oversample:
      train_args.append("--oversample")

    train_args.append("--num_gpus={args.num_gpus}".format(args=args))

    train_args.append("--threads={args.threads}".format(args=args))

    train_args.append("--prefetch_batches={args.prefetch_batches}".format(args=args))

    train_args.append("--log_interval={args.log_interval}".format(args=args))

    # train!
    try:
      train_mitoses.main(train_args)
    except tf.errors.InvalidArgumentError as e:  # if values become nan or inf
      print(e)
      print("Experiment failed!")

    # it is necessary to completely reset everything in between experiments
    tf.reset_default_graph()
    tf.keras.backend.clear_session()


if __name__ == "__main__":
  main()

