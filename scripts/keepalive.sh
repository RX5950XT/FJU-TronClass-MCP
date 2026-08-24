#!/usr/bin/env bash
# 滑動延長 TronClass 24h session。成功安靜、失敗非零結束。
set -euo pipefail
exec fjumcp keepalive
