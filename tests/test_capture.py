import pytest

torch = pytest.importorskip("torch")

pytestmark = pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")


@pytest.mark.xfail(strict=False, reason="TODO(veer)")
def test_capture_diamond_replays(tmp_path):
    from cgviz import capture, demo

    workload, inputs = demo.diamond()
    graph = capture.capture(workload, inputs)
    assert capture.check_replay(graph, workload, inputs)
    assert capture.dump_dot(graph, tmp_path / "g.dot").is_file()
