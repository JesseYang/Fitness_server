from easydict import EasyDict as edict

cfg = edict()


# general config
cfg.max_queue_len = 10000

# for capture
cfg.cam_idx = 0
cfg.capture_frame_num = -1
cfg.fps = 10 # choose from 30, 15, 10, 7.5, 6, 5

# for detect
cfg.model_path = "model_files/mobilenetv2_pose_estimation"

# for visualize
cfg.std_data_dir = "std_data"

cfg.batch_size = 8

cfg.output_height = 640
cfg.output_width = 480
# cfg.output_height = 480
# cfg.output_width = 800


cfg.show_img_h = 250
cfg.show_img_w = 400

cfg.min_qsize = 10

# for action
cfg.max_buffer_len = 300

cfg.part_num = 18
cfg.part_colors = [[255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0], [170, 255, 0], [85, 255, 0], [0, 255, 0], \
                  [0, 255, 85], [0, 255, 170], [0, 255, 255], [0, 170, 255], [0, 85, 255], [0, 0, 255], [85, 0, 255], \
                  [170, 0, 255], [255, 0, 255], [255, 0, 170], [255, 0, 85]]
