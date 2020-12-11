import sys
import json


_FLAGS = {
        'annotation': ('./data/committedframes/',   str, 'Image Annotations Path'),
        'dataset': ('./data/committedframes/',      str, 'Images Path'),
        'backup': ('./data/ckpt/',                  str, 'Checkpoints Path'),
        'summary': ('./data/summaries/',            str, 'Tensorboard Summaries Path'),
        'config': ('./data/cfg/',                   str, 'Model Config Path'),
        'binary': ('./data/bin/',                   str, 'Binary Weights Path'),
        'built_graph': ('./data/built_graph/',      str, 'Protobuf Output Path'),
        'imgdir': ('./data/sample_img/',            str, 'Images to Predict Path'),
        'img_out': ('./data/img_out/',              str, 'Prediction Output Path'),
        'video_out': ('./data/video_out/',          str, 'Video Output Path'),
        'batch': (8,                                int, 'Images per Batch'),
        'cli': (False,                             bool, 'Using Command Line'),
        'clip': (False,                            bool, 'Clipping Gradients'),
        'clip_norm': (0.0,                        float, 'Gradient Clip Norm'),
        'clr_mode': ('triangular',                 str, 'Cyclic Learning Policy'),
        'done': (False,                            bool, 'Done Signal'),
        'epoch': (1,                                int, 'Epochs to Train'),
        'error': ('',                               str, 'Error Signal'),
        'video': ([],                              list, 'Videos to Annotate'),
        'gpu': (0.0,                              float, 'GPU Utilization'),
        'gpu_name': ('/gpu:0',                      str, 'Current GPU'),
        'output_type': ([],                        list, 'Predict Output Type'),
        'keep': (20,                                int, 'Checkpoint to Keep'),
        'kill': (False,                            bool, 'Kill Signal'),
        'labels': ('./data/predefined_classes.txt', str, 'Class Labels File'),
        'load': (-1,                                int, 'Checkpoint to Use'),
        'lr': (1e-05,                             float, 'Initial Learning Rate'),
        'max_lr': (1e-05,                         float, 'Maximum Learning Rate'),
        'model': ('./data/cfg/tiny-yolov2.cfg',     str, 'Model Configuration File'),
        'momentum': (0.0,                         float, 'Momentum Setting for Trainer'),
        'pid': (0,                                  int, 'Process Identifier'),
        'progress': (0.0,                         float, 'Progress Signal'),
        'project_name': ('default',                 str, 'Saving Under'),
        'quantify': (False,                        bool, 'Behavior Quantification Mode'),
        'save': (1,                                 int, 'Save Checkpoint After'),
        'size': (1,                                 int, 'Dataset Size (Images)'),
        'started': (False,                          int, 'Started Signal'),
        'step_size_coefficient': (2,                int, 'Cyclic Learning Coefficient'),
        'threshold': (0.4000,                     float, 'Detection Record Threshold'),
        'trainer': ('adam',                         str, 'Optimization Algorithm'),
        'verbalise': (False,                       bool, 'Verbose Output'),
        'train': (False,                           bool, 'Training Mode')
        }


DEFAULTS = {
   'FLAGS': {k: v[0] for k, v in _FLAGS.items()},
   'TYPES': {k: v[1] for k, v in _FLAGS.items()},
   'DESCS': {k: v[2] for k, v in _FLAGS.items()}
}

def get_defaults(k):
    data = DEFAULTS['FLAGS'].get(k)
    dtype = DEFAULTS['TYPES'].get(k)
    desc = DEFAULTS['DESCS'].get(k)
    return k, data, dtype, desc

def gen_defaults():
    for flag in _FLAGS:
        yield get_defaults(flag)

class Flags(dict):
    """
    Allows you to set and get {key: value} pairs like attributes.
    Compatible with argparse.Namespace objects.
    Enforces type-checking during flag setting.
    """

    def __init__(self, defaults=True):
        super(Flags, self).__init__()
        if defaults:
            self._get_defaults()

    def _get_defaults(self):
        for flag, value, *_ in gen_defaults():
            self.__setattr__(flag, value)

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        attr, _, dtype, _ = get_defaults(attr)
        try:
            if isinstance(value, dtype):
                self[attr] = value
            else:
                self[attr] = dtype(value)
        except TypeError:
            raise RuntimeError(f'Flags().{attr} is not supported.')


    def from_json(self, file):
        data = dict(json.load(file))
        for attr, value in data.items():
            self.__setattr__(attr, value)
        return self

    def to_json(self, file=sys.stdout):
        return json.dump(dict(self.items()), fp=file)
