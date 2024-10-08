# # Copyright (c) OpenMMLab. All rights reserved.
# from typing import Dict, List

# import torch
# from torch import Tensor
# from torch import nn as nn

# from mmdet3d.registry import MODELS
# from mmdet3d.structures.det3d_data_sample import SampleList
# from .decode_head import Base3DDecodeHead
# from mmdet3d.utils.typing_utils import ConfigType


# @MODELS.register_module()
# class MinkUNetHead(Base3DDecodeHead):
#     r"""MinkUNet decoder head with TorchSparse backend.

#     Refer to `implementation code <https://github.com/mit-han-lab/spvnas>`_.

#     Args:
#         batch_first (bool): Whether to put the batch dimension to the first
#             dimension when getting voxel coordinates. Defaults to True.
#     """

#     def __init__(self, batch_first: bool = True, **kwargs) -> None:
#         super(MinkUNetHead, self).__init__(**kwargs)
#         self.batch_first = batch_first
        
#     def build_conv_seg(self, channels: int, num_classes: int,
#                        kernel_size: int) -> nn.Module:
#         """Build Convolutional Segmentation Layers."""
#         return nn.Linear(channels, num_classes)

#     def forward(self, voxel_dict: dict) -> dict:
#         """Forward function."""
#         logits = self.cls_seg(voxel_dict['voxel_feats'])
#         voxel_dict['logits'] = logits
#         return voxel_dict

#     def loss(self, inputs: dict, batch_data_samples: SampleList,
#             train_cfg: ConfigType,
#             projected_points=False) -> Dict[str, Tensor]:
#         """Forward function for training.

#         Args:
#             inputs (dict): Feature dict from backbone.
#             batch_data_samples (List[:obj:`Det3DDataSample`]): The seg data
#                 samples. It usually includes information such as `metainfo` and
#                 `gt_pts_seg`.
#             train_cfg (dict or :obj:`ConfigDict`): The training config.

#         Returns:
#             Dict[str, Tensor]: A dictionary of loss components.
#         """
#         seg_logits = self.forward(inputs)
#         losses = self.loss_by_feat(seg_logits, batch_data_samples, projected_points=projected_points)
#         return losses
    
#     def loss_by_feat(self, voxel_dict: dict,
#                      batch_data_samples: SampleList,
#                      projected_points=False) -> Dict[str, Tensor]:
#         """Compute semantic segmentation loss.

#         Args:
#             voxel_dict (dict): The dict may contain `logits`,
#                 `point2voxel_map`.
#             batch_data_samples (List[:obj:`Det3DDataSample`]): The seg data
#                 samples. It usually includes information such as `metainfo` and
#                 `gt_pts_seg`.

#         Returns:
#             Dict[str, Tensor]: A dictionary of loss components.
#         """
#         voxel_semantic_segs = []
#         voxel_inds = voxel_dict['voxel_inds']
#         for batch_idx, data_sample in enumerate(batch_data_samples):
#             pts_semantic_mask = data_sample.gt_pts_seg.pts_semantic_mask_pjt if projected_points is True \
#                 else data_sample.gt_pts_seg.pts_semantic_mask
#             voxel_semantic_mask = pts_semantic_mask[voxel_inds[batch_idx]]
#             voxel_semantic_segs.append(voxel_semantic_mask)
#         seg_label = torch.cat(voxel_semantic_segs)
#         seg_logit_feat = voxel_dict['logits']
#         loss = dict()
#         loss['loss_ce'] = self.loss_decode(seg_logit_feat, seg_label, ignore_index=self.ignore_index) ## loss['loss_ce_pjt']
#         return loss

#     def predict(self, voxel_dict: dict,
#                 batch_data_samples: SampleList) -> List[Tensor]:
#         """Forward function for testing.

#         Args:
#             voxel_dict (dict): Features from backbone.
#             batch_data_samples (List[:obj:`Det3DDataSample`]): The det3d data
#                 samples. It usually includes information such as `metainfo` and
#                 `gt_pts_seg`. We use `point2voxel_map` in this function.

#         Returns:
#             List[Tensor]: The segmentation prediction mask of each batch.
#         """
#         voxel_dict = self.forward(voxel_dict)
#         seg_pred_list = self.predict_by_feat(voxel_dict, batch_data_samples)
#         return seg_pred_list

#     def predict_by_feat(self, voxel_dict: dict,
#                         batch_data_samples: SampleList) -> List[Tensor]:
#         """Predict function.

#         Args:
#             voxel_dict (dict): The dict may contain `logits`,
#                 `point2voxel_map`.
#             batch_data_samples (List[:obj:`Det3DDataSample`]): The det3d data
#                 samples. It usually includes information such as `metainfo` and
#                 `gt_pts_seg`.

#         Returns:
#             List[Tensor]: List of point-wise segmentation logits.
#         """
#         seg_logits = voxel_dict['logits']

