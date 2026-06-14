"""自包含 COLMAP 模型读取器（二进制格式），无需 pycolmap。

仅依赖标准库 + numpy。解析 cameras.bin / images.bin / points3D.bin，
输出每张图像的内参 K、世界到相机外参 w2c，以及稀疏点云 xyz/rgb。
格式参考 COLMAP 官方 read_write_model.py（公有领域）。
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# COLMAP 相机模型 -> 参数个数
_CAMERA_MODEL_PARAMS = {
    0: 3,   # SIMPLE_PINHOLE: f, cx, cy
    1: 4,   # PINHOLE: fx, fy, cx, cy
    2: 4,   # SIMPLE_RADIAL: f, cx, cy, k
    3: 5,   # RADIAL
    4: 8,   # OPENCV
}


def _read(f, n: int, fmt: str):
    return struct.unpack("<" + fmt, f.read(n))


@dataclass
class CameraView:
    K: np.ndarray       # (3,3) 内参（已按 factor 缩放）
    w2c: np.ndarray     # (4,4) 世界->相机
    image_path: Path
    width: int
    height: int


def _qvec_to_rotmat(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ])


def _read_cameras(path: Path) -> dict[int, dict]:
    cams: dict[int, dict] = {}
    with open(path, "rb") as f:
        (num,) = _read(f, 8, "Q")
        for _ in range(num):
            cam_id, model_id, width, height = _read(f, 24, "iiQQ")
            n_params = _CAMERA_MODEL_PARAMS.get(model_id, 4)
            params = _read(f, 8 * n_params, "d" * n_params)
            cams[cam_id] = {"model": model_id, "w": width, "h": height, "params": params}
    return cams


def _read_images(path: Path) -> list[dict]:
    images: list[dict] = []
    with open(path, "rb") as f:
        (num,) = _read(f, 8, "Q")
        for _ in range(num):
            data = _read(f, 64, "idddddddi")
            qvec = np.array(data[1:5])
            tvec = np.array(data[5:8])
            cam_id = data[8]
            # 读图像名（以 \x00 结尾）
            name = b""
            while True:
                c = f.read(1)
                if c == b"\x00":
                    break
                name += c
            (num_pts,) = _read(f, 8, "Q")
            f.read(24 * num_pts)  # 跳过 2D 点
            images.append({
                "qvec": qvec, "tvec": tvec, "cam_id": cam_id,
                "name": name.decode("utf-8", errors="replace"),
            })
    return images


def _read_points3d(path: Path) -> tuple[np.ndarray, np.ndarray]:
    xyz_list, rgb_list = [], []
    with open(path, "rb") as f:
        (num,) = _read(f, 8, "Q")
        for _ in range(num):
            blob = _read(f, 43, "QdddBBBd")
            xyz_list.append(blob[1:4])
            rgb_list.append(blob[4:7])
            (track_len,) = _read(f, 8, "Q")
            f.read(8 * track_len)  # 跳过 track
    xyz = np.array(xyz_list, dtype=np.float32) if xyz_list else np.zeros((0, 3), np.float32)
    rgb = np.array(rgb_list, dtype=np.uint8) if rgb_list else np.zeros((0, 3), np.uint8)
    return xyz, rgb


def parse_colmap(
    sparse_dir: Path, images_dir: Path, factor: int = 1
) -> tuple[list[CameraView], np.ndarray, np.ndarray]:
    """解析 COLMAP 稀疏模型。

    Returns:
        (views, points_xyz[N,3], points_rgb[N,3])
    """
    cams = _read_cameras(sparse_dir / "cameras.bin")
    imgs = _read_images(sparse_dir / "images.bin")
    xyz, rgb = _read_points3d(sparse_dir / "points3D.bin")

    views: list[CameraView] = []
    for im in imgs:
        cam = cams[im["cam_id"]]
        p = cam["params"]
        if cam["model"] in (0, 2):  # SIMPLE_PINHOLE / SIMPLE_RADIAL
            fx = fy = p[0]; cx, cy = p[1], p[2]
        else:                        # PINHOLE / 其他
            fx, fy, cx, cy = p[0], p[1], p[2], p[3]
        K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float32)
        K[:2] /= factor
        R = _qvec_to_rotmat(im["qvec"])
        w2c = np.eye(4, dtype=np.float32)
        w2c[:3, :3] = R
        w2c[:3, 3] = im["tvec"]
        views.append(CameraView(
            K=K, w2c=w2c,
            image_path=images_dir / im["name"],
            width=cam["w"] // factor, height=cam["h"] // factor,
        ))
    return views, xyz, rgb


__all__ = ["parse_colmap", "CameraView"]
