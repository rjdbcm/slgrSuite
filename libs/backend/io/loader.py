import tensorflow as tf
import os
from libs.backend.dark import darknet
import numpy as np
from os.path import basename
from libs.constants import WEIGHTS_FILE_KEYS, WGT_EXT


class Loader:
    __create_key = object()
    """
    interface to work with both .weights and .ckpt files
    in loading / recollecting / resolving mode
    """
    VAR_LAYER = ['convolutional', 'connected', 'local', 'select', 'conv-select',
                        'extract', 'conv-extract']

    def __init__(self, create_key, *args):
        msg = f"Loaders must be created using Loader.create"
        if not create_key == Loader.__create_key:
            raise NotImplementedError(msg)
        self.src_key = list()
        self.vals = list()
        self.constructor(*args)

    def __call__(self, key):
        for idx in range(len(key)):
            val = self.find(key, idx)
            if val is not None:
                return val
        return None
    
    def find(self, key, idx):
        up_to = min(len(self.src_key), 4)
        for i in range(up_to):
            key_b = self.src_key[i]
            if key_b[idx:] == key[idx:]:
                return self.yields(i)
        return None

    def yields(self, idx):
        del self.src_key[idx]
        temp = self.vals[idx]
        del self.vals[idx]
        return temp

    @classmethod
    def create(cls, path, cfg=None):
        if path is None:
            load_type = WeightsLoader
        elif WGT_EXT in path:
            load_type = WeightsLoader
        else:
            load_type = CheckpointLoader

        return load_type(cls.__create_key, path, cfg)

    @staticmethod
    def model_name(file_path):
        file_name = basename(file_path)
        ext = str()
        if '.' in file_name:  # exclude extension
            file_name = file_name.split('.')
            ext = file_name[-1]
            file_name = '.'.join(file_name[:-1])
        if ext == str() or ext == 'meta':  # ckpt file
            file_name = file_name.split('-')
            num = int(file_name[-1])
            return '-'.join(file_name[:-1])
        if ext == 'weights':
            return file_name

    def constructor(self, *args):
        pass


class WeightsLoader(Loader):
    """one who understands .weights files"""

    def constructor(self, path, src_layers):
        self.src_layers = src_layers
        walker = WeightsWalker(path)

        for i, layer in enumerate(src_layers):
            if layer.type not in self.VAR_LAYER:
                continue
            self.src_key.append([layer])
            
            if walker.eof:
                new = None
            else: 
                args = layer.signature
                new = darknet.create_darkop(*args)
            self.vals.append(new)

            if new is None:
                continue
            order = WEIGHTS_FILE_KEYS[new.type]
            for par in order:
                if par not in new.wshape:
                    continue
                val = walker.walk(new.wsize[par])
                new.w[par] = val
            new.finalize(walker.transpose)

        if walker.path is not None:
            assert walker.offset == walker.size, \
            'expect {} bytes, found {}'.format(
                walker.offset, walker.size)
            print('Successfully identified {} bytes'.format(
                walker.offset))


class CheckpointLoader(Loader):
    """
    one who understands .ckpt files, very much
    """
    def constructor(self, ckpt, ignore):
        meta = ckpt + '.meta'
        with tf.Graph().as_default() as graph:
            with tf.compat.v1.Session().as_default() as sess:
                saver = tf.compat.v1.train.import_meta_graph(meta)
                saver.restore(sess, ckpt)
                for var in tf.compat.v1.global_variables():
                    name = var.name.split(':')[0]
                    packet = [name, var.get_shape().as_list()]
                    self.src_key += [packet]
                    self.vals += [var.eval(sess)]


class WeightsWalker(object):
    """incremental reader of float32 binary files"""
    def __init__(self, path):
        self.eof = False  # end of file
        self.path = path  # current pos
        if path is None: 
            self.eof = True
            return
        else: 
            self.size = os.path.getsize(path)# save the path
            major, minor, revision, seen = np.memmap(path, shape=(), mode='r', offset=0, dtype='({})i4,'.format(4))
            self.transpose = major > 1000 or minor > 1000
            self.offset = 16

    def walk(self, size):
        if self.eof:
            return None
        end_point = self.offset + 4 * size
        assert end_point <= self.size, \
            'Over-read {}'.format(self.path)
        float32_1D_array = np.memmap(self.path, shape=(), mode='r', offset=self.offset,
                                     dtype='({})float32,'.format(size))

        self.offset = end_point
        if end_point == self.size: 
            self.eof = True
        return float32_1D_array


