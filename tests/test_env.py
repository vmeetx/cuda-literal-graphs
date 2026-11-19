from cgviz import env

KEYS = [
    "python",
    "torch",
    "torch CUDA",
    "driver",
    "cuda-bindings",
    "networkx",
    "matplotlib",
    "img2unicode",
    "n2",
    "GPU",
]


def test_collect_keys():
    info = env.collect()
    assert list(info) == KEYS
    assert all(isinstance(v, str) and v for v in info.values())


def test_missing_dist():
    assert env._dist_version("definitely-not-a-real-dist-xyz") == env.NOT_INSTALLED


def test_no_nvidia_smi(monkeypatch):
    monkeypatch.setattr(env.shutil, "which", lambda _: None)
    assert env._nvidia_smi("name") == "nvidia-smi not found"


def test_format_aligned():
    lines = env.format_info({"a": "1", "long key": "2"}).splitlines()
    assert lines == ["a         1", "long key  2"]