#         seg_pred_list = []
#         coors = voxel_dict['coors']
#         for batch_idx in range(len(batch_data_samples)):
#             if self.batch_first:
#                 batch_mask = coors[:, 0] == batch_idx
#             else:
#                 batch_mask = coors[:, -1] == batch_idx
#             seg_logits_sample = seg_logits[batch_mask]
#             point2voxel_map = voxel_dict['point2voxel_maps'][batch_idx].long()
#             point_seg_predicts = seg_logits_sample[point2voxel_map] ## return voxel -> point
#             seg_pred_list.append(point_seg_predicts)

#         return seg_pred_list

#     # ## newly added
#     # def loss_pjt(self, inputs: dict, batch_data_samples: SampleList) -> Dict[str, Tensor]:
#     #     """Forward function for training.

#     #     Args:
#     #         inputs (dict): Feature dict from backbone.
#     #         batch_data_samples (List[:obj:`Det3DDataSample`]): The seg data
#     #             samples. It usually includes information such as `metainfo` and
#     #             `gt_pts_seg`.
#     #         train_cfg (dict or :obj:`ConfigDict`): The training config.

#     #     Returns:
#     #         Dict[str, Tensor]: A dictionary of loss components.
#     #     """
#     #     seg_logits = self.forward(inputs)
#     #     losses = self.loss_by_feat_pjt(seg_logits, batch_data_samples)
#     #     return losses
    
#     # def loss_by_feat_pjt(self, voxel_dict: dict,
#     #                  batch_data_samples: SampleList) -> Dict[str, Tensor]:
#     #     """Compute semantic segmentation loss.

#     #     Args:
#     #         voxel_dict (dict): The dict may contain `logits`,
#     #             `point2voxel_map`.
#     #         batch_data_samples (List[:obj:`Det3DDataSample`]): The seg data
#     #             samples. It usually includes information such as `metainfo` and
#     #             `gt_pts_seg`.

#     #     Returns:
#     #         Dict[str, Tensor]: A dictionary of loss components.
#     #     """
#     #     voxel_semantic_segs = []
#     #     voxel_inds = voxel_dict['voxel_inds']
#     #     for batch_idx, data_sample in enumerate(batch_data_samples):
#     #         pts_semantic_mask = data_sample.gt_pts_seg.pts_semantic_mask_pjt
#     #         voxel_semantic_mask = pts_semantic_mask[voxel_inds[batch_idx]] ## to voxel
#     #         voxel_semantic_segs.append(voxel_semantic_mask)
#     #     seg_label = torch.cat(voxel_semantic_segs)
#     #     seg_logit_feat = voxel_dict['logits']
#     #     loss = dict()
#     #     loss['loss_ce_pjt'] = self.loss_decode(
#     #         seg_logit_feat, seg_label, ignore_index=self.ignore_index)
#     #     return loss
    
#     # ## newly added
#     # def loss_adv(self, inputs: dict, batch_data_samples: SampleList) -> Dict[str, Tensor]:
#     #     """Forward function for training.

#     #     Args:
#     #         inputs (dict): Feature dict from backbone.
#     #         batch_data_samples (List[:obj:`Det3DDataSample`]): The seg data
#     #             samples. It usually includes information such as `metainfo` and
#     #             `gt_pts_seg`.
#     #         train_cfg (dict or :obj:`ConfigDict`): The training config.

#     #     Returns:
#     #         Dict[str, Tensor]: A dictionary of loss components.
#     #     """
#     #     seg_logits = self.forward(inputs)
#     #     losses = self.loss_by_feat_adv(seg_logits, batch_data_samples)
#     #     return losses
    
#     # def loss_by_feat_adv(self, voxel_dict: dict,
#     #                     batch_data_samples: SampleList) -> Dict[str, Tensor]:
#     #     """Compute semantic segmentation loss.

#     #     Args:
#     #         voxel_dict (dict): The dict may contain `logits`,
#     #             `point2voxel_map`.
#     #         batch_data_samples (List[:obj:`Det3DDataSample`]): The seg data
#     #             samples. It usually includes information such as `metainfo` and
#     #             `gt_pts_seg`.

#     #     Returns:
#     #         Dict[str, Tensor]: A dictionary of loss components.
#     #     """
#     #     voxel_semantic_segs = []
#     #     voxel_inds = voxel_dict['voxel_inds']
#     #     for batch_idx, data_sample in enumerate(batch_data_samples):
#     #         pts_semantic_mask = data_sample.gt_pts_seg.pts_semantic_mask
#     #         voxel_semantic_mask = pts_semantic_mask[voxel_inds[batch_idx]] ## to voxel
#     #         voxel_semantic_segs.append(voxel_semantic_mask)
#     #     seg_label = torch.cat(voxel_semantic_segs)
#     #     seg_logit_feat = voxel_dict['logits']
#     #     loss = dict()
#     #     loss['loss_adv_ce'] = self.loss_decode(
#     #         seg_logit_feat, seg_label, ignore_index=self.ignore_index)
#     #     return loss