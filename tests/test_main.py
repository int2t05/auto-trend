"""main.py pipeline 重试行为测试。

回归 2026-09-19/20 CI 连续崩溃：run_pipeline 抛运行时异常时，
main() 的重试循环没有捕获，导致进程直接崩溃退出，
而非捕获异常并重试。
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


def test_main_catches_pipeline_exception_and_retries(mocker):
    """run_pipeline 持续抛异常时，main() 应捕获并重试到最大次数后退出。"""
    from scripts.main import main, MAX_PIPELINE_ATTEMPTS

    call_count = 0

    async def crash_pipeline(report_date):
        nonlocal call_count
        call_count += 1
        raise AttributeError("'list' object has no attribute 'replace'")

    verify_mock = mocker.Mock(return_value=[])
    mocker.patch("scripts.main.run_pipeline", crash_pipeline)
    mocker.patch("scripts.main.verify_report", verify_mock)
    mocker.patch("scripts.main.git_commit_and_push")
    mocker.patch("scripts.main.PIPELINE_RETRY_BACKOFF", 0)
    mocker.patch("sys.argv", ["main.py"])
    mocker.patch.dict(os.environ, {"CI": ""})

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert call_count == MAX_PIPELINE_ATTEMPTS
    # pipeline 崩溃时 verify_report 不应被调用
    assert not verify_mock.called


def test_main_retries_after_crash_then_succeeds(mocker):
    """第一次 run_pipeline 崩溃，第二次成功，main() 应重试后正常退出。"""
    from scripts.main import main

    call_count = 0

    async def flaky_pipeline(report_date):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise AttributeError("first attempt crash")

    mocker.patch("scripts.main.run_pipeline", flaky_pipeline)
    mocker.patch("scripts.main.verify_report", return_value=[])
    mocker.patch("scripts.main.git_commit_and_push")
    mocker.patch("scripts.main.PIPELINE_RETRY_BACKOFF", 0)
    mocker.patch("sys.argv", ["main.py"])
    mocker.patch.dict(os.environ, {"CI": ""})

    main()  # 不应抛异常

    assert call_count == 2


def test_main_backs_off_between_pipeline_retries(mocker):
    """回归 2026-10-09 CI 504 连败：pipeline 重试之间必须指数退避，
    等待上游瞬断恢复，而非在 1 秒内 3 连败直接退出。"""
    from scripts.main import main, MAX_PIPELINE_ATTEMPTS, PIPELINE_RETRY_BACKOFF

    call_count = 0

    async def crash_pipeline(report_date):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("Server error '504 Gateway Time-out'")

    sleep_mock = mocker.patch("scripts.main.time.sleep")
    mocker.patch("scripts.main.run_pipeline", crash_pipeline)
    mocker.patch("scripts.main.verify_report", return_value=[])
    mocker.patch("scripts.main.git_commit_and_push")
    mocker.patch("sys.argv", ["main.py"])
    mocker.patch.dict(os.environ, {"CI": ""})

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert call_count == MAX_PIPELINE_ATTEMPTS
    # 两次重试前分别等待 30s、60s（指数退避）
    assert sleep_mock.call_args_list == [
        mocker.call(PIPELINE_RETRY_BACKOFF),
        mocker.call(PIPELINE_RETRY_BACKOFF * 2),
    ]
